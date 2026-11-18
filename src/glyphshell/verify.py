"""できたピースが要件を満たすかを、立体の演算で確かめる（TESTLIST.md の 2・4・5・6 番）。"""

from dataclasses import dataclass
from itertools import combinations, permutations

import manifold3d
import numpy as np
import trimesh
from scipy.optimize import nnls
from scipy.spatial import cKDTree


@dataclass(frozen=True)
class ContactFrame:
    """ピースから見た1つの接触。"""

    point: np.ndarray  # 接触面の中心
    outward: np.ndarray  # 接触面の法線（ピースの外を向く）
    up: np.ndarray  # その点での曲面の外向きの法線（ピースの表の向き）
    contact: int = -1  # 接触の番号
    first: bool = True  # このピースが、接触の2つのピースのうち番号の小さいほうか


def overlap_volume(a: manifold3d.Manifold, b: manifold3d.Manifold) -> float:
    """2つの立体が重なっている部分の体積。"""
    return float((a ^ b).volume())


def removal_direction(outward: np.ndarray, contact_outwards: list[np.ndarray]) -> np.ndarray:
    """ピースを抜く向きを返す。どの接触面にも食い込まない向きのうち、outward にいちばん近い向き。

    接触面の法線（ピースの外向き）n のどれについても、向き d は d·n <= 0 を満たす。
    満たす向きが無ければ ValueError。
    """
    direction = outward / np.linalg.norm(outward)
    if contact_outwards:
        normals = np.array([n / np.linalg.norm(n) for n in contact_outwards])
        # 条件を満たす向きの集まり（錐）への射影。outward から、法線の非負の重みつきの和で表せる
        # 成分のうち outward にいちばん近いものを引くと、錐の中で outward にいちばん近い向きになる
        weights, _ = nnls(normals.T, direction)
        direction = direction - normals.T @ weights
    length = np.linalg.norm(direction)
    if length < 1e-6 or any(direction @ n > 1e-6 * np.linalg.norm(n) for n in contact_outwards):
        raise ValueError("どの接触面にも食い込まずに抜ける向きがない")
    return direction / length


def removal_blocked_by(
    piece: manifold3d.Manifold,
    others: list[manifold3d.Manifold],
    direction: np.ndarray,
    travel: float,
    step: float,
    tolerance: float = 0.0,
) -> list[int]:
    """piece を direction へ travel だけ動かす途中で、ぶつかる立体の番号を返す。"""
    blocked = set()
    for distance in np.arange(step, travel + step / 2, step):
        moved = piece.translate(list(direction * distance))
        for k, other in enumerate(others):
            if k not in blocked and overlap_volume(moved, other) > tolerance:
                blocked.add(k)
    return sorted(blocked)


