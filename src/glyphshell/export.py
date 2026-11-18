"""保存した配置からピースの立体を作り、検証して、STL とビューワー用のデータに書き出す。

    uv run python -m glyphshell.export                          # out/layout.npz を使う
    uv run python -m glyphshell.export --layout out/layout_39.npz
    uv run python -m glyphshell.export --mesh bunny.off --height 300 --out out_bunny

書き出すもの（出力先のフォルダの下）:
    stl/piece_番号_字.stl   印刷用。外側の面を上に向け、底を z=0 に置いた向き
    stl/extra_番号.stl      メッシュを渡したときの追加のパーツ（耳など、字のピースにならない部分）
    assembled.stl           組み上がった位置のままの全ピース
    verify_report.json      検証の結果（TESTLIST.md の 2〜6・9 番）
    viewer_data.json        ビューワー用の形と接触の情報
    pieces_preview.png      ピースの立体を 6 方向から見た図
"""

import base64
import json
import time

import numpy as np
import trimesh

from glyphshell.build import (
    HOLE_MARGIN,
    MAGNET_DIAMETER,
    MAGNET_THICKNESS,
    MIN_CONTACT,
    MIN_CONTACTS_PER_PIECE,
    MIN_WALL,
    PAD,
    THICKNESS,
    parse_job,
)
from glyphshell.contacts import find_contacts, piece_fields, stable_pieces
from glyphshell.layout import load_layout
from glyphshell.preview import render_solids, write_png
from glyphshell.skin import extra_parts
from glyphshell.solids import Pocket, clip_region, piece_solid, thicken
from glyphshell.verify import (
    ContactFrame,
    assign_polarity,
    attracts,
    fit_transforms,
    overlap_volume,
    overlapping_contacts,
    removal_plan,
    wall_normals,
    wall_shortfall,
)

HOLE_DIAMETER = MAGNET_DIAMETER + HOLE_MARGIN
# 立体の重なりとみなす体積の下限。一辺 0.4 mm（ノズル径）の立方体より小さい重なりは、
# 計算の丸めと区別できないので数えない
VOLUME_TOLERANCE = 0.4**3
# 穴のまわりの肉の不足とみなす体積の下限。穴の口の面積（肉を含む）× 0.1 mm。
# 0.1 mm は磁石の寸法公差と同じ程度で、これより薄い不足は印刷の誤差に埋もれる
WALL_TOLERANCE = np.pi * (HOLE_DIAMETER / 2 + MIN_WALL) ** 2 * 0.1
# ピースを抜く動きを確かめる距離（ピースの厚さに対する倍率）と刻み。厚さの 1.5 倍動かせば、
# 隣の壁から完全に離れる
REMOVAL_TRAVEL_RATIO = 1.5
REMOVAL_STEP = 1.0
# 隣のピースと接している壁を探すときの、表面に取る点の間隔。メッシュの辺の長さ（1.4 mm）より細かくする
WALL_SPACING = 1.0
# 追加のパーツとして残す体積の下限。磁石の穴とまわりの壁が入る円柱の体積。
# これより小さいかけらは、磁石を埋められないので付けようがない
EXTRA_MIN_VOLUME = np.pi * (HOLE_DIAMETER / 2 + MIN_WALL) ** 2 * (MAGNET_THICKNESS + MIN_WALL)
# 別の場所にはまるかを調べるときの許容差。磁石どうしが半径（3 mm）より大きくずれると、
# 面どうしが重ならず吸着しない。向きは 20 度より大きくずれると、台の端で 2.7 mm の隙間になる
FIT_POSITION_TOLERANCE = MAGNET_DIAMETER / 2
FIT_ANGLE_TOLERANCE = np.radians(20.0)
# ビューワー用の形を粗くするときの許容差。印刷用の STL は粗くしない
VIEWER_TOLERANCE = 0.05


def _mesh(solid) -> trimesh.Trimesh:
    data = solid.to_mesh()
    return trimesh.Trimesh(
        vertices=np.asarray(data.vert_properties)[:, :3], faces=np.asarray(data.tri_verts), process=False
    )


def _print_pose(mesh: trimesh.Trimesh, outward: np.ndarray) -> trimesh.Trimesh:
    """外側の面が上（+z）を向き、底が z=0 に来るように回した形を返す。"""
    posed = mesh.copy()
    posed.apply_transform(trimesh.geometry.align_vectors(outward / np.linalg.norm(outward), [0, 0, 1]))
    posed.apply_translation([0, 0, -posed.bounds[0, 2]])
    return posed


def _packed(array: np.ndarray, dtype) -> str:
    return base64.b64encode(np.ascontiguousarray(array, dtype=dtype).tobytes()).decode("ascii")


