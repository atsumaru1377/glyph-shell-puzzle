"""保存した配置からピースの立体を作り、検証して、STL とビューワー用のデータに書き出す。

    uv run python -m glyphshell.export [配置のファイル]   # 既定は out/layout.npz

書き出すもの（out/ の下）:
    stl/piece_番号_字.stl   印刷用。外側の面を上に向け、底を z=0 に置いた向き
    assembled.stl           組み上がった位置のままの全ピース
    verify_report.json      検証の結果（TESTLIST.md の 2〜6・9 番）
    viewer_data.json        ビューワー用の形と接触の情報
"""

import base64
import json
import sys
import time
from pathlib import Path

import numpy as np
import trimesh

from glyphshell.build import (
    HOLE_MARGIN,
    MAGNET_DIAMETER,
    MAGNET_THICKNESS,
    MIN_CONTACT,
    MIN_CONTACTS_PER_PIECE,
    MIN_WALL,
    OUT,
    PAD,
    RADIUS,
    SUBDIVISIONS,
)
from glyphshell.contacts import find_contacts, piece_fields, stable_pieces
from glyphshell.layout import load_layout
from glyphshell.solids import Pocket, clip_region, piece_solid, thicken
from glyphshell.surface import icosphere
from glyphshell.verify import (
    ContactFrame,
    assign_polarity,
    attracts,
    fit_transforms,
    overlap_volume,
    overlapping_contacts,
    removal_blocked_by,
    removal_direction,
    removal_order,
    wall_shortfall,
)

# 殻の厚さ。磁石の穴（直径 6.2 mm）の上下に壁 0.8 mm ずつで 7.8 mm 要る。穴はまっすぐで
# 曲面は曲がっているので、その差と面の粗さの余裕を足して 8.5 mm にする
THICKNESS = 8.5
HOLE_DIAMETER = MAGNET_DIAMETER + HOLE_MARGIN
# 立体の重なりとみなす体積の下限。一辺 0.4 mm（ノズル径）の立方体より小さい重なりは、
# 計算の丸めと区別できないので数えない
VOLUME_TOLERANCE = 0.4**3
# 穴のまわりの肉の不足とみなす体積の下限。穴の口の面積（肉を含む）× 0.1 mm。
# 0.1 mm は磁石の寸法公差と同じ程度で、これより薄い不足は印刷の誤差に埋もれる
WALL_TOLERANCE = np.pi * (HOLE_DIAMETER / 2 + MIN_WALL) ** 2 * 0.1
# ピースを抜く動きを確かめる距離と刻み。殻の厚さの 1.5 倍動かせば、隣の壁から完全に離れる
REMOVAL_TRAVEL = 1.5 * THICKNESS
REMOVAL_STEP = 1.0
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
    layout_path = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT / "layout.npz"
    started = time.time()
    surface = icosphere(RADIUS, SUBDIVISIONS)
    placements = load_layout(layout_path)
    contacts = find_contacts(surface, placements, MIN_CONTACT, PAD)
    kept = stable_pieces(len(placements), contacts, MIN_CONTACTS_PER_PIECE)
    dropped = [p.char for i, p in enumerate(placements) if i not in kept]
    if dropped:
        placements = [placements[i] for i in kept]
        contacts = find_contacts(surface, placements, MIN_CONTACT, PAD)
    fields = piece_fields(surface, placements, contacts, PAD)
    count = len(placements)
    chars = [p.char for p in placements]

    frames: list[list[ContactFrame]] = [[] for _ in range(count)]
    for c, contact in enumerate(contacts):
        middle = contact.point - contact.normal * THICKNESS / 2
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
        pockets[contact.a].append(Pocket(contact.point, contact.normal, -contact.direction, north_on_a))
        pockets[contact.b].append(Pocket(contact.point, contact.normal, contact.direction, not north_on_a))

    regions = [clip_region(surface, fields[i]) for i in range(count)]
    plain = [thicken(region, THICKNESS) for region in regions]
    solids = [
        piece_solid(regions[i], THICKNESS, pockets[i], HOLE_DIAMETER, MAGNET_THICKNESS)
        for i in range(count)
    ]
    print(f"{count} ピースの立体を作った（{time.time() - started:.0f} 秒）")

    report: dict = {
        "pieces": count,
        "contacts": len(contacts),
        "magnets": 2 * len(contacts),
        "dropped_for_contacts": dropped,
        "dropped_islands": {
            chars[i]: round(regions[i].dropped_area, 1) for i in range(count) if regions[i].dropped_area > 0
        },
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
        if sum(p.north_out for i in (contact.a, contact.b) for p in pockets[i] if p.point is contact.point) != 1
    ]
    report["test5_wrong_fits_checked"] = len(wrong_fits)
    report["test5_wrong_fits_attracting"] = sum(attracts(pairs, polarity) for pairs in wrong_fits)
    print(f"2・3・5・6・9番を確かめた（{time.time() - started:.0f} 秒）")

    # 4番: 決まった順に入れれば、どのピースも外から入れられる
    directions = []
    blocked_by: list[list[int]] = []
    for i in range(count):
        outward = regions[i].normals.mean(axis=0)
        direction = removal_direction(outward, [frame.outward for frame in frames[i]])
        others = [j for j in range(count) if j != i]
        blocked = removal_blocked_by(
            solids[i], [solids[j] for j in others], direction, REMOVAL_TRAVEL, REMOVAL_STEP, VOLUME_TOLERANCE
        )
        directions.append(direction)
        blocked_by.append([others[k] for k in blocked])
    order = removal_order(blocked_by)[::-1]
    report["test4_insert_before"] = [
        (chars[i], "".join(chars[j] for j in blocked_by[i])) for i in range(count) if blocked_by[i]
    ]
    report["assembly_order"] = "".join(chars[i] for i in order)
    print(f"4番を確かめた（{time.time() - started:.0f} 秒）")

    stl = OUT / "stl"
    stl.mkdir(parents=True, exist_ok=True)
    for old in stl.glob("*.stl"):
        old.unlink()
    meshes = [_mesh(solid) for solid in solids]
    for i, mesh in enumerate(meshes):
        outward = regions[i].normals.mean(axis=0)
        _print_pose(mesh, outward).export(stl / f"piece_{i:02d}_U+{ord(chars[i]):04X}.stl")
    trimesh.util.concatenate(meshes).export(OUT / "assembled.stl")
    (OUT / "verify_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    viewer = {
        "diameter": 2 * RADIUS,
        "thickness": THICKNESS,
        "magnet": {"diameter": MAGNET_DIAMETER, "thickness": MAGNET_THICKNESS},
        "report": report,
        "pieces": [],
        "contacts": [
            {
                "a": contact.a,
                "b": contact.b,
                "point": np.round(contact.point - contact.normal * THICKNESS / 2, 2).tolist(),
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
    (OUT / "viewer_data.json").write_text(json.dumps(viewer, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    print(f"書き出した（{time.time() - started:.0f} 秒）")


if __name__ == "__main__":
    main()
