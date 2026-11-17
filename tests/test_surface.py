import numpy as np
import pytest

from glyphshell.surface import icosphere, local_map

RADIUS = 75.0


@pytest.fixture(scope="module")
def sphere():
    return icosphere(radius=RADIUS, subdivisions=5)


def test_球の頂点は半径の上にある(sphere):
    assert np.linalg.norm(sphere.vertices, axis=1) == pytest.approx(RADIUS)


def test_局所座標の原点は中心の頂点(sphere):
    index, uv = local_map(sphere, center=0, radius=40.0)
    assert uv[index == 0][0] == pytest.approx([0.0, 0.0], abs=1e-6)


def test_局所座標の距離は球面上の距離に合う(sphere):
    index, uv = local_map(sphere, center=0, radius=40.0)
    p = sphere.vertices[index] / RADIUS
    geodesic = np.arccos(np.clip(p @ p[index == 0][0], -1, 1)) * RADIUS
    inner = geodesic < 30.0
    assert np.abs(np.linalg.norm(uv, axis=1) - geodesic)[inner].max() < 0.2


def test_局所座標は中心から半径の内側だけを返す(sphere):
    index, _ = local_map(sphere, center=0, radius=40.0)
    distance = np.linalg.norm(sphere.vertices[index] - sphere.vertices[0], axis=1)
    assert distance.max() < 40.0
    assert len(index) < len(sphere.vertices) / 4


def test_半径が小さすぎて面が取れないときは例外(sphere):
    with pytest.raises(ValueError):
        local_map(sphere, center=0, radius=0.01)