def main() -> None:
    job = parse_job("配置からピースの立体を作り、検証して書き出す")
    started = time.time()
    surface, skin = job.surface, job.skin
    placements = load_layout(job.layout)
    contacts = find_contacts(surface, placements, MIN_CONTACT, PAD)
    kept = stable_pieces(len(placements), contacts, MIN_CONTACTS_PER_PIECE)
    dropped = [p.char for i, p in enumerate(placements) if i not in kept]
    if dropped:
        placements = [placements[i] for i in kept]
        contacts = find_contacts(surface, placements, MIN_CONTACT, PAD)
    if not placements:
        raise SystemExit(f"接触が {MIN_CONTACTS_PER_PIECE} か所に届く字が1つも残らなかった（{job.layout}）")
    fields = piece_fields(surface, placements, contacts, PAD)
    count = len(placements)
    chars = [p.char for p in placements]

    # 磁石の穴の深さの基準にする点。殻の内側の面から、法線に沿って殻の厚さだけ外の所。
    # 球では字を敷き詰めた面（外側の面）の上、メッシュでは内側の面から殻の厚さだけ上になる
    lift = THICKNESS if skin else 0.0
    datums = [contact.point + lift * contact.normal for contact in contacts]
    frames: list[list[ContactFrame]] = [[] for _ in range(count)]
    for c, contact in enumerate(contacts):
        middle = datums[c] - contact.normal * THICKNESS / 2
        frames[contact.a].append(ContactFrame(middle, contact.direction, contact.normal, c, True))
        frames[contact.b].append(ContactFrame(middle, -contact.direction, contact.normal, c, False))

    # 5番: 置き場所が1つに決まる。別の場所に接触3つが重なる置き方を全部挙げ、
    # そのどれもが、重なる接触の少なくとも1つで反発するように磁石の向きを決める
    wrong_fits = []
    for i in range(count):
        for j in range(count):
            for transform in fit_transforms(
                frames[i], frames[j], i == j, FIT_POSITION_TOLERANCE, FIT_ANGLE_TOLERANCE
            ):
                pairs = overlapping_contacts(
                    frames[i], frames[j], transform, FIT_POSITION_TOLERANCE, FIT_ANGLE_TOLERANCE
                )
                wrong_fits.append([(frames[i][k], frames[j][m]) for k, m in pairs])
    polarity = assign_polarity(len(contacts), wrong_fits, seed=0)
    print(f"間違った置き方 {len(wrong_fits)} 通りを調べ、磁石の向きを決めた（{time.time() - started:.0f} 秒）")

    pockets: list[list[Pocket]] = [[] for _ in range(count)]
    for c, contact in enumerate(contacts):
        north_on_a = bool(polarity[c])
        pockets[contact.a].append(Pocket(datums[c], contact.normal, -contact.direction, north_on_a))
        pockets[contact.b].append(Pocket(datums[c], contact.normal, contact.direction, not north_on_a))

    dropped_volume = {}
    if skin is None:
        regions = [clip_region(surface, fields[i]) for i in range(count)]
        plain = [thicken(region, THICKNESS) for region in regions]
        extras, lost_volume = [], 0.0
    else:
        # 内側の面から外へ押し出した柱を、元の形で切り取る。離れたかけらができたら、
        # 体積がいちばん大きい塊だけを残す
        regions = [clip_region(surface, fields[i], skin.reach) for i in range(count)]
        plain = []
        for i, region in enumerate(regions):
            parts = sorted((thicken(region, 0.0) ^ skin.outer).decompose(), key=lambda part: -part.volume())
            plain.append(parts[0])
            if len(parts) > 1:
                dropped_volume[chars[i]] = round(sum(part.volume() for part in parts[1:]), 1)
        extras, lost_volume = extra_parts(skin, EXTRA_MIN_VOLUME)
    solids = [piece_solid(plain[i], THICKNESS, pockets[i], HOLE_DIAMETER, MAGNET_THICKNESS) for i in range(count)]
    print(f"{count} ピースの立体を作った（{time.time() - started:.0f} 秒）")

    report: dict = {
        "pieces": count,
        "contacts": len(contacts),
        "magnets": 2 * len(contacts),
        "dropped_for_contacts": dropped,
        "dropped_islands": {
            chars[i]: round(regions[i].dropped_area, 1) for i in range(count) if regions[i].dropped_area > 0
        },
        "dropped_fragments_volume": dropped_volume,
        "extra_parts_volume": [round(extra.volume()) for extra in extras],
        "discarded_crumbs_volume": round(lost_volume, 1),
    }

    # 2番: ピースどうしが重ならない
    report["test2_overlaps"] = [
        (chars[a], chars[b], round(volume, 2))
        for a in range(count)
        for b in range(a + 1, count)
        if (volume := overlap_volume(solids[a], solids[b])) > VOLUME_TOLERANCE
    ]

    # 3番: どのピースも3か所以上で隣とつながる
    report["test3_short_of_contacts"] = [
        chars[i] for i in range(count) if len(pockets[i]) < MIN_CONTACTS_PER_PIECE
    ]

    # 6番: 磁石の穴の周りに肉厚がある
    thin = []
    for i in range(count):
        for k, pocket in enumerate(pockets[i]):
            start = pocket.point - pocket.normal * THICKNESS / 2
            shortfall = wall_shortfall(plain[i], start, pocket.into, HOLE_DIAMETER, MAGNET_THICKNESS, MIN_WALL)
            if shortfall > WALL_TOLERANCE:
                thin.append((chars[i], k, round(shortfall, 2)))
    report["test6_thin_walls"] = thin

    # 9番: 接触の両側で磁石の極が逆を向く
    report["test9_same_poles"] = [
        (chars[contact.a], chars[contact.b])
        for c, contact in enumerate(contacts)
        if sum(p.north_out for i in (contact.a, contact.b) for p in pockets[i] if p.point is datums[c]) != 1
    ]
    report["test5_wrong_fits_checked"] = len(wrong_fits)
    report["test5_wrong_fits_attracting"] = sum(attracts(pairs, polarity) for pairs in wrong_fits)
    print(f"2・3・5・6・9番を確かめた（{time.time() - started:.0f} 秒）")

    # 4番: 決まった順に入れれば、どのピースも外から入れられる
    travel = REMOVAL_TRAVEL_RATIO * (THICKNESS if skin is None else float(skin.reach.max()))
    outwards = [region.normals.mean(axis=0) for region in regions]
    # 抜く向きを縛る面: 磁石の接触面と、隣のピースと接している壁（字の重なりを切り分けた面）
    contact_normals: list[list[tuple[int, np.ndarray]]] = [[] for _ in range(count)]
    for contact in contacts:
        contact_normals[contact.a].append((contact.b, contact.direction))
        contact_normals[contact.b].append((contact.a, -contact.direction))
    for i, walls in enumerate(wall_normals(solids, WALL_SPACING)):
        contact_normals[i].extend(walls)
    removed, directions, stuck = removal_plan(solids, outwards, contact_normals, travel, REMOVAL_STEP, VOLUME_TOLERANCE)
    # 抜けなかったピースは、ビューワーでは外向きに動かし、順は最後に置く
    directions = [outwards[i] / np.linalg.norm(outwards[i]) if d is None else d for i, d in enumerate(directions)]
    order = stuck + removed[::-1]
    report["test4_stuck"] = [chars[i] for i in stuck]
    report["assembly_order"] = "".join(chars[i] for i in removed[::-1])
    print(f"4番を確かめた（{time.time() - started:.0f} 秒）")

    stl = job.out / "stl"
    stl.mkdir(parents=True, exist_ok=True)
    for old in stl.glob("*.stl"):
        old.unlink()
    meshes = [_mesh(solid) for solid in solids]
    for i, mesh in enumerate(meshes):
        outward = regions[i].normals.mean(axis=0)
        _print_pose(mesh, outward).export(stl / f"piece_{i:02d}_U+{ord(chars[i]):04X}.stl")
    extra_meshes = [_mesh(extra) for extra in extras]
    for k, mesh in enumerate(extra_meshes):
        mesh.export(stl / f"extra_{k:02d}.stl")
    trimesh.util.concatenate(meshes + extra_meshes).export(job.out / "assembled.stl")
    # 1 mm あたり 2 画素。高さ 300 mm の形で、1方向が約 630 画素になる
    write_png(job.out / "pieces_preview.png", render_solids(meshes, extra_meshes, pixels_per_unit=2.0))
    (job.out / "verify_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    viewer = {
        "shape": job.shape,
        "extent": round(float((surface.vertices.max(axis=0) - surface.vertices.min(axis=0)).max()), 1),
        "thickness": THICKNESS,
        "magnet": {"diameter": MAGNET_DIAMETER, "thickness": MAGNET_THICKNESS},
        "report": report,
        "pieces": [],
        "extras": [
            {
                "positions": _packed(np.asarray(light.vert_properties)[:, :3], np.float32),
                "indices": _packed(np.asarray(light.tri_verts), np.uint32),
            }
            for light in (extra.simplify(VIEWER_TOLERANCE).to_mesh() for extra in extras)
        ],
        "contacts": [
            {
                "a": contact.a,
                "b": contact.b,
                "point": np.round(datums[c] - contact.normal * THICKNESS / 2, 2).tolist(),
                "direction": np.round(contact.direction, 4).tolist(),
                "northOnA": bool(polarity[c]),
            }
            for c, contact in enumerate(contacts)
        ],
    }
    for i, solid in enumerate(solids):
        light = solid.simplify(VIEWER_TOLERANCE).to_mesh()
        viewer["pieces"].append(
            {
                "char": chars[i],
                "file": f"piece_{i:02d}_U+{ord(chars[i]):04X}.stl",
                "positions": _packed(np.asarray(light.vert_properties)[:, :3], np.float32),
                "indices": _packed(np.asarray(light.tri_verts), np.uint32),
                "direction": np.round(directions[i], 4).tolist(),
                "step": order.index(i) + 1,
                "magnets": len(pockets[i]),
                "northOut": sum(pocket.north_out for pocket in pockets[i]),
                "size": placements[i].size,
            }
        )
    (job.out / "viewer_data.json").write_text(json.dumps(viewer, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    print(f"書き出した（{time.time() - started:.0f} 秒）")


if __name__ == "__main__":
    main()
