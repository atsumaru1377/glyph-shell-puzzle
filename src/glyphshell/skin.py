"""複雑な形の内側に、字を敷き詰めるためのなめらかな面を作る。

元の形を、殻の厚さ以上の深さまで内側へ下げ、でこぼこをならした面を「内側の面」とする。
字はこの面の上に敷き詰める。ピースは、内側の面から外へ押し出した柱を元の形で切り取って
作るので、内側はなめらか、外側は元の形の表面になる。

耳のように細長い部分には、内側の面が入らない。残すと、根元のピースから長い柱として生えて
しまうので、先に元の形から切り離して、字のピースとは別の追加のパーツにする。
"""

from dataclasses import dataclass

import manifold3d
import numpy as np
import trimesh
from scipy import ndimage
from scipy.spatial import cKDTree

from glyphshell.surface import Surface

# 距離の格子の刻みを、殻の厚さの何分の1にするか。ならす幅（殻の厚さ）に格子が4つ入る
CELLS_PER_THICKNESS = 4
# 格子の線が元の形の頂点や辺の真上を通らないよう、格子をずらす量（刻みに対する割合）。
# 半端な値であればよく、値そのものに意味はない
GRID_SHIFT = np.array([0.137, 0.291, 0.419])
# 内側の面を下げる深さを決め直す回数の上限。1回ごとに不足ぶん以上深くなるので、ふつう2回で決まる
INSET_ROUNDS = 10
# 細長い部分とみなす細長さ（突き出しの長さ ÷ 断面の一辺）の下限（仮の値。担当者の承認が要る）。
# 高さ 300 mm のうさぎでは、耳が 4.1 と 3.9、足先と底の縁がつながった塊が 0.6 で、その間に置いた
SLENDER_RATIO = 2.0
# 押し出した先で、押し出し元より近い面の点があるかを比べるときの許容差。計算の丸めより十分大きく、
# メッシュの辺の長さより十分小さい
NEAREST_TOLERANCE = 0.01
# 押し出した先でいちばん近い頂点が、押し出し元から「辺 SAME_PLACE_EDGES 本ぶん以内」か
# 「押し出した長さの SAME_PLACE_RATIO 倍以内」なら、面の同じ所とみなす。面の曲がりで隣の頂点が
# わずかに近くなるのは、別の所の柱に入ったのとは違う（くぼみでの隣どうしのぶつかりは、
# EDGE_SHRINK_LIMIT で別に止める）。4分の1は、約 15 度より深い角度で交わる柱を見分けられる値
SAME_PLACE_EDGES = 2
SAME_PLACE_RATIO = 0.25
# 押し出した面の辺が、元の長さのこの割合より短くならないようにする。
# 0 で辺がつぶれ、負で面が裏返る。半分までにとどめれば、頂点ごとの長さの違いがあっても裏返らない
EDGE_SHRINK_LIMIT = 0.5


@dataclass(frozen=True)
class Skin:
    surface: Surface  # 内側の面。法線は外向き
    outer: manifold3d.Manifold  # 元の形から細い部分を切り離した残り。ピースの外側の面になる
    parts: list[manifold3d.Manifold]  # 切り離した細い部分（耳など）。体積の大きい順
    reach: np.ndarray  # [V] 内側の面から外へ押し出す長さ。outer の表面より少し先まで
    inset: float  # 内側の面を下げた深さ


@dataclass(frozen=True)
class _Grid:
    """格子の上の符号付き距離（内側が正）。"""

    low: np.ndarray
    cell: float
    values: np.ndarray

    def sample(self, points: np.ndarray) -> np.ndarray:
        return ndimage.map_coordinates(self.values, ((points - self.low) / self.cell).T, order=1, mode="nearest")

    def gradient(self, points: np.ndarray) -> np.ndarray:
        step = self.cell / 2
        return np.stack(
            [(self.sample(points + step * axis) - self.sample(points - step * axis)) / (2 * step) for axis in np.eye(3)],
            axis=1,
        )


def _manifold(vertices: np.ndarray, faces: np.ndarray) -> manifold3d.Manifold:
    return manifold3d.Manifold(
        manifold3d.Mesh(
            vert_properties=np.ascontiguousarray(vertices, dtype=np.float32),
            tri_verts=np.ascontiguousarray(faces, dtype=np.uint32),
        )
    )


