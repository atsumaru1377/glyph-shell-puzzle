"""配置のプレビューを PNG に描く。6方向から見た図を並べる。"""

import struct
import zlib
from pathlib import Path

import numpy as np

from glyphshell.surface import Surface

GLYPH = np.array([40, 40, 46], dtype=float)
BRIDGE = np.array([240, 140, 40], dtype=float)
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


def region_fields(fields: np.ndarray, reach: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """頂点ごとに、(いちばん近い字の番号, 字の内側なら負になる値, 橋の中なら負になる値) を返す。

    fields は [字, 頂点] の符号付き距離。橋は、2つの字の両方から reach / 2 より近い所。
    """
    order = np.argsort(fields, axis=0)[:2]
    first = np.take_along_axis(fields, order[:1], axis=0)[0]
    second = np.take_along_axis(fields, order[1:2], axis=0)[0] if len(fields) > 1 else np.full_like(first, np.inf)
    return order[0], first, second - reach / 2


def render(surface: Surface, glyph: np.ndarray, bridge: np.ndarray, pixels_per_unit: float) -> np.ndarray:
    """6方向の正射影を 3×2 に並べた画像を返す。glyph と bridge は頂点ごとの値（負が内側）。"""
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
    glyph_s = np.einsum("sk,fk->fs", weights, glyph[surface.faces]).ravel()
    bridge_s = np.einsum("sk,fk->fs", weights, np.minimum(bridge[surface.faces], 1e6)).ravel()
    color = np.where(
        (glyph_s < 0)[:, None], GLYPH, np.where((bridge_s < 0)[:, None], BRIDGE, EMPTY)
    )
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
