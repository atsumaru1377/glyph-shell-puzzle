"""書体から字の形を取り出し、ピースに使えるかを調べる。

字の形は、キャップハイト（大文字の高さ）を 1 とする大きさの shapely の図形で扱う。
"""

from functools import reduce

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry

# 曲線1本を折れ線にするときの分割数。
# 高さ 40 mm の字で半径 10 mm の四分円を 8 分割すると、弦と弧のずれは約 0.05 mm で、
# ノズル径 0.4 mm より十分小さい。
CURVE_SEGMENTS = 8


class _ContourPen(BasePen):
    """輪郭を折れ線の点列として集めるペン。"""

    def __init__(self, glyph_set):
        super().__init__(glyph_set)
        self.contours: list[list[tuple[float, float]]] = []

    def _moveTo(self, pt):
        self.contours.append([pt])

    def _lineTo(self, pt):
        self.contours[-1].append(pt)

    def _curveToOne(self, pt1, pt2, pt3):
        p0 = self.contours[-1][-1]
        for i in range(1, CURVE_SEGMENTS + 1):
            t = i / CURVE_SEGMENTS
            a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t**2, t**3
            self.contours[-1].append(
                (
                    a * p0[0] + b * pt1[0] + c * pt2[0] + d * pt3[0],
                    a * p0[1] + b * pt1[1] + c * pt2[1] + d * pt3[1],
                )
            )

    def _qCurveToOne(self, pt1, pt2):
        p0 = self.contours[-1][-1]
        for i in range(1, CURVE_SEGMENTS + 1):
            t = i / CURVE_SEGMENTS
            a, b, c = (1 - t) ** 2, 2 * (1 - t) * t, t**2
            self.contours[-1].append(
                (a * p0[0] + b * pt1[0] + c * pt2[0], a * p0[1] + b * pt1[1] + c * pt2[1])
            )


def load_font(path: str, face_index: int = 0) -> TTFont:
    """書体のファイルを開く。.ttc のときは face_index で書体を選ぶ。"""
    return TTFont(path, fontNumber=face_index)


def _contours(font: TTFont, char: str) -> list[list[tuple[float, float]]]:
    """1文字の輪郭を、書体の単位のままの点列で返す。"""
    glyph_name = font.getBestCmap().get(ord(char))
    if glyph_name is None:
        raise ValueError(f"書体にない字: {char!r}")
    glyph_set = font.getGlyphSet()
    pen = _ContourPen(glyph_set)
    glyph_set[glyph_name].draw(pen)
    return pen.contours


def cap_height(font: TTFont) -> float:
    """キャップハイトを書体の単位で返す。「H」の輪郭の上端で測る。

    書体の OS/2 表の値は古い版の書体（Arial Black など）には無いので使わない。
    """
    return max(y for contour in _contours(font, "H") for _, y in contour)


def glyph_shape(font: TTFont, char: str) -> BaseGeometry:
    """1文字の形を返す。キャップハイトを 1 とし、ベースラインを y=0 とする。

    輪郭どうしの重なりは偶奇則で扱う（輪郭の内側にある輪郭は穴になる）。
    書体にない字、輪郭が壊れている字は ValueError にする。
    """
    if len(char) != 1:
        raise ValueError(f"1文字だけを渡す: {char!r}")
    unit = cap_height(font)

    polygons = []
    for contour in _contours(font, char):
        if len(contour) < 3:
            continue
        polygon = Polygon([(x / unit, y / unit) for x, y in contour])
        if not polygon.is_valid:
            raise ValueError(f"輪郭が自己交差している字: {char!r}")
        polygons.append(polygon)
    return reduce(lambda a, b: a.symmetric_difference(b), polygons, MultiPolygon())


def is_single_piece(shape: BaseGeometry) -> bool:
    """形が、1つにつながった空でない図形かどうか。"""
    return isinstance(shape, Polygon) and not shape.is_empty


def neck_width(shape: BaseGeometry, step: float) -> float:
    """形のいちばん細い所の幅を、step の2倍の刻みで返す。

    形を step ずつ内側へ縮めていき、1つのまとまりでなくなった（切れた、または消えた）
    ときの縮め量の2倍を返す。最初から1つにつながっていない形は 0 を返す。
    """
    if step <= 0:
        raise ValueError(f"step は正の数にする: {step}")
    if not is_single_piece(shape):
        return 0.0
    k = 1
    while is_single_piece(shape.buffer(-k * step)):
        k += 1
    return 2 * k * step