def _inside(vertices: np.ndarray, faces: np.ndarray, axes: list[np.ndarray]) -> np.ndarray:
    """格子の各点が形の内側かどうか。z 方向の線が面を横切る回数の偶奇で決める。"""
    tri = vertices[faces]
    a, b, c = tri[:, 0, :2], tri[:, 1, :2], tri[:, 2, :2]
    det = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    seen = det != 0  # 真横から見て線になる三角形は、z 方向の線と交わらない
    a, b, c, det, tri = a[seen], b[seen], c[seen], det[seen], tri[seen]
    shape = tuple(len(axis) for axis in axes)
    crossings = np.zeros(shape, dtype=np.int32)
    y = axes[1][:, None]
    for i, x in enumerate(axes[0]):
        u = ((x - a[:, 0]) * (c[:, 1] - a[:, 1]) - (y - a[:, 1]) * (c[:, 0] - a[:, 0])) / det
        v = ((b[:, 0] - a[:, 0]) * (y - a[:, 1]) - (b[:, 1] - a[:, 1]) * (x - a[:, 0])) / det
        row, hit = np.nonzero((u >= 0) & (v >= 0) & (u + v <= 1))
        z = tri[hit, 0, 2] + u[row, hit] * (tri[hit, 1, 2] - tri[hit, 0, 2]) + v[row, hit] * (tri[hit, 2, 2] - tri[hit, 0, 2])
        above = np.searchsorted(axes[2], z)  # 交点より上にある最初の格子点
        np.add.at(crossings[i], (row[above < shape[2]], above[above < shape[2]]), 1)
    return np.cumsum(crossings, axis=2) % 2 == 1


def _distance_grid(outer: manifold3d.Manifold, vertices: np.ndarray, faces: np.ndarray, cell: float, pad: float):
    """元の形までの符号付き距離を格子の上に作る。表面に細かく取った点の木も返す。"""
    low = vertices.min(axis=0) - pad + cell * GRID_SHIFT
    axes = [np.arange(low[k], vertices[:, k].max() + pad, cell) for k in range(3)]
    dense, _ = trimesh.remesh.subdivide_to_size(vertices, faces, max_edge=cell / 2)
    tree = cKDTree(dense)
    points = np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1)
    distance = tree.query(points.reshape(-1, 3), workers=-1)[0].reshape(points.shape[:3])
    inside = _inside(vertices, faces, axes)
    # 内か外かの判定が大きく狂っていないかを、体積で確かめる。格子で数えた体積の誤差は、
    # 表面の1層ぶん（表面積 × 刻み）を超えない
    if abs(inside.sum() * cell**3 - outer.volume()) > outer.surface_area() * cell:
        raise ValueError("形の内側と外側を判定できなかった")
    return _Grid(low, cell, np.where(inside, distance, -distance)), tree


def _level_solid(grid: _Grid, level: float, edge_length: float) -> manifold3d.Manifold:
    """格子の値が level 以上の所を立体にする。"""
    high = grid.low + (np.array(grid.values.shape) - 1) * grid.cell
    return manifold3d.Manifold.level_set(
        lambda x, y, z: float(grid.sample(np.array([[x, y, z]]))[0]), [*grid.low, *high], edge_length, level
    )


def _arrays(solid: manifold3d.Manifold) -> tuple[np.ndarray, np.ndarray]:
    mesh = solid.to_mesh()
    return np.asarray(mesh.vert_properties[:, :3], dtype=float), np.asarray(mesh.tri_verts, dtype=np.int64)


