"""頂点の上の値で表したピースを、厚みのある立体にして、磁石の穴を開ける。"""

from dataclasses import dataclass

import manifold3d
import numpy as np
import trimesh

from glyphshell.surface import Surface

# 値が 0 になる点を辺の上に置くとき、辺の端からこの割合より近くには置かない。
# 端に重なると面積 0 の三角形ができ、立体の演算が不安定になる。
# 辺の長さ 1.4 mm のとき 0.03 mm で、印刷の精度より十分小さい。
EDGE_GUARD = 0.02
# 穴の円柱を、接触面から外へはみ出させる長さ。面とちょうど重なる底を作らないため。
POCKET_OVERSHOOT = 0.5
POCKET_SEGMENTS = 48


@dataclass(frozen=True)
class Region:
    """曲面から切り出した1つの塊。"""

    vertices: np.ndarray  # [n, 3]
    normals: np.ndarray  # [n, 3]
    faces: np.ndarray  # [m, 3]
    dropped_area: float  # 捨てた小さい島の面積の合計


@dataclass(frozen=True)
class Pocket:
    """磁石の穴。接触面の中心から、ピースの内側へ掘る。"""

    point: np.ndarray  # 接触面の中心（曲面の上）
    normal: np.ndarray  # その点での曲面の外向きの法線
    into: np.ndarray  # 掘る向き（接触面に垂直で、ピースの内側を向く）


def _triangle_areas(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    tri = vertices[faces]
    return np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) / 2


def clip_region(surface: Surface, field: np.ndarray) -> Region:
    """曲面のうち field が負の所を切り出す。縁は、辺の上で値を直線で補間して 0 になる点を通る。

    離れた塊がいくつもあるときは、面積がいちばん大きい塊だけを残す。
    """
    field = np.where(np.isfinite(field), field, 1e6)
    inside = field < 0
    if not inside.any():
        raise ValueError("内側の頂点がない")
    faces = surface.faces[inside[surface.faces].any(axis=1)]
    count = len(surface.vertices)

    # 内側と外側をまたぐ辺に新しい頂点を作る。辺は番号の小さい頂点から大きい頂点への向きで扱い、
    # 隣のピースが同じ辺を切るときに同じ点になるようにする
    pairs = np.vstack([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    pairs = pairs[inside[pairs[:, 0]] != inside[pairs[:, 1]]]
    keys = np.unique(np.minimum(pairs[:, 0], pairs[:, 1]) * count + np.maximum(pairs[:, 0], pairs[:, 1]))
    low, high = keys // count, keys % count
    t = np.clip(field[low] / (field[low] - field[high]), EDGE_GUARD, 1 - EDGE_GUARD)[:, None]
    cut_vertices = surface.vertices[low] * (1 - t) + surface.vertices[high] * t
    cut_normals = surface.normals[low] * (1 - t) + surface.normals[high] * t
    cut_normals /= np.linalg.norm(cut_normals, axis=1, keepdims=True)

    def cut(u: np.ndarray, v: np.ndarray) -> np.ndarray:
        return count + np.searchsorted(keys, np.minimum(u, v) * count + np.maximum(u, v))

    triangles = [faces[inside[faces].all(axis=1)]]
    for shift in range(3):
        a, b, c = (faces[:, (shift + k) % 3] for k in range(3))
        one = inside[a] & ~inside[b] & ~inside[c]  # a だけが内側
        triangles.append(np.stack([a[one], cut(a[one], b[one]), cut(a[one], c[one])], axis=1))
        two = inside[a] & inside[b] & ~inside[c]  # a と b が内側
        ac, bc = cut(a[two], c[two]), cut(b[two], c[two])
        triangles.append(np.stack([a[two], b[two], bc], axis=1))
        triangles.append(np.stack([a[two], bc, ac], axis=1))
    all_faces = np.vstack(triangles)
    all_vertices = np.vstack([surface.vertices, cut_vertices])
    all_normals = np.vstack([surface.normals, cut_normals])

    # つながった塊に分け、面積がいちばん大きい塊を残す
    edges = np.vstack([all_faces[:, [0, 1]], all_faces[:, [1, 2]]])
    components = trimesh.graph.connected_components(edges, min_len=1)
    label = np.full(len(all_vertices), -1, dtype=np.int64)
    for k, component in enumerate(components):
        label[component] = k
    areas = np.bincount(label[all_faces[:, 0]], weights=_triangle_areas(all_vertices, all_faces))
    largest = int(areas.argmax())
    kept_faces = all_faces[label[all_faces[:, 0]] == largest]
    used = np.unique(kept_faces)
    renumber = np.full(len(all_vertices), -1, dtype=np.int64)
    renumber[used] = np.arange(len(used))
    return Region(
        vertices=all_vertices[used],
        normals=all_normals[used],
        faces=renumber[kept_faces],
        dropped_area=float(areas.sum() - areas[largest]),
    )


def thicken(region: Region, thickness: float) -> manifold3d.Manifold:
    """切り出した面を、法線の内向きに thickness だけ下げた面と壁でつなぎ、閉じた立体にする。"""
    n = len(region.vertices)
    inner = region.vertices - thickness * region.normals
    faces = region.faces
    # 縁の辺は、1つの三角形にしか属さない辺。向きつきの辺 (u, v) の逆向き (v, u) が無いもの
    directed = np.vstack([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    keys = directed[:, 0] * n + directed[:, 1]
    boundary = directed[~np.isin(keys, directed[:, 1] * n + directed[:, 0])]
    u, v = boundary[:, 0], boundary[:, 1]
    walls = np.vstack([np.stack([u, u + n, v], axis=1), np.stack([v, u + n, v + n], axis=1)])
    triangles = np.vstack([faces, faces[:, ::-1] + n, walls])
    mesh = manifold3d.Mesh(
        vert_properties=np.ascontiguousarray(np.vstack([region.vertices, inner]), dtype=np.float32),
        tri_verts=np.ascontiguousarray(triangles, dtype=np.uint32),
    )
    solid = manifold3d.Manifold(mesh)
    if solid.status() != manifold3d.Error.NoError:
        raise ValueError(f"閉じた立体にならない: {solid.status().name}")
    return solid


def piece_solid(
    region: Region, thickness: float, pockets: list[Pocket], hole_diameter: float, hole_depth: float
) -> manifold3d.Manifold:
    """厚みを付けた立体に、磁石の穴を開ける。穴の中心は厚みの真ん中に置く。"""
    solid = thicken(region, thickness)
    for pocket in pockets:
        axis = pocket.into / np.linalg.norm(pocket.into)
        side = np.cross(pocket.normal, axis)
        up = np.cross(axis, side)
        start = pocket.point - pocket.normal * thickness / 2 - axis * POCKET_OVERSHOOT
        # 円柱は z 軸に沿って作られるので、z 軸を掘る向きに合わせる
        transform = np.column_stack([side, up, axis, start])
        cylinder = manifold3d.Manifold.cylinder(
            hole_depth + POCKET_OVERSHOOT, hole_diameter / 2, circular_segments=POCKET_SEGMENTS
        ).transform(transform)
        solid = solid - cylinder
    return solid
