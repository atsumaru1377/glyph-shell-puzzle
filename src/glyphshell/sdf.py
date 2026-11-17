"""字の形を、符号付き距離の格子（内側が負）として持つ。

曲面の上で字どうしの重なりや隙間を調べるときに、多数の点の距離を速く求めるために使う。
"""

from dataclasses import dataclass

import numpy as np
import shapely
import shapely.affinity
from shapely.geometry.base import BaseGeometry

from glyphshell.glyphs import neck_width

# 格子の目の大きさ（キャップハイトを 1 とする単位）。
# 字の高さ 50 mm のとき 0.5 mm で、ノズル径 0.4 mm と同じ程度の細かさになる。
CELL = 0.01
# 形の外接する箱の外側に取る格子の余白。字どうしの隙間と橋渡しの幅を調べる範囲で、
# 字の高さ 15 mm のとき 7.5 mm に当たる。
MARGIN = 0.5
# いちばん細い所の幅を測る刻み。測った幅は、この2倍（字の高さ 50 mm のとき 0.25 mm）の刻みになる。
NECK_STEP = CELL / 4


@dataclass(frozen=True)
class GlyphField:
    """1字ぶんの符号付き距離の格子。原点は形の外接する箱の中心。"""

    char: str
    lower_left: tuple[float, float]
    values: np.ndarray  # [行(y), 列(x)]。内側が負
    area: float
    radius: float  # 原点から形のいちばん遠い点までの距離
    neck: float  # いちばん細い所の幅
    min_extent: float  # 外接する箱の短い辺


def glyph_field(char: str, shape: BaseGeometry) -> GlyphField:
    minx, miny, maxx, maxy = shape.bounds
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    centered = shapely.affinity.translate(shape, -cx, -cy)
    half_w, half_h = (maxx - minx) / 2 + MARGIN, (maxy - miny) / 2 + MARGIN
    xs = np.arange(-half_w, half_w + CELL, CELL)
    ys = np.arange(-half_h, half_h + CELL, CELL)
    gx, gy = np.meshgrid(xs, ys)
    points = shapely.points(gx.ravel(), gy.ravel())
    distance = shapely.distance(points, centered.boundary)
    inside = shapely.contains_xy(centered, gx.ravel(), gy.ravel())
    values = np.where(inside, -distance, distance).reshape(gy.shape)
    outline = shapely.get_coordinates(centered)
    return GlyphField(
        char=char,
        lower_left=(float(xs[0]), float(ys[0])),
        values=values,
        area=float(shape.area),
        radius=float(np.linalg.norm(outline, axis=1).max()),
        neck=neck_width(shape, NECK_STEP),
        min_extent=float(min(maxx - minx, maxy - miny)),
    )


def signed_distance(field: GlyphField, points: np.ndarray, size: float, angle: float) -> np.ndarray:
    """字を原点に置いたときの、各点から字の輪郭までの符号付き距離を返す。

    points は [..., 2]。size はキャップハイト（points と同じ長さの単位）、angle は字を回す角度。
    格子の外の点は、格子の縁の値に縁までの距離を足した値にする。真の距離より小さくはならないが、
    大きくなることがある。余白（MARGIN × size）より遠い所の値は目安として扱う。
    """
    cos, sin = np.cos(angle), np.sin(angle)
    x = (points[..., 0] * cos + points[..., 1] * sin) / size
    y = (-points[..., 0] * sin + points[..., 1] * cos) / size
    ny, nx = field.values.shape
    gx = (x - field.lower_left[0]) / CELL
    gy = (y - field.lower_left[1]) / CELL
    cx = np.clip(gx, 0, nx - 1)
    cy = np.clip(gy, 0, ny - 1)
    outside = np.hypot(gx - cx, gy - cy) * CELL
    ix = np.minimum(cx.astype(np.intp), nx - 2)
    iy = np.minimum(cy.astype(np.intp), ny - 2)
    tx, ty = cx - ix, cy - iy
    v = field.values
    inner = (
        v[iy, ix] * (1 - tx) * (1 - ty)
        + v[iy, ix + 1] * tx * (1 - ty)
        + v[iy + 1, ix] * (1 - tx) * ty
        + v[iy + 1, ix + 1] * tx * ty
    )
    return (inner + outside) * size
