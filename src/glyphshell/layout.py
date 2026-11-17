"""字を曲面に1つずつ置いていく。

いちばん広く空いている所を探し、そこに入る字のうち、覆う広さと隣の字に近い所の広さの和が
最も大きいものを置く。これを、入る字がなくなるまで繰り返す。
"""

from dataclasses import dataclass

import numpy as np
import potpourri3d as pp3d

from glyphshell.sdf import GlyphField, signed_distance
from glyphshell.surface import Surface, local_map


@dataclass(frozen=True)
class LayoutParams:
    sizes: tuple[float, ...]  # 使う字の大きさ（キャップハイト）。大きい順
    min_gap: float  # 字の輪郭どうしの最小の隙間。メッシュの辺の長さ以上にする
    reach: float  # 隣とつなぐ（橋渡しする）隙間の上限
    rotations: int  # 試す向きの数（1周を等分する）
    min_neck: float  # 字のいちばん細い所に要る幅
    min_extent: float  # 字の外接する箱の短い辺に要る長さ
    seed: int


@dataclass(frozen=True)
class Placement:
    char: str
    center: int  # 局所座標の原点にした頂点
    offset: tuple[float, float]  # 局所座標での字の中心
    angle: float
    size: float
    index: np.ndarray  # 字の距離を持つ頂点の番号
    distance: np.ndarray  # その頂点から字の輪郭までの符号付き距離（内側が負）


def separation(a: Placement, b: Placement) -> float:
    """2つの字の輪郭どうしの隙間。重なっていれば負。共有する頂点がなければ無限大。

    両方の距離を持つ頂点での距離の和の最小で測る。頂点の上でしか測らないので、
    真の隙間より最大でメッシュの辺の長さ程度まで大きく出る。
    """
    _, ia, ib = np.intersect1d(a.index, b.index, assume_unique=True, return_indices=True)
    if len(ia) == 0:
        return float("inf")
    return float((a.distance[ia] + b.distance[ib]).min())


def _offsets(free_radius: float) -> np.ndarray:
    """字の中心をずらす候補。空き円の中心と、そのまわりの六角形の頂点。"""
    if not np.isfinite(free_radius):
        return np.zeros((1, 2))
    angles = np.arange(6) * np.pi / 3
    ring = free_radius / 3 * np.stack([np.cos(angles), np.sin(angles)], axis=1)
    return np.vstack([np.zeros((1, 2)), ring])


def _best_at(
    surface: Surface,
    center: int,
    nearest: np.ndarray,
    unused: list[GlyphField],
    params: LayoutParams,
    rng: np.random.Generator,
) -> Placement | None:
    """center のまわりに置ける字のうち、最も良いものを返す。置ける字がなければ None。"""
    free_radius = float(nearest[center])
    offsets = _offsets(free_radius)
    offset_reach = float(np.linalg.norm(offsets, axis=1).max())
    largest = max(field.radius for field in unused) * params.sizes[0]
    index, uv = local_map(surface, center, largest + offset_reach + params.reach)
    occupied = nearest[index]
    uv_norm = np.linalg.norm(uv, axis=1)
    angles = rng.uniform(0, 2 * np.pi) + np.arange(params.rotations) * 2 * np.pi / params.rotations
    cos, sin = np.cos(angles)[None, :, None], np.sin(angles)[None, :, None]
    order = rng.permutation(len(unused))

    best = None
    for k in order:
        field = unused[k]
        # この字が入る最も大きい大きさだけを候補にする
        for size in params.sizes:
            if field.neck * size < params.min_neck or field.min_extent * size < params.min_extent:
                continue
            # 字のいちばん太い所が、いちばん広い空きにも入らないなら、どこにも置けない
            if -field.values.min() * size + params.min_gap > free_radius:
                continue
            near = uv_norm < field.radius * size + offset_reach + params.reach
            shifted = uv[near][None, None, :, :] - offsets[:, None, None, :]
            # 向きは点のほうを逆に回して与える
            rotated = np.stack(
                [
                    shifted[..., 0] * cos + shifted[..., 1] * sin,
                    -shifted[..., 0] * sin + shifted[..., 1] * cos,
                ],
                axis=-1,
            )
            distance = signed_distance(field, rotated, size, angle=0.0)
            total = occupied[near][None, None, :] + distance
            valid = total.min(axis=2) >= params.min_gap
            if not valid.any():
                continue
            # 字が覆う広さと、隣の字との隙間が reach 以下になる所の広さの和（頂点の数）。
            # 大きい字ほど、また隣と多く接するほど高い
            gain = (distance < 0).sum(axis=2) + ((total <= params.reach) & (distance > 0)).sum(axis=2)
            gain = np.where(valid, gain, -1)
            o, r = np.unravel_index(gain.argmax(), gain.shape)
            if best is None or gain[o, r] > best[0]:
                best = (int(gain[o, r]), field, size, o, r, index[near], distance[o, r])
            break
    if best is None:
        return None
    _, field, size, o, r, where, distance = best
    return Placement(
        char=field.char,
        center=center,
        offset=(float(offsets[o, 0]), float(offsets[o, 1])),
        angle=float(angles[r]),
        size=size,
        index=where,
        distance=distance.copy(),
    )


def pack(surface: Surface, fields: list[GlyphField], params: LayoutParams) -> list[Placement]:
    """字を曲面に敷き詰める。同じ字は1回しか使わない。"""
    rng = np.random.default_rng(params.seed)
    count = len(surface.vertices)
    nearest = np.full(count, np.inf)  # 置いた字の輪郭までの距離の最小
    heat = pp3d.MeshHeatMethodDistanceSolver(surface.vertices, surface.faces)
    tried = np.zeros(count, dtype=bool)  # 入る字がなかった空きの中の頂点
    unused = list(fields)
    placements: list[Placement] = []
    center = int(rng.integers(count))
    while unused:
        if placements:
            free = np.where(tried, -np.inf, nearest)
            center = int(free.argmax())
            if free[center] <= params.min_gap:
                break
        placement = _best_at(surface, center, nearest, unused, params, rng)
        if placement is None:
            if not placements:
                break
            # この空き円には入る字がなかったので、円の中を次の中心の候補から外す
            reach = np.linalg.norm(surface.vertices - surface.vertices[center], axis=1)
            tried |= reach <= nearest[center]
            continue
        placements.append(placement)
        # 字の近くは輪郭までの正確な距離、遠くは字の内側の頂点からの曲面上の距離（近似）を使う
        far = heat.compute_distance_multisource(placement.index[placement.distance < 0])
        far[placement.index] = placement.distance
        nearest = np.minimum(nearest, far)
        unused = [field for field in unused if field.char != placement.char]
    return placements
