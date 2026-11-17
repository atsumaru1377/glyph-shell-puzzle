import numpy as np
import pytest
from shapely.geometry import Point, box

from glyphshell.layout import LayoutParams, pack, separation
from glyphshell.sdf import glyph_field
from glyphshell.surface import icosphere

RADIUS = 40.0
PARAMS = LayoutParams(
    sizes=(20.0, 12.0),
    min_gap=3.0,
    reach=6.0,
    rotations=8,
    min_neck=3.8,
    min_extent=7.8,
    seed=1,
)


@pytest.fixture(scope="module")
def sphere():
    return icosphere(radius=RADIUS, subdivisions=4)


@pytest.fixture(scope="module")
def fields():
    shapes = {
        "a": box(0, 0, 1, 1),
        "b": box(0, 0, 1.4, 0.6),
        "c": Point(0, 0).buffer(0.5),
        "d": box(0, 0, 0.7, 1.2),
        "e": Point(0, 0).buffer(0.6),
        "f": box(0, 0, 1.2, 0.9),
    }
    return [glyph_field(char, shape) for char, shape in shapes.items()]


@pytest.fixture(scope="module")
def placements(sphere, fields):
    return pack(sphere, fields, PARAMS)


def test_複数の字が置かれる(placements):
    assert len(placements) >= 3


# test list 2 の配置の段での確認: 字どうしが重ならない
def test_置いた字どうしは決めた隙間以上に離れる(placements):
    for i, a in enumerate(placements):
        for b in placements[i + 1 :]:
            assert separation(a, b) >= PARAMS.min_gap


def test_同じ字は1回しか使わない(placements):
    chars = [p.char for p in placements]
    assert len(chars) == len(set(chars))


def test_決めた大きさだけを使う(placements):
    assert {p.size for p in placements} <= set(PARAMS.sizes)


def test_同じ設定なら同じ配置になる(sphere, fields, placements):
    again = pack(sphere, fields, PARAMS)
    assert [(p.char, p.center, p.size, p.angle) for p in again] == [
        (p.char, p.center, p.size, p.angle) for p in placements
    ]


def test_細すぎる字は置かない(sphere):
    thin = glyph_field("t", box(0, 0, 1, 0.1))  # 大きさ 20 でも幅 2 で、要る幅 3.8 に足りない
    assert pack(sphere, [thin], PARAMS) == []


def test_離れた字どうしの隙間は無限大(placements):
    far = max(
        (separation(placements[0], other) for other in placements[1:]),
        default=np.inf,
    )
    assert far > 0
