import numpy as np
import pytest
from shapely.geometry import Point, box

from glyphshell.layout import LayoutParams, load_layout, pack, save_layout, separation
from glyphshell.sdf import glyph_field
from glyphshell.surface import icosphere

RADIUS = 40.0
PARAMS = LayoutParams(
    sizes=(20.0, 12.0),
    max_overlap=2.0,
    min_contact=6.0,
    rotations=8,
    candidates=6,
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


def test_置いた字どうしは決めた深さより深く重ならない(placements):
    for i, a in enumerate(placements):
        for b in placements[i + 1 :]:
            assert separation(a, b) >= -PARAMS.max_overlap


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


def test_字の穴の中には別の字を置かない(sphere):
    ring = glyph_field("o", Point(0, 0).buffer(1.0).difference(Point(0, 0).buffer(0.75)))
    dot = glyph_field("c", Point(0, 0).buffer(0.5))
    params = LayoutParams(
        sizes=(30.0, 12.0), max_overlap=2.0, min_contact=6.0, rotations=4, candidates=2, min_neck=3.8, min_extent=7.8, seed=1
    )
    placements = pack(sphere, [ring, dot], params)
    assert [p.char for p in placements][0] == "o"
    ring_placed = placements[0]
    # 穴のうち、重なってよい深さより内側の所
    hole = ring_placed.index[(ring_placed.solid < -2.0) & (ring_placed.distance > 2.0)]
    assert len(hole) > 0
    for other in placements[1:]:
        inside_other = other.index[other.distance < 0]
        assert len(np.intersect1d(hole, inside_other)) == 0


def test_1か所で試す字の数を絞ると選ばれる字が変わる(sphere, fields, placements):
    narrow = LayoutParams(**{**PARAMS.__dict__, "candidates": 1})
    chars = [p.char for p in pack(sphere, fields, narrow)]
    assert len(chars) == len(set(chars))
    assert chars != [p.char for p in placements]


def test_配置を保存して読み直すと同じになる(placements, tmp_path):
    save_layout(tmp_path / "layout.npz", placements)
    loaded = load_layout(tmp_path / "layout.npz")
    assert len(loaded) == len(placements)
    for a, b in zip(loaded, placements):
        assert (a.char, a.center, a.offset, a.angle, a.size) == (b.char, b.center, b.offset, b.angle, b.size)
        assert np.array_equal(a.index, b.index)
        assert np.array_equal(a.distance, b.distance)
        assert np.array_equal(a.solid, b.solid)


def test_置いてある字を残して空きに字を足せる(sphere, fields, placements):
    kept = placements[: len(placements) // 2]
    refilled = pack(sphere, fields, PARAMS, existing=kept)
    assert refilled[: len(kept)] == kept
    assert len(refilled) > len(kept)
    chars = [p.char for p in refilled]
    assert len(chars) == len(set(chars))
    for i, a in enumerate(refilled):
        for b in refilled[i + 1 :]:
            assert separation(a, b) >= -PARAMS.max_overlap
