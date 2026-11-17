import numpy as np
import pytest

import trimesh

from glyphshell.surface import icosphere, load_surface, local_map

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


def test_局所座標は返す範囲の端まで正確(sphere):
    index, uv = local_map(sphere, center=0, radius=40.0)
    p = sphere.vertices[index] / RADIUS
    geodesic = np.arccos(np.clip(p @ p[index == 0][0], -1, 1)) * RADIUS
    assert np.abs(np.linalg.norm(uv, axis=1) - geodesic).max() < 0.2


# test list 7 の入口: 球でないメッシュを読める
@pytest.fixture(scope="module")
def ellipsoid(tmp_path_factory):
    path = tmp_path_factory.mktemp("mesh") / "ellipsoid.stl"
    ball = trimesh.creation.icosphere(subdivisions=3)
    trimesh.Trimesh(vertices=ball.vertices * [0.5, 0.7, 1.0], faces=ball.faces).export(path)
    return path


def test_ファイルのメッシュを決めた大きさと細かさで読む(ellipsoid):
    surface = load_surface(ellipsoid, height=80.0, edge_length=3.0)
    extents = surface.vertices.max(axis=0) - surface.vertices.min(axis=0)
    assert extents.max() == pytest.approx(80.0, rel=0.01)
    edges = surface.vertices[surface.faces] - surface.vertices[np.roll(surface.faces, 1, axis=1)]
    assert np.linalg.norm(edges, axis=2).max() <= 3.0
    # 法線は外向き（楕円体は凸なので、中心から見た向きと同じ側）
    assert ((surface.normals * surface.vertices).sum(axis=1) > 0).all()


def test_読んだメッシュでも局所座標を作れる(ellipsoid):
    surface = load_surface(ellipsoid, height=80.0, edge_length=3.0)
    index, uv = local_map(surface, center=0, radius=15.0)
    distance = np.linalg.norm(surface.vertices[index] - surface.vertices[0], axis=1)
    # 曲面に沿った距離は直線距離以上で、この大きさでは 1 mm も違わない
    difference = np.linalg.norm(uv, axis=1) - distance
    assert difference.min() > -0.5  # 辺の長さ 3 mm の粗いメッシュなので、誤差は辺の1〜2割
    assert difference.max() < 1.0


def test_閉じていないメッシュは例外(tmp_path):
    path = tmp_path / "open.stl"
    sphere = trimesh.creation.icosphere(subdivisions=2)
    trimesh.Trimesh(vertices=sphere.vertices, faces=sphere.faces[:-10]).export(path)
    with pytest.raises(ValueError):
        load_surface(path, height=80.0, edge_length=3.0)
