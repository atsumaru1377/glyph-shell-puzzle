import numpy as np
import pytest

import trimesh

from glyphshell.surface import Surface, icosphere, load_mesh, local_map

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


def test_ファイルのメッシュを決めた大きさで読む(ellipsoid):
    vertices, faces = load_mesh(ellipsoid, height=80.0)
    extents = vertices.max(axis=0) - vertices.min(axis=0)
    assert extents.max() == pytest.approx(80.0, rel=0.01)
    # 中心は原点に置く
    assert (vertices.max(axis=0) + vertices.min(axis=0)) / 2 == pytest.approx(np.zeros(3), abs=1e-6)


def test_閉じていないメッシュは例外(tmp_path):
    path = tmp_path / "open.stl"
    sphere = trimesh.creation.icosphere(subdivisions=2)
    trimesh.Trimesh(vertices=sphere.vertices, faces=sphere.faces[:-10]).export(path)
    with pytest.raises(ValueError):
        load_mesh(path, height=80.0)


def _grid(size, removed):
    """size×size のマスの平らな板。removed のマス (列, 行) は面を作らない。"""
    xs, ys = np.meshgrid(np.arange(size + 1.0), np.arange(size + 1.0))
    vertices = np.stack([xs.ravel(), ys.ravel(), np.zeros(xs.size)], axis=1)
    faces = []
    for row in range(size):
        for column in range(size):
            if (column, row) in removed:
                continue
            a = row * (size + 1) + column
            b, c, d = a + 1, a + size + 2, a + size + 1
            faces += [[a, b, c], [a, c, d]]
    normals = np.tile([0.0, 0.0, 1.0], (len(vertices), 1))
    return Surface(vertices, np.array(faces), normals)


def test_面が1点だけで接する所があっても局所座標を作れる():
    # 頂点 (3, 3) の右上と左下のマスを抜くと、残りの面はその頂点だけで接する
    plate = _grid(6, removed={(3, 3), (2, 2)})
    center = 1 * 7 + 1  # 頂点 (1, 1)
    index, uv = local_map(plate, center, radius=10.0)
    assert center in index
    assert np.isfinite(uv).all()
    # 板が粗い（マス1つが辺1本）ので、辺でつながった隣の頂点だけで距離を確かめる
    distance = np.linalg.norm(plate.vertices[index] - plate.vertices[center], axis=1)
    beside = np.isclose(distance, 1.0)
    assert np.linalg.norm(uv[beside], axis=1) == pytest.approx(1.0, abs=0.1)
    # 1点だけで接していた頂点は、解ける範囲から外れる
    assert 3 * 7 + 3 not in index
