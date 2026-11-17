import pytest
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from glyphshell.glyphs import glyph_shape, is_single_piece, load_font, neck_width

ARIAL_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"


@pytest.fixture(scope="module")
def font():
    return load_font(ARIAL_BLACK)


# test list 1: 使える字だけを選ぶ
def test_離れた部分のある字は不採用(font):
    assert not is_single_piece(glyph_shape(font, "i"))


def test_つながった字は採用(font):
    assert is_single_piece(glyph_shape(font, "A"))


def test_穴のある字は穴を保つ(font):
    shape = glyph_shape(font, "O")
    assert isinstance(shape, Polygon)
    assert len(shape.interiors) == 1


def test_形のない字は不採用(font):
    assert not is_single_piece(glyph_shape(font, " "))


def test_書体にない字は例外(font):
    with pytest.raises(ValueError):
        glyph_shape(font, "あ")


def test_2文字以上は例外(font):
    with pytest.raises(ValueError):
        glyph_shape(font, "AB")


def test_字はキャップハイトを1とする大きさで返る(font):
    _, miny, _, maxy = glyph_shape(font, "H").bounds
    assert miny == pytest.approx(0.0, abs=0.01)
    assert maxy == pytest.approx(1.0, abs=0.01)


# 線の細さの測り方
def test_長方形の首の幅は短い辺(font):
    assert neck_width(box(0, 0, 10, 2), step=0.05) == pytest.approx(2.0, abs=0.1)


def test_細い棒でつないだ形の首の幅は棒の幅():
    dumbbell = unary_union([box(0, 0, 4, 4), box(4, 1.75, 8, 2.25), box(8, 0, 13, 5)])
    assert neck_width(dumbbell, step=0.05) == pytest.approx(0.5, abs=0.1)


def test_離れた形の首の幅は0():
    assert neck_width(unary_union([box(0, 0, 1, 1), box(2, 0, 3, 1)]), step=0.05) == 0.0