def _level_surface(grid: _Grid, level: float, edge_length: float) -> Surface:
    """ならした距離が level の面を取り出す。離れた塊があれば、体積がいちばん大きい塊だけを使う。"""
    parts = _level_solid(grid, level, 2 * edge_length).decompose()
    if not parts:
        raise ValueError("内側の面が残らない。形が殻の厚さに比べて細すぎる")
    fine_vertices, fine_faces = trimesh.remesh.subdivide_to_size(
        *_arrays(max(parts, key=lambda part: part.volume())), max_edge=edge_length
    )
    fine = trimesh.Trimesh(vertices=fine_vertices, faces=fine_faces, process=True)
    points = np.asarray(fine.vertices, dtype=float)
    for _ in range(3):  # 辺を分けてできた頂点を、面の上へ寄せる（ニュートン法。3回で 0.001 mm 以下になる）
        gradient = grid.gradient(points)
        points = points + ((level - grid.sample(points)) / (gradient**2).sum(axis=1))[:, None] * gradient
    gradient = grid.gradient(points)
    normals = -gradient / np.linalg.norm(gradient, axis=1, keepdims=True)
    return Surface(points, np.asarray(fine.faces, dtype=np.int64), normals)


def _reach(surface: Surface, raw: _Grid) -> np.ndarray:
    """内側の面の各頂点から、法線に沿って外へ押し出す長さ。

    形の表面までの長さの2倍まで。押し出した面は頂点の間が平らなので、表面のすぐ外で止めると、
    とがった縁の角を平らな面が削ってしまう。2倍まで出せば、面は表面から厚みぶん離れる。
    ただし、押し出した先から見て、面の別の所のほうが近くなる手前で止める（その先は、別の所から
    押し出した柱の持ち分で、越えるとピースどうしが重なる）。くぼんだ所では、隣の頂点の法線と
    ぶつかる手前で止める。
    """
    step = raw.cell / CELLS_PER_THICKNESS
    tree = cKDTree(surface.vertices)
    pairs = np.vstack([surface.faces[:, [0, 1]], surface.faces[:, [1, 2]], surface.faces[:, [2, 0]]])
    edge = surface.vertices[pairs[:, 1]] - surface.vertices[pairs[:, 0]]
    same_place = SAME_PLACE_EDGES * float(np.linalg.norm(edge, axis=1).max())
    length = np.zeros(len(surface.vertices))
    exit_at = np.full(len(surface.vertices), np.inf)  # 形の表面を越えた長さ
    active = np.arange(len(surface.vertices))
    while len(active):
        ahead = length[active] + step
        points = surface.vertices[active] + ahead[:, None] * surface.normals[active]
        distance, nearest = tree.query(points)
        apart = np.linalg.norm(surface.vertices[nearest] - surface.vertices[active], axis=1)
        elsewhere = apart > np.maximum(same_place, SAME_PLACE_RATIO * ahead)
        own = ~(elsewhere & (distance < ahead - NEAREST_TOLERANCE))
        active, ahead, points = active[own], ahead[own], points[own]
        length[active] = ahead
        left = np.isinf(exit_at[active]) & (raw.sample(points) < 0)
        exit_at[active[left]] = ahead[left]
        active = active[ahead < 2 * exit_at[active]]
    reach = length
    # 辺 (u, v) を長さ h だけ押し出すと、辺の向きの成分は |e|² + h e·(n_v − n_u) になる。
    # 法線が寄っていく辺（e·(n_v − n_u) < 0）では、これが元の EDGE_SHRINK_LIMIT 倍になる h までにする
    closing = -(edge * (surface.normals[pairs[:, 1]] - surface.normals[pairs[:, 0]])).sum(axis=1)
    narrowing = closing > 0
    bound = (1 - EDGE_SHRINK_LIMIT) * (edge[narrowing] ** 2).sum(axis=1) / closing[narrowing]
    np.minimum.at(reach, pairs[narrowing, 0], bound)
    np.minimum.at(reach, pairs[narrowing, 1], bound)
    return reach


