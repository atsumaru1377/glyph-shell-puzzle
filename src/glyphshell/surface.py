"""字を敷き詰める曲面（三角形メッシュ）と、その上の局所座標。"""

from dataclasses import dataclass
from pathlib import Path

import manifold3d
import numpy as np
import potpourri3d as pp3d
import trimesh


# 局所座標を解く範囲を、返す範囲より広く取る倍率。
# 解いた範囲の外周1割では誤差が大きい（球で測って最大 2.5 mm。内側9割は 0.05 mm 以下）ので、
# 返すのは内側8割だけにする
SOLVE_MARGIN = 1.25


@dataclass(frozen=True)
class Surface:
    vertices: np.ndarray  # [V, 3]
    faces: np.ndarray  # [F, 3]
    normals: np.ndarray  # [V, 3] 外向きの単位法線


def icosphere(radius: float, subdivisions: int) -> Surface:
    mesh = trimesh.creation.icosphere(subdivisions=subdivisions, radius=radius)
    return Surface(
        vertices=np.asarray(mesh.vertices, dtype=float),
        faces=np.asarray(mesh.faces, dtype=np.int64),
        normals=np.asarray(mesh.vertex_normals, dtype=float),
    )


def load_surface(path: Path, height: float, edge_length: float) -> Surface:
    """メッシュのファイル（STL、OBJ、OFF、PLY など）を読み、字を敷き詰められる曲面にする。

    いちばん長い辺が height になるよう拡大縮小し、どの辺も edge_length 以下になるまで
    三角形を分ける。閉じていないメッシュ、裏返った面のあるメッシュは ValueError にする。
    """
    mesh = trimesh.load_mesh(path, process=True)
    if not isinstance(mesh, trimesh.Trimesh) or not mesh.is_watertight:
        raise ValueError(f"閉じた1つのメッシュだけを扱える: {path}")
    extent = float(mesh.extents.max())
    if extent <= 0:
        raise ValueError(f"大きさが 0 のメッシュ: {path}")
    vertices = (np.asarray(mesh.vertices) - mesh.bounds.mean(axis=0)) * (height / extent)
    solid = manifold3d.Manifold(
        manifold3d.Mesh(
            vert_properties=np.ascontiguousarray(vertices, dtype=np.float32),
            tri_verts=np.ascontiguousarray(mesh.faces, dtype=np.uint32),
        )
    )
    if solid.status() != manifold3d.Error.NoError or solid.volume() <= 0:
        raise ValueError(f"面の向きがそろった閉じた立体ではない: {path}")
    fine_vertices, fine_faces = trimesh.remesh.subdivide_to_size(vertices, mesh.faces, max_edge=edge_length)
    refined = trimesh.Trimesh(vertices=fine_vertices, faces=fine_faces, process=True)
    return Surface(
        vertices=np.asarray(refined.vertices, dtype=float),
        faces=np.asarray(refined.faces, dtype=np.int64),
        normals=np.asarray(refined.vertex_normals, dtype=float),
    )


def local_map(surface: Surface, center: int, radius: float) -> tuple[np.ndarray, np.ndarray]:
    """中心の頂点のまわりの局所座標（対数写像）を返す。

    戻り値は (頂点の番号 [n], 座標 [n, 2])。座標の原点は中心の頂点で、原点からの長さは
    曲面に沿った距離になる。対象は、中心から直線距離で radius より近く、中心と面でつながった
    頂点だけ。曲面の一部（radius の SOLVE_MARGIN 倍まで）だけを解くので、全体を解くより速い。
    """
    reach = np.linalg.norm(surface.vertices - surface.vertices[center], axis=1)
    near = reach < radius * SOLVE_MARGIN
    faces = surface.faces[near[surface.faces].all(axis=1)]
    if not (reach[faces] < radius).any():
        raise ValueError(f"半径 {radius} の中に面がない（中心の頂点 {center}）")
    # 直線距離では近いが曲面の上ではつながっていない部分（薄い形の裏側など）を除く
    edges = np.vstack([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    components = trimesh.graph.connected_components(edges, min_len=1)
    solved = np.sort(next(c for c in components if center in c))
    renumber = np.full(len(surface.vertices), -1, dtype=np.int64)
    renumber[solved] = np.arange(len(solved))
    patch_faces = renumber[faces]
    patch_faces = patch_faces[(patch_faces >= 0).all(axis=1)]
    solver = pp3d.MeshVectorHeatSolver(surface.vertices[solved], patch_faces)
    uv = np.asarray(solver.compute_log_map(int(renumber[center])))
    inner = reach[solved] < radius
    return solved[inner], uv[inner]
