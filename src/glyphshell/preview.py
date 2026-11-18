"""配置のプレビューを PNG に描く。6方向から見た図を並べる。"""

import struct
import zlib
from pathlib import Path

import numpy as np
import trimesh

from glyphshell.surface import Surface

# ピースの色。隣どうしを見分けられるよう、番号の順に使い回す
PALETTE = np.array(
    [[38, 70, 83], [42, 157, 143], [92, 107, 192], [231, 111, 81], [69, 123, 157], [141, 110, 99], [84, 110, 122]],
    dtype=float,
)
MARK = np.array([255, 214, 10], dtype=float)
EMPTY = np.array([225, 228, 232], dtype=float)
BACKGROUND = 255
# 1つの三角形の中に取る点の細かさ。辺を SUBDIVISION 等分した格子点を描く。
# 辺の長さ 1.4 mm、1 mm あたり 3 画素のとき、点の間隔は約 0.7 画素になり、すき間なく塗れる。
SUBDIVISION = 6
VIEWS = [
    ("+X", (1, 0, 0), (0, 0, 1)),
    ("-X", (-1, 0, 0), (0, 0, 1)),
    ("+Y", (0, 1, 0), (0, 0, 1)),
    ("-Y", (0, -1, 0), (0, 0, 1)),
    ("+Z", (0, 0, 1), (0, 1, 0)),
    ("-Z", (0, 0, -1), (0, 1, 0)),
]


def write_png(path: Path, image: np.ndarray) -> None:
    """[高さ, 幅, 3] の uint8 の画像を PNG に書く。"""
    height, width, _ = image.shape
    rows = np.concatenate([np.zeros((height, 1), dtype=np.uint8), image.reshape(height, -1)], axis=1)

    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(rows.tobytes(), 6))
        + chunk(b"IEND", b"")
    )


def render(
    surface: Surface, pieces: np.ndarray, mark: np.ndarray, pixels_per_unit: float
) -> np.ndarray:
    """6方向の正射影を 3×2 に並べた画像を返す。

    pieces は [ピース, 頂点] の値で、負の所をそのピースの色で塗る。mark は頂点ごとの値で、
    負の所をその上から印の色で塗る。
    """
    glyph = pieces.min(axis=0)
    owner = pieces.argmin(axis=0)
    extent = float(np.abs(surface.vertices).max()) * 1.05
    side = int(np.ceil(2 * extent * pixels_per_unit))
    weights = np.array(
        [
            (i, j, SUBDIVISION - i - j)
            for i in range(SUBDIVISION + 1)
            for j in range(SUBDIVISION + 1 - i)
        ],
        dtype=float,
    ) / SUBDIVISION
    tri = surface.vertices[surface.faces]
    points = np.einsum("sk,fkd->fsd", weights, tri).reshape(-1, 3)
    normals = np.einsum("sk,fkd->fsd", weights, surface.normals[surface.faces]).reshape(-1, 3)
    glyph_s = np.einsum("sk,fk->fs", weights, np.minimum(glyph[surface.faces], 1e6)).ravel()
    mark_s = np.einsum("sk,fk->fs", weights, np.minimum(mark[surface.faces], 1e6)).ravel()
    # 三角形の中の点は、いちばん近い頂点のピースの色にする
    nearest_corner = surface.faces[:, weights.argmax(axis=1)]
    piece_color = PALETTE[owner[nearest_corner].ravel() % len(PALETTE)]
    color = np.where((mark_s < 0)[:, None], MARK, np.where((glyph_s < 0)[:, None], piece_color, EMPTY))
    image = np.full((2 * side, 3 * side, 3), BACKGROUND, dtype=np.uint8)
    for k, (_, toward, up) in enumerate(VIEWS):
        toward, up = np.array(toward, dtype=float), np.array(up, dtype=float)
        right = np.cross(up, toward)
        facing = normals @ toward
        visible = facing > 0
        x = ((points[visible] @ right + extent) * pixels_per_unit).astype(int)
        y = ((extent - points[visible] @ up) * pixels_per_unit).astype(int)
        depth = points[visible] @ toward
        shade = 0.55 + 0.45 * facing[visible]
        shaded = np.clip(color[visible] * shade[:, None] + 40 * (1 - shade[:, None]), 0, 255)
        inside = (x >= 0) & (x < side) & (y >= 0) & (y < side)
        # 奥の点から順に書くと、手前の点が最後に残る
        back_to_front = np.argsort(depth[inside])
        view = np.full((side, side, 3), BACKGROUND, dtype=np.uint8)
        view[y[inside][back_to_front], x[inside][back_to_front]] = shaded[inside][back_to_front]
        row, column = divmod(k, 3)
        image[row * side : (row + 1) * side, column * side : (column + 1) * side] = view
    return image


def render_solids(pieces: list[trimesh.Trimesh], extras: list[trimesh.Trimesh], pixels_per_unit: float) -> np.ndarray:
    """ピースの立体を、ピースごとの色で 6 方向から描く。extras（字でないパーツ）は色を付けずに描く。"""
    # 立体の三角形は大きさがまちまちなので、点を取る前に、曲面と同じ細かさ（1 画素より細かい間隔）まで分ける
    edge = SUBDIVISION / (2 * pixels_per_unit)
    vertices, faces, normals, owner = [], [], [], []
    offset = 0
    for k, mesh in enumerate([*pieces, *extras]):
        fine_vertices, fine_faces = trimesh.remesh.subdivide_to_size(mesh.vertices, mesh.faces, max_edge=edge)
        fine = trimesh.Trimesh(vertices=fine_vertices, faces=fine_faces, process=False)
        vertices.append(fine_vertices)
        faces.append(fine_faces + offset)
        normals.append(fine.vertex_normals)
        owner.append(np.full(len(fine_vertices), k if k < len(pieces) else -1))
        offset += len(fine_vertices)
    owner = np.concatenate(owner)
    values = np.where(owner[None, :] == np.arange(len(pieces))[:, None], -1.0, 1.0)
    surface = Surface(np.vstack(vertices), np.vstack(faces), np.vstack(normals))
    return render(surface, values, np.full(len(owner), np.inf), pixels_per_unit)
