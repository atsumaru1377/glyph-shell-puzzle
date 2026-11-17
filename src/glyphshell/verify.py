"""できたピースが要件を満たすかを、立体の演算で確かめる（TESTLIST.md の 2・4・5・6 番）。"""

from dataclasses import dataclass
from itertools import combinations, permutations

import manifold3d
import numpy as np


@dataclass(frozen=True)
class ContactFrame:
    """ピースから見た1つの接触。"""

    point: np.ndarray  # 接触面の中心
    outward: np.ndarray  # 接触面の法線（ピースの外を向く）
    up: np.ndarray  # その点での曲面の外向きの法線（ピースの表の向き）


def overlap_volume(a: manifold3d.Manifold, b: manifold3d.Manifold) -> float:
    """2つの立体が重なっている部分の体積。"""
    return float((a ^ b).volume())


def removal_direction(outward: np.ndarray, contact_outwards: list[np.ndarray]) -> np.ndarray:
    """ピースを抜く向きを返す。どの接触面にも食い込まない向きのうち、outward にいちばん近い向き。

    接触面の法線（ピースの外向き）n のどれについても、向き d は d·n <= 0 を満たす。
    満たす向きが無ければ ValueError。
    """
    direction = outward / np.linalg.norm(outward)
    normals = [n / np.linalg.norm(n) for n in contact_outwards]
    # 食い込む成分を順に取り除く。ダイクストラの交互射影で、条件を満たす向きのうち
    # outward にいちばん近いものへ収束する
    corrections = [np.zeros(3) for _ in normals]
    for _ in range(200):
        moved = 0.0
        for k, normal in enumerate(normals):
            candidate = direction + corrections[k]
            projected = candidate - max(candidate @ normal, 0.0) * normal
            corrections[k] = candidate - projected
            moved = max(moved, float(np.linalg.norm(projected - direction)))
            direction = projected
        if moved < 1e-12:
            break
    length = np.linalg.norm(direction)
    if length < 1e-6 or any(direction @ normal > 1e-6 for normal in normals):
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
    """
    found = []
    for i, source in enumerate(pieces):
        for j, target in enumerate(pieces):
            if _fits(source, target, i == j, position_tolerance, angle_tolerance):
                found.append((i, j))
    return found


def _fits(source, target, same_piece, position_tolerance, angle_tolerance) -> bool:
    if len(source) < 3 or len(target) < 3:
        return False
    target_points = np.array([frame.point for frame in target])
    target_dirs = np.array([frame.outward for frame in target])
    target_ups = np.array([frame.up for frame in target])
    for triple in combinations(range(len(source)), 3):
        points = np.array([source[k].point for k in triple])
        dirs = np.array([source[k].outward for k in triple])
        ups = np.array([source[k].up for k in triple])
        sides = np.linalg.norm(points - np.roll(points, 1, axis=0), axis=1)
        for match in permutations(range(len(target)), 3):
            if same_piece and match == triple:
                continue
            matched = target_points[list(match)]
            # 辺の長さが合わない組は、重ねる計算をせずに飛ばす
            matched_sides = np.linalg.norm(matched - np.roll(matched, 1, axis=0), axis=1)
            if np.abs(sides - matched_sides).max() > 2 * position_tolerance:
                continue
            rotation, shift = _aligned(points, matched)
            if np.linalg.norm(points @ rotation.T + shift - matched, axis=1).max() > position_tolerance:
                continue
            faces = np.einsum("kd,kd->k", dirs @ rotation.T, target_dirs[list(match)])
            tops = np.einsum("kd,kd->k", ups @ rotation.T, target_ups[list(match)])
            if min(faces.min(), tops.min()) >= np.cos(angle_tolerance):
                return True
    return False
