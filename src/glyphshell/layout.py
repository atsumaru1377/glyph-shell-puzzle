"""字を曲面に1つずつ置いていく。

いちばん広く空いている所を探し、そこに入る字のうち、隣の字と十分な幅で重なる相手の数が
最も多く、その中で最も広く覆うものを置く。これを、入る字がなくなるまで繰り返す。

字どうしは、決めた深さまで重なってよい。重なった所は後の段で平らに切り分け、
その切り口を接触面（磁石を埋める面）にする。接触面は字の輪郭の内側に収まる。
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import potpourri3d as pp3d

from glyphshell.sdf import GlyphField, signed_distance
from glyphshell.surface import Surface, local_map


@dataclass(frozen=True)
class LayoutParams:
    sizes: tuple[float, ...]  # 使う字の大きさ（キャップハイト）。大きい順
    max_overlap: float  # 字どうしが重なってよい深さ
    min_contact: float  # 接触面に要る幅。これ以上の幅で重なる相手を「接する相手」と数える
    rotations: int  # 試す向きの数（1周を等分する）
    candidates: int  # 1か所につき試す字の数。まだ使っていない字から無作為に選ぶ
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
    solid: np.ndarray  # 字の穴を埋めた形までの符号付き距離。字を置く場所を決めるのに使う


def separation(a: Placement, b: Placement) -> float:
    """2つの字の輪郭どうしの隙間。重なっていれば負（重なりの深さ）。共有する頂点がなければ無限大。

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
    owner: np.ndarray,
    contact_vertices: int,
    unused: list[GlyphField],
    params: LayoutParams,
    rng: np.random.Generator,
) -> Placement | None:
    """center のまわりに置ける字のうち、最も良いものを返す。置ける字がなければ None。"""
    free_radius = float(nearest[center])
    offsets = _offsets(free_radius)
    offset_reach = float(np.linalg.norm(offsets, axis=1).max())
    largest = max(field.radius for field in unused) * params.sizes[0]
    index, uv = local_map(surface, center, largest + offset_reach + params.max_overlap)
    occupied = nearest[index]
    # まわりに置いてある字ごとの印。重なる相手を字ごとに数えるのに使う
    neighbours, label = np.unique(owner[index], return_inverse=True)
    one_hot = (label[:, None] == np.arange(len(neighbours))[None, :]) & (neighbours >= 0)[None, :]
    uv_norm = np.linalg.norm(uv, axis=1)
    angles = rng.uniform(0, 2 * np.pi) + np.arange(params.rotations) * 2 * np.pi / params.rotations
    cos, sin = np.cos(angles)[None, :, None], np.sin(angles)[None, :, None]
    # 毎回すべての字を試すと、面積の大きい字ばかりが選ばれて字の種類が偏る
    order = rng.permutation(len(unused))[: params.candidates]

    best = None
    for k in order:
        field = unused[k]
        # この字が入る最も大きい大きさだけを候補にする
        for size in params.sizes:
            if field.neck * size < params.min_neck or field.min_extent * size < params.min_extent:
                continue
            # 字のいちばん太い所が、いちばん広い空きにも入らないなら、どこにも置けない
            if -field.values.min() * size - params.max_overlap > free_radius:
                continue
            near = uv_norm < field.radius * size + offset_reach + params.max_overlap
            shifted = uv[near][None, None, :, :] - offsets[:, None, None, :]
            # 向きは点のほうを逆に回して与える
            rotated = np.stack(
                [
                    shifted[..., 0] * cos + shifted[..., 1] * sin,
                    -shifted[..., 0] * sin + shifted[..., 1] * cos,
                ],
                axis=-1,
            )
            # 字の穴の中に別の字を置かないよう、穴を埋めた形で重なりを測る
            distance = signed_distance(field, rotated, size, angle=0.0, solid=True)
            total = occupied[near][None, None, :] + distance
            valid = total.min(axis=2) >= -params.max_overlap
            if not valid.any():
                continue
            # 置いてある字ごとに、重なっている頂点を数える。接触面の幅ぶん以上あれば接する相手とする
            overlap = (distance < 0) & (occupied[near] < 0)[None, None, :]
            per_neighbour = overlap.astype(np.float32) @ one_hot[near].astype(np.float32)
            touching = np.minimum((per_neighbour >= contact_vertices).sum(axis=2), 3)
            covered = (distance < 0).sum(axis=2)
            # 接する相手の数（3つまで数える）を先に比べ、同じなら覆う広さで比べる
            gain = np.where(valid, touching * (len(index) + 1) + covered, -1)
            o, r = np.unravel_index(gain.argmax(), gain.shape)
            if best is None or gain[o, r] > best[0]:
                best = (int(gain[o, r]), field, size, o, r, index[near], rotated[o, r], distance[o, r])
            break
    if best is None:
        return None
    _, field, size, o, r, where, points, solid = best
    return Placement(
        char=field.char,
        center=center,
        offset=(float(offsets[o, 0]), float(offsets[o, 1])),
        angle=float(angles[r]),
        size=size,
        index=where,
        distance=signed_distance(field, points, size, angle=0.0),
        solid=solid.copy(),
    )