def _split_slender_parts(
    outer: manifold3d.Manifold, raw: _Grid, radius: float
) -> tuple[manifold3d.Manifold, list[manifold3d.Manifold]]:
    """太さが radius の2倍より細く、細長く突き出している部分を切り離す。(残り, 切り離した部分) を返す。

    形を radius だけ縮めてから同じだけ太らせると、radius の2倍より細い所は戻らない。
    戻らなかった塊のうち、細長さ（太らせた形からの突き出しの長さ ÷ 断面の一辺）が SLENDER_RATIO を
    超えるものを切り離す。断面の一辺は、体積 ÷ 長さ の平方根。とがった縁に残る薄いかけらや、
    足先のような短い出っ張りは、細長くないので切り離さない。
    """
    core = raw.values >= radius
    if not core.any():
        return outer, []
    away = ndimage.distance_transform_edt(~core, sampling=raw.cell)  # 縮めた形までの距離
    # 格子の段がそのまま切り口に出ないよう、刻み1つぶんの幅でならしてから面にする。格子の上の距離は
    # 刻み1つぶんまで狂うので、太らせた形はそのぶん大きく取る。小さく取ると、形の表面の全体が
    # 薄い皮として残り、細い部分とつながってしまう
    field = _Grid(raw.low, raw.cell, ndimage.gaussian_filter(radius - away, 1.0))
    opened = _level_solid(field, -raw.cell, 2 * raw.cell)
    parts = []
    for part in (outer - opened).decompose():
        if part.volume() <= 0:  # 空洞の面は立体ではない
            continue
        points = _arrays(part)[0]
        length = float(ndimage.map_coordinates(away, ((points - raw.low) / raw.cell).T, order=1).max()) - radius
        # 突き出しが radius より短い塊は、細長くても切り離さない（とがった縁のかけらや小さなとげ）
        if length > radius and length**3 > SLENDER_RATIO**2 * part.volume():
            parts.append(part)
    parts.sort(key=lambda part: -part.volume())
    body = outer
    for part in parts:
        body = body - part
    return max(body.decompose(), key=lambda piece: piece.volume()), parts


def _inner_surface(outer: manifold3d.Manifold, thickness: float, edge_length: float) -> tuple[Surface, _Grid, float]:
    """形の内側の面を作る。(面, 形までの距離の格子, 面を下げた深さ) を返す。

    形までの距離を、殻の厚さの幅でならす（殻の厚さより細かいでこぼこが消える）。ならした距離が
    一定の面を内側の面にする。深さは殻の厚さから始め、形の表面までの距離がどこでも殻の厚さ以上に
    なるまで深くする。
    """
    cell = thickness / CELLS_PER_THICKNESS
    raw, tree = _distance_grid(outer, *_arrays(outer), cell, pad=3 * thickness + 2 * cell)
    smooth = _Grid(raw.low, cell, ndimage.gaussian_filter(raw.values, thickness / cell))
    inset = thickness
    for _ in range(INSET_ROUNDS):
        surface = _level_surface(smooth, inset, edge_length)
        shortfall = thickness - float(tree.query(surface.vertices)[0].min())
        if shortfall <= 0:
            return surface, raw, inset
        inset += shortfall
    raise ValueError("内側の面を、殻の厚さが取れる深さに決められなかった")


def inner_skin(vertices: np.ndarray, faces: np.ndarray, thickness: float, edge_length: float) -> Skin:
    """閉じた形から、細長い部分を切り離し、残りの内側の面を作る。"""
    whole = _manifold(vertices, faces)
    if whole.status() != manifold3d.Error.NoError or whole.volume() <= 0:
        raise ValueError("面の向きがそろった閉じた立体ではない")
    surface, raw, inset = _inner_surface(whole, thickness, edge_length)
    # 内側の面が入れない太さ。厚さ 2h の板の真ん中では、ならした距離が h − √(2/π) × ならす幅 に
    # なる（板を横切る向きにだけ距離が変わるとして、正規分布の絶対値の平均を引いた値）。これが
    # 面を下げた深さに届かない板には、内側の面ができない
    radius = inset + np.sqrt(2 / np.pi) * thickness
    outer, parts = _split_slender_parts(whole, raw, radius)
    if parts:
        surface, raw, inset = _inner_surface(outer, thickness, edge_length)
    return Skin(surface, outer, parts, _reach(surface, raw), inset)


def unreached_volume(skin: Skin) -> float:
    """skin.outer のうち、内側の面から押し出した柱が届かない所の体積。どのピースにも入らない。"""
    top = skin.surface.vertices + skin.reach[:, None] * skin.surface.normals
    filled = _manifold(top, skin.surface.faces)
    if filled.status() != manifold3d.Error.NoError or filled.volume() <= 0:
        raise ValueError("押し出した面が閉じた立体にならない")
    return float((skin.outer - filled).volume())
