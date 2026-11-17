import numpy as np
import pytest

from glyphshell.solids import Pocket, clip_region, piece_solid, thicken
from glyphshell.surface import icosphere

RADIUS = 40.0
THICKNESS = 8.0


@pytest.fixture(scope="module")
def sphere():
    return icosphere(radius=RADIUS, subdivisions=5)


def _cap_field(sphere, axis, angle_radius):
    """axis のまわりの、曲面上の半径 angle_radius の円の内側で負になる値。"""
    geodesic = np.arccos(np.clip(sphere.vertices @ np.asarray(axis, dtype=float) / RADIUS, -1, 1)) * RADIUS
    return geodesic - angle_radius


def test_切り出した領域の面積は円の面積に合う(sphere):
    region = clip_region(sphere, _cap_field(sphere, (0, 0, 1), 15.0))
    tri = region.vertices[region.faces]
    area = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1).sum() / 2
    exact = 2 * np.pi * RADIUS**2 * (1 - np.cos(15.0 / RADIUS))
    assert area == pytest.approx(exact, rel=0.02)


def test_切り出した領域の縁は値が0の線の上にある(sphere):
    region = clip_region(sphere, _cap_field(sphere, (0, 0, 1), 15.0))
    geodesic = np.arccos(np.clip(region.vertices[:, 2] / np.linalg.norm(region.vertices, axis=1), -1, 1)) * RADIUS
    assert geodesic.max() == pytest.approx(15.0, abs=0.1)


def test_内側の頂点がなければ例外(sphere):
    with pytest.raises(ValueError):
        clip_region(sphere, np.ones(len(sphere.vertices)))


def test_離れた小さい島は捨てていちばん大きい塊だけを残す(sphere):
    field = np.minimum(_cap_field(sphere, (0, 0, 1), 15.0), _cap_field(sphere, (0, 0, -1), 4.0))
    region = clip_region(sphere, field)
    assert region.vertices[:, 2].min() > 0
    assert region.dropped_area == pytest.approx(np.pi * 4.0**2, rel=0.2)


def test_厚みを付けた形は閉じていて体積が合う(sphere):
    solid = thicken(clip_region(sphere, _cap_field(sphere, (0, 0, 1), 15.0)), THICKNESS)
    assert solid.status().name == "NoError"
    cap = 2 * np.pi * (1 - np.cos(15.0 / RADIUS)) / 3
    exact = cap * (RADIUS**3 - (RADIUS - THICKNESS) ** 3)
    assert solid.volume() == pytest.approx(exact, rel=0.02)


def test_穴のある領域も閉じた形になる(sphere):
    field = np.maximum(_cap_field(sphere, (0, 0, 1), 15.0), -_cap_field(sphere, (0, 0, 1), 6.0))
    solid = thicken(clip_region(sphere, field), THICKNESS)
    assert solid.status().name == "NoError"
    assert solid.genus() == 1


def test_磁石の穴を開けると円柱ぶんの体積が減る(sphere):
    region = clip_region(sphere, _cap_field(sphere, (0, 0, 1), 15.0))
    # 円の縁（x の正の側）に、中心へ向かって掘る
    edge = np.array([np.sin(15.0 / RADIUS), 0.0, np.cos(15.0 / RADIUS)])
    inward = np.array([-np.cos(15.0 / RADIUS), 0.0, np.sin(15.0 / RADIUS)])
    pocket = Pocket(point=edge * RADIUS, normal=edge, into=inward)
    plain = thicken(region, THICKNESS)
    drilled = piece_solid(region, THICKNESS, [pocket], hole_diameter=6.2, hole_depth=3.0)
    removed = plain.volume() - drilled.volume()
    assert removed == pytest.approx(np.pi * 3.1**2 * 3.0, rel=0.1)
    assert drilled.status().name == "NoError"


def test_N極を外へ向ける穴には内側の面に印の突起が付く(sphere):
    region = clip_region(sphere, _cap_field(sphere, (0, 0, 1), 15.0))
    edge = np.array([np.sin(15.0 / RADIUS), 0.0, np.cos(15.0 / RADIUS)])
    inward = np.array([-np.cos(15.0 / RADIUS), 0.0, np.sin(15.0 / RADIUS)])
    plain = piece_solid(region, THICKNESS, [Pocket(edge * RADIUS, edge, inward)], 6.2, 3.0)
    marked = piece_solid(region, THICKNESS, [Pocket(edge * RADIUS, edge, inward, north_out=True)], 6.2, 3.0)
    added = marked.volume() - plain.volume()
    assert added == pytest.approx(np.pi * 1.2**2 * 0.8, rel=0.15)
    # 突起は殻の内側の面（半径 RADIUS − THICKNESS）より中心側へ出る
    inner_most = np.linalg.norm(np.asarray(marked.to_mesh().vert_properties)[:, :3], axis=1).min()
    assert inner_most == pytest.approx(RADIUS - THICKNESS - 0.8, abs=0.1)