def pack(
    surface: Surface,
    fields: list[GlyphField],
    params: LayoutParams,
    existing: list[Placement] | None = None,
) -> list[Placement]:
    """字を曲面に敷き詰める。同じ字は1回しか使わない。

    existing を渡すと、その配置を残したまま、空いている所に字を足す。
    戻り値は existing の後ろに足した字が続く。
    """
    rng = np.random.default_rng(params.seed)
    count = len(surface.vertices)
    nearest = np.full(count, np.inf)  # 置いた字の輪郭までの距離の最小
    owner = np.full(count, -1, dtype=np.int64)  # いちばん近い字の番号
    edges = surface.vertices[surface.faces[:, 0]] - surface.vertices[surface.faces[:, 1]]
    # 接触面の幅に並ぶ頂点の数
    contact_vertices = int(np.ceil(params.min_contact / np.linalg.norm(edges, axis=1).mean()))
    heat = pp3d.MeshHeatMethodDistanceSolver(surface.vertices, surface.faces)
    tried = np.zeros(count, dtype=bool)  # 入る字がなかった空きの中の頂点
    placements: list[Placement] = []

    def add(placement: Placement) -> None:
        nonlocal nearest
        placements.append(placement)
        # 字の近くは輪郭までの正確な距離、遠くは字の内側の頂点からの曲面上の距離（近似）を使う
        far = heat.compute_distance_multisource(placement.index[placement.solid < 0])
        far[placement.index] = placement.solid
        owner[far < nearest] = len(placements) - 1
        nearest = np.minimum(nearest, far)

    for placement in existing or []:
        add(placement)
    used = {placement.char for placement in placements}
    unused = [field for field in fields if field.char not in used]
    center = int(rng.integers(count))
    while unused:
        if placements:
            free = np.where(tried, -np.inf, nearest)
            center = int(free.argmax())
            if free[center] <= 0:
                break
        placement = _best_at(
            surface, center, nearest, owner, contact_vertices, unused, params, rng
        )
        if placement is None:
            if not placements:
                break
            # この空き円には入る字がなかったので、円の中を次の中心の候補から外す
            reach = np.linalg.norm(surface.vertices - surface.vertices[center], axis=1)
            tried |= reach <= nearest[center]
            continue
        add(placement)
        unused = [field for field in unused if field.char != placement.char]
    return placements


def save_layout(path: Path, placements: list[Placement]) -> None:
    """配置を1つの .npz ファイルに書く。頂点ごとの値は、全ピースぶんをつなげて持つ。"""
    np.savez_compressed(
        path,
        char=np.array([p.char for p in placements]),
        center=np.array([p.center for p in placements], dtype=np.int64),
        offset=np.array([p.offset for p in placements], dtype=float).reshape(-1, 2),
        angle=np.array([p.angle for p in placements], dtype=float),
        size=np.array([p.size for p in placements], dtype=float),
        count=np.array([len(p.index) for p in placements], dtype=np.int64),
        index=np.concatenate([p.index for p in placements]) if placements else np.zeros(0, np.int64),
        distance=np.concatenate([p.distance for p in placements]) if placements else np.zeros(0),
        solid=np.concatenate([p.solid for p in placements]) if placements else np.zeros(0),
    )


def load_layout(path: Path) -> list[Placement]:
    """save_layout で書いた配置を読む。"""
    with np.load(path) as data:
        ends = np.cumsum(data["count"])
        starts = ends - data["count"]
        return [
            Placement(
                char=str(data["char"][i]),
                center=int(data["center"][i]),
                offset=(float(data["offset"][i, 0]), float(data["offset"][i, 1])),
                angle=float(data["angle"][i]),
                size=float(data["size"][i]),
                index=data["index"][starts[i] : ends[i]],
                distance=data["distance"][starts[i] : ends[i]],
                solid=data["solid"][starts[i] : ends[i]],
            )
            for i in range(len(ends))
        ]