def wall_shortfall(
    solid: manifold3d.Manifold,
    start: np.ndarray,
    into: np.ndarray,
    hole_diameter: float,
    hole_depth: float,
    wall: float,
) -> float:
    """穴のまわりに厚さ wall の肉を取ったとき、立体からはみ出す体積を返す。0 なら肉厚は足りている。

    solid は穴を開ける前の立体。start は穴の口の中心、into は掘る向き。
    穴の口の面は開いているので、口の側の肉は確かめない。
    """
    axis = into / np.linalg.norm(into)
    helper = np.array([1.0, 0.0, 0.0]) if abs(axis[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    side = np.cross(helper, axis)
    side /= np.linalg.norm(side)
    up = np.cross(axis, side)
    transform = np.column_stack([side, up, axis, start])
    needed = manifold3d.Manifold.cylinder(
        hole_depth + wall, hole_diameter / 2 + wall, circular_segments=48
    ).transform(transform)
    return float((needed - solid).volume())


def _aligned(source: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """source の点を target の点に重ねる回転と平行移動（鏡写しを含まない）を返す。"""
    cs, ct = source.mean(axis=0), target.mean(axis=0)
    u, _, vt = np.linalg.svd((source - cs).T @ (target - ct))
    sign = np.sign(np.linalg.det(vt.T @ u.T))
    rotation = vt.T @ np.diag([1.0, 1.0, sign]) @ u.T
    return rotation, ct - rotation @ cs


def false_fits(
    pieces: list[list[ContactFrame]], position_tolerance: float, angle_tolerance: float
) -> list[tuple[int, int]]:
    """ピース i が、ピース j の場所に（正しくない形で）はまる組 (i, j) を返す。

    「はまる」は、i の接触のうち3つを、回転と平行移動だけで j の接触3つに重ねられること。
    位置のずれが position_tolerance 以下、面の向きと表の向きのずれが angle_tolerance 以下なら
    重なるとする。表の向きも比べるので、裏返しにしてはまる場合は数えない。
    i == j のときは、接触を元と違う相手に重ねられる場合（向きを変えてもはまる場合）を数える。

    接触の位置だけで判定するので、ピースの形がぶつかって実際には入らない組も含む。
    """
    return [
        (i, j)
        for i, source in enumerate(pieces)
        for j, target in enumerate(pieces)
        if fit_transforms(source, target, i == j, position_tolerance, angle_tolerance)
    ]


def fit_transforms(
    source: list[ContactFrame],
    target: list[ContactFrame],
    same_piece: bool,
    position_tolerance: float,
    angle_tolerance: float,
) -> list[np.ndarray]:
    """source のピースを target の場所へ運ぶ動き（3×4 の行列）のうち、接触3つが重なるものを返す。

    ほぼ同じ動き（平行移動が position_tolerance 未満、回転が angle_tolerance 未満の差）は1つにまとめる。
    """
    if len(source) < 3 or len(target) < 3:
        return []
    target_points = np.array([frame.point for frame in target])
    target_dirs = np.array([frame.outward for frame in target])
    target_ups = np.array([frame.up for frame in target])
    matches = np.array(list(permutations(range(len(target)), 3)))
    matched_points = target_points[matches]  # [並べ方, 3, 3]
    matched_sides = np.linalg.norm(matched_points - np.roll(matched_points, 1, axis=1), axis=2)
    centre = np.mean([frame.point for frame in source], axis=0)
    found: list[np.ndarray] = []
    for triple in combinations(range(len(source)), 3):
        points = np.array([source[k].point for k in triple])
        dirs = np.array([source[k].outward for k in triple])
        ups = np.array([source[k].up for k in triple])
        sides = np.linalg.norm(points - np.roll(points, 1, axis=0), axis=1)
        # 辺の長さが合わない並べ方は、重ねる計算をせずに飛ばす
        close = np.abs(matched_sides - sides).max(axis=1) <= 2 * position_tolerance
        if same_piece:
            close &= (matches != np.array(triple)).any(axis=1)
        for match in matches[close]:
            matched = target_points[match]
            rotation, shift = _aligned(points, matched)
            if np.linalg.norm(points @ rotation.T + shift - matched, axis=1).max() > position_tolerance:
                continue
            faces = np.einsum("kd,kd->k", dirs @ rotation.T, target_dirs[match])
            tops = np.einsum("kd,kd->k", ups @ rotation.T, target_ups[match])
            if min(faces.min(), tops.min()) < np.cos(angle_tolerance):
                continue
            if same_piece:
                # 元の場所に元の向きで置くのとほぼ同じ動きは、正しい置き方なので数えない
                turned = np.arccos(np.clip((np.trace(rotation) - 1) / 2, -1, 1))
                moved = np.linalg.norm(rotation @ centre + shift - centre)
                if turned < angle_tolerance and moved < position_tolerance:
                    continue
            duplicate = any(
                np.linalg.norm((other[:, :3] - rotation) @ np.ones(3)) < angle_tolerance
                and np.linalg.norm(other[:, :3] @ centre + other[:, 3] - rotation @ centre - shift)
                < position_tolerance
                for other in found
            )
            if not duplicate:
                found.append(np.column_stack([rotation, shift]))
    return found


def overlapping_contacts(
    source: list[ContactFrame],
    target: list[ContactFrame],
    transform: np.ndarray,
    position_tolerance: float,
    angle_tolerance: float,
) -> list[tuple[int, int]]:
    """source を transform で動かしたとき、target の接触と重なる接触の組 (source の番号, target の番号)。"""
    rotation, shift = transform[:, :3], transform[:, 3]
    pairs = []
    for k, frame in enumerate(source):
        point = rotation @ frame.point + shift
        for m, other in enumerate(target):
            if (
                np.linalg.norm(point - other.point) <= position_tolerance
                and (rotation @ frame.outward) @ other.outward >= np.cos(angle_tolerance)
                and (rotation @ frame.up) @ other.up >= np.cos(angle_tolerance)
            ):
                pairs.append((k, m))
    return pairs


def _north_out(frame: ContactFrame, polarity: np.ndarray) -> bool:
    """このピースの側の磁石が、N 極を接触面の外へ向けているか。"""
    return bool(polarity[frame.contact]) == frame.first


def attracts(pairs: list[tuple[ContactFrame, ContactFrame]], polarity: np.ndarray) -> bool:
    """間違った置き方で重なる接触の組が、すべて引き合うか。

    組は (置いたピースの接触, その場所の本来のピースの接触)。相手側の磁石は本来のピースと
    逆の極を向けているので、置いたピースが本来のピースと同じ極を向けていれば引き合う。
    """
    return all(_north_out(a, polarity) == _north_out(b, polarity) for a, b in pairs)


def assign_polarity(
    contact_count: int, wrong_fits: list[list[tuple[ContactFrame, ContactFrame]]], seed: int
) -> np.ndarray:
    """接触ごとの磁石の向きを決める。真なら、番号の小さいほうのピースが N 極を外へ向ける。

    間違った置き方のどれについても、重なる接触のうち少なくとも1つが反発するようにする。
    正しい相手とは、どの向きの決め方でも必ず引き合う。決められなければ ValueError。
    """
    rng = np.random.default_rng(seed)
    polarity = rng.integers(0, 2, contact_count).astype(bool)
    # 反発させようのない置き方（重なる接触が1つもない）は対象にしない
    wrong_fits = [pairs for pairs in wrong_fits if pairs]
    for _ in range(200 * max(len(wrong_fits), 1)):
        bad = [pairs for pairs in wrong_fits if attracts(pairs, polarity)]
        if not bad:
            return polarity
        # まだ引き合う置き方を1つ選び、それに関わる接触の向きを1つ反転する
        pairs = bad[rng.integers(len(bad))]
        a, b = pairs[rng.integers(len(pairs))]
        chosen = a if rng.integers(2) else b
        polarity[chosen.contact] = ~polarity[chosen.contact]
    raise ValueError("間違った置き方をすべて反発させる磁石の向きが見つからない")


def _surface_samples(solid: manifold3d.Manifold, spacing: float) -> tuple[np.ndarray, np.ndarray]:
    """立体の表面に spacing 以下の間隔で取った点と、その点での外向きの法線。"""
    mesh = solid.to_mesh()
    vertices, faces = trimesh.remesh.subdivide_to_size(
        np.asarray(mesh.vert_properties[:, :3], dtype=float), np.asarray(mesh.tri_verts, dtype=np.int64), spacing
    )
    tri = vertices[faces]
    normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    length = np.linalg.norm(normals, axis=1)
    return tri.mean(axis=1)[length > 0], normals[length > 0] / length[length > 0, None]


def _facing(samples_a, samples_b, spacing: float) -> np.ndarray:
    (points_a, normals_a), (points_b, normals_b) = samples_a, samples_b
    if (points_a.min(axis=0) > points_b.max(axis=0) + spacing).any() or (
        points_b.min(axis=0) > points_a.max(axis=0) + spacing
    ).any():
        return np.zeros((0, 3))
    distance, nearest = cKDTree(points_b).query(points_a, distance_upper_bound=spacing)
    close = np.isfinite(distance)
    # 逆向きとみなす角度は 30 度まで（cos 150° = −0.87）。接している壁どうしは、点の位置がずれても
    # 法線の向きはほぼ正反対になる
    facing = np.zeros(len(points_a), dtype=bool)
    facing[close] = (normals_a[close] * normals_b[nearest[close]]).sum(axis=1) < -np.cos(np.radians(30.0))
    found = normals_a[facing]
    # 成分を 0.01 刻み（約 0.6 度）に丸めて同じになる法線は、最初の1つだけ残す
    _, first = np.unique(np.round(found, 2), axis=0, return_index=True)
    return found[np.sort(first)]


def facing_normals(a: manifold3d.Manifold, b: manifold3d.Manifold, spacing: float) -> np.ndarray:
    """a の表面のうち、b の表面と向かい合って接している所の法線（a の外向き）を返す。[k, 3]

    両方の表面に spacing 以下の間隔で点を取り、spacing より近くに、ほぼ逆向きの法線を持つ b の点が
    ある a の点を「接している」とみなす。ほぼ同じ向きの法線は1つにまとめる。
    """
    return _facing(_surface_samples(a, spacing), _surface_samples(b, spacing), spacing)


def wall_normals(solids: list[manifold3d.Manifold], spacing: float) -> list[list[tuple[int, np.ndarray]]]:
    """立体ごとに、ほかの立体と接している壁の (相手の番号, 法線（自分の外向き）) を返す。"""
    samples = [_surface_samples(solid, spacing) for solid in solids]
    return [
        [(j, normal) for j in range(len(solids)) if j != i for normal in _facing(samples[i], samples[j], spacing)]
        for i in range(len(solids))
    ]


def removal_plan(
    solids: list[manifold3d.Manifold],
    outwards: list[np.ndarray],
    contact_normals: list[list[tuple[int, np.ndarray]]],
    travel: float,
    step: float,
    tolerance: float,
) -> tuple[list[int], list[np.ndarray | None], list[int]]:
    """全ピースを1つずつ外へ抜いていく順と向きを求める。組み立ては、この逆の順に入れる。

    contact_normals[i] は、ピース i の接触ごとの (相手の番号, 接触面の法線（i の外向き）)。
    抜く向きは、その時点で残っている相手の接触面にだけ食い込まない向きにする。くぼんだ所の
    ピースは、まわりが全部あると抜ける向きがないが、隣が抜けた後なら斜めに抜ける。
    戻り値は (抜く順, ピースごとの抜く向き, 抜けずに残ったピース)。残ったピースの向きは None。
    """
    remaining = set(range(len(solids)))
    order: list[int] = []
    directions: list[np.ndarray | None] = [None] * len(solids)
    # 前に試して抜けなかったピースは、そのとき邪魔だった相手のどれかが抜けるまで試し直さない
    waiting: dict[int, set[int]] = {}
    progress = True
    while remaining and progress:
        progress = False
        for i in sorted(remaining):
            if i in waiting and waiting[i] <= remaining:
                continue
            neighbours = {j for j, _ in contact_normals[i] if j in remaining}
            try:
                direction = removal_direction(outwards[i], [n for j, n in contact_normals[i] if j in remaining])
            except ValueError:
                waiting[i] = neighbours
                continue
            others = sorted(remaining - {i})
            blocked = removal_blocked_by(solids[i], [solids[j] for j in others], direction, travel, step, tolerance)
            if blocked:
                waiting[i] = neighbours | {others[k] for k in blocked}
                continue
            remaining.remove(i)
            order.append(i)
            directions[i] = direction
            progress = True
    return order, directions, sorted(remaining)
