import numpy as np
import pytest
from shapely.geometry import box

from glyphshell.sdf import glyph_field, signed_distance


@pytest.fixture(scope="module")
def square():
    # 一辺 1 の正方形。場の原点は外接する箱の中心に来る
    return glyph_field("□", box(3.0, 5.0, 4.0, 6.0))


def test_中心は内側で距離は辺までの半分(square):
    d = signed_distance(square, np.array([[0.0, 0.0]]), size=1.0, angle=0.0)
    assert d[0] == pytest.approx(-0.5, abs=0.02)


def test_外側の点は辺までの距離(square):
    d = signed_distance(square, np.array([[0.8, 0.0]]), size=1.0, angle=0.0)
    assert d[0] == pytest.approx(0.3, abs=0.02)


def test_大きさを変えると距離も同じ比で変わる(square):
    d = signed_distance(square, np.array([[40.0, 0.0]]), size=40.0, angle=0.0)
    assert d[0] == pytest.approx(20.0, abs=0.8)


def test_回すと形も回る():
    wide = glyph_field("▭", box(0.0, 0.0, 4.0, 1.0))
    point = np.array([[0.0, 1.5]])
    assert signed_distance(wide, point, size=1.0, angle=0.0)[0] == pytest.approx(1.0, abs=0.03)
    # 90度回すと長い辺が縦になり、同じ点は内側に入る
    assert signed_distance(wide, point, size=1.0, angle=np.pi / 2)[0] < 0


def test_格子の外の点でも距離を小さく見積もらない(square):
    d = signed_distance(square, np.array([[10.0, 0.0]]), size=1.0, angle=0.0)
    assert d[0] >= 9.5 - 0.02


def test_面積と外接円の半径を持つ(square):
    assert square.area == pytest.approx(1.0)
    assert square.radius == pytest.approx(np.sqrt(0.5))


def test_いちばん細い所の幅と箱の短い辺を持つ():
    wide = glyph_field("▭", box(0.0, 0.0, 4.0, 1.0))
    assert wide.neck == pytest.approx(1.0, abs=0.02)
    assert wide.min_extent == pytest.approx(1.0)
