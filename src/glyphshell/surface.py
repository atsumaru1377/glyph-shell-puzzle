"""字を敷き詰める曲面（三角形メッシュ）と、その上の局所座標。"""

from dataclasses import dataclass
from pathlib import Path

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


def load_mesh(path: Path, height: float) -> tuple[np.ndarray, np.ndarray]:
    """メッシュのファイル（STL、OBJ、OFF、PLY など）を読み、(頂点 [V, 3], 面 [F, 3]) を返す。

    いちばん長い辺が height になるよう拡大縮小し、外接する箱の中心を原点に置く。
    閉じていないメッシュは ValueError にする。
    """
    mesh = trimesh.load_mesh(path, process=True)
    if not isinstance(mesh, trimesh.Trimesh) or not mesh.is_watertight:
        raise ValueError(f"閉じた1つのメッシュだけを扱える: {path}")
    extent = float(mesh.extents.max())
    if extent <= 0:
        raise ValueError(f"大きさが 0 のメッシュ: {path}")
    vertices = (np.asarray(mesh.vertices, dtype=float) - mesh.bounds.mean(axis=0)) * (height / extent)
    return vertices, np.asarray(mesh.faces, dtype=np.int64)


def _disk_around(faces: np.ndarray, center: int, vertex_count: int) -> np.ndarray:
    """faces のうち、center を含み、辺でつながったひと続きの面だけを返す。

    直線距離では近いが曲面の上ではつながっていない部分（薄い形の裏側など）を除く。
    面どうしが1つの頂点だけで接する所があると局所座標を解けないので、その頂点のまわりの面も除く。
    """
    while True:
        adjacency = trimesh.graph.face_adjacency(faces)
        components = trimesh.graph.connected_components(adjacency, min_len=1, nodes=np.arange(len(faces)))
        seeds = np.flatnonzero((faces == center).any(axis=1))
        if len(seeds) == 0:
            raise ValueError(f"中心の頂点 {center} のまわりに面がない")
        faces = faces[np.sort(next(c for c in components if seeds[0] in c))]
        # 縁の辺（1つの面にしか属さない辺）が3本以上集まる頂点は、面が1点だけで接している所
        edges = np.sort(np.vstack([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1)
        unique, counts = np.unique(edges, axis=0, return_counts=True)
        rim = np.bincount(unique[counts == 1].ravel(), minlength=vertex_count)
        pinched = rim > 2
        if not pinched.any():
            return faces
        if pinched[center]:
            raise ValueError(f"中心の頂点 {center} で面が1点だけで接している")
        faces = faces[~pinched[faces].any(axis=1)]


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
    faces = _disk_around(faces, center, len(surface.vertices))
    solved = np.unique(faces)
    renumber = np.full(len(surface.vertices), -1, dtype=np.int64)
    renumber[solved] = np.arange(len(solved))
    patch_faces = renumber[faces]
    solver = pp3d.MeshVectorHeatSolver(surface.vertices[solved], patch_faces)
    uv = np.asarray(solver.compute_log_map(int(renumber[center])))
    inner = reach[solved] < radius
    return solved[inner], uv[inner]
