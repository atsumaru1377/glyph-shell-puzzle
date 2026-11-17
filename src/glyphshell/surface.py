"""字を敷き詰める曲面（三角形メッシュ）と、その上の局所座標。"""

from dataclasses import dataclass

import numpy as np
import potpourri3d as pp3d
import trimesh


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


def local_map(surface: Surface, center: int, radius: float) -> tuple[np.ndarray, np.ndarray]:
    """中心の頂点のまわりの局所座標（対数写像）を返す。

    戻り値は (頂点の番号 [n], 座標 [n, 2])。座標の原点は中心の頂点で、原点からの長さは
    曲面に沿った距離になる。対象は、中心から直線距離で radius より近く、中心と面でつながった
    頂点だけ。曲面の一部だけを解くので、全体を解くより速い。
    """
    near = np.linalg.norm(surface.vertices - surface.vertices[center], axis=1) < radius
    faces = surface.faces[near[surface.faces].all(axis=1)]
    if len(faces) == 0:
        raise ValueError(f"半径 {radius} の中に面がない（中心の頂点 {center}）")
    # 直線距離では近いが曲面の上ではつながっていない部分（薄い形の裏側など）を除く
    edges = np.vstack([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    components = trimesh.graph.connected_components(edges, min_len=1)
    index = np.sort(next(c for c in components if center in c))
    renumber = np.full(len(surface.vertices), -1, dtype=np.int64)
    renumber[index] = np.arange(len(index))
    patch_faces = renumber[faces]
    patch_faces = patch_faces[(patch_faces >= 0).all(axis=1)]
    solver = pp3d.MeshVectorHeatSolver(surface.vertices[index], patch_faces)
    uv = solver.compute_log_map(int(renumber[center]))
    return index, np.asarray(uv)
