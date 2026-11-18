import manifold3d
import numpy as np
import pytest
import trimesh
from scipy.spatial import cKDTree

from glyphshell.skin import inner_skin, unreached_volume
from glyphshell.solids import clip_region, thicken
from glyphshell.surface import local_map

RADIUS = 40.0
THICKNESS = 8.5
EDGE = 2.0
# 耳の代わりの細い板。厚さ 6 mm は殻の厚さより薄く、球の上へ 45 mm 突き出す
PLATE_TOP = RADIUS + 45.0


def _arrays(solid):
    mesh = solid.to_mesh()
    return np.asarray(mesh.vert_properties[:, :3], dtype=float), np.asarray(mesh.tri_verts, dtype=np.int64)


@pytest.fixture(scope="module")
def eared():
    """球に細い板を1枚立てた形から作った内側の面。"""
    ball = manifold3d.Manifold.sphere(RADIUS, 96)
    plate = manifold3d.Manifold.cube([24.0, 6.0, PLATE_TOP - 30.0], center=True).translate(
        [0.0, 0.0, (PLATE_TOP + 30.0) / 2]
    )
    return inner_skin(*_arrays(ball + plate), THICKNESS, EDGE)


@pytest.fixture(scope="module")
def peanut():
    """2つの球を重ねた、くびれのある形から作った内側の面。"""
    left = manifold3d.Manifold.sphere(RADIUS, 96).translate([-30.0, 0.0, 0.0])
    right = manifold3d.Manifold.sphere(RADIUS, 96).translate([30.0, 0.0, 0.0])
    return inner_skin(*_arrays(left + right), THICKNESS, EDGE)


@pytest.fixture(scope="module")
def stubbed():
    """球に太くて短い円柱を立てた形から作った内側の面。円柱は太いので切り離されない。"""
    ball = manifold3d.Manifold.sphere(RADIUS, 96)
    stub = manifold3d.Manifold.cylinder(RADIUS + 30.0, 20.0, circular_segments=64)
    return inner_skin(*_arrays(ball + stub), THICKNESS, EDGE)


def _distance_to_outer(skin, points):
    vertices, faces = _arrays(skin.outer)
    dense, _ = trimesh.remesh.subdivide_to_size(vertices, faces, max_edge=0.5)
    return cKDTree(dense).query(points)[0]


def test_内側の面から元の表面まで殻の厚さ以上ある(eared):
    assert _distance_to_outer(eared, eared.surface.vertices).min() >= THICKNESS - 0.05


def test_内側の面は閉じた1つの塊で細い板を写さない(eared):
    surface = eared.surface
    solid = manifold3d.Manifold(
        manifold3d.Mesh(
            vert_properties=np.ascontiguousarray(surface.vertices, dtype=np.float32),
            tri_verts=np.ascontiguousarray(surface.faces, dtype=np.uint32),
        )
    )
    assert solid.status().name == "NoError"
    assert len(solid.decompose()) == 1
    assert solid.volume() > 0
    # 板は球の外（半径 40 mm より外）にある。内側の面はそこまで出ない
    assert np.linalg.norm(surface.vertices, axis=1).max() < RADIUS - THICKNESS + 1.0
    edges = surface.vertices[surface.faces] - surface.vertices[np.roll(surface.faces, 1, axis=1)]
    assert np.linalg.norm(edges, axis=2).max() <= EDGE * 1.05  # 等値面へ寄せるぶん、わずかに伸びる


def test_内側の面の法線は外を向く(eared):
    surface = eared.surface
    assert ((surface.normals * surface.vertices).sum(axis=1) > 0).all()
    assert np.linalg.norm(surface.normals, axis=1) == pytest.approx(1.0)


def test_内側の面で局所座標を作れる(peanut):
    surface = peanut.surface
    index, uv = local_map(surface, center=0, radius=15.0)
    distance = np.linalg.norm(surface.vertices[index] - surface.vertices[0], axis=1)
    # 曲面に沿った距離は直線距離以上で、この大きさでは 1 mm も違わない
    difference = np.linalg.norm(uv, axis=1) - distance
    assert difference.min() > -0.3
    assert difference.max() < 1.0


def test_くびれのある形でも押し出した面は裏返らない(peanut):
    surface = peanut.surface
    assert (peanut.reach > 0).all()
    top = surface.vertices + peanut.reach[:, None] * surface.normals

    def face_normals(points):
        tri = points[surface.faces]
        return np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])

    assert ((face_normals(top) * face_normals(surface.vertices)).sum(axis=1) > 0).all()


@pytest.mark.parametrize("shape", ["eared", "peanut", "stubbed"])
def test_押し出した先でもいちばん近い内側の面の点は押し出し元(shape, request):
    # 押し出しすぎると、面の別の所から押し出した柱の中へ入り、ピースどうしが重なる
    skin = request.getfixturevalue(shape)
    surface = skin.surface
    top = surface.vertices + skin.reach[:, None] * surface.normals
    distance, nearest = cKDTree(surface.vertices).query(top)
    # 隣の頂点がわずかに近くなるのは別の所ではない。押し出し元から、押し出した長さの4分の1より
    # 離れた頂点のほうが近くなっていないことを確かめる
    apart = np.linalg.norm(surface.vertices[nearest] - surface.vertices, axis=1)
    assert ((distance >= skin.reach - 0.05) | (apart <= np.maximum(4.2, 0.25 * skin.reach))).all()


def test_とがった縁の角まで柱が届く():
    # 立方体の角は、内側の面から斜めに遠い。そこまで押し出さないと角が欠ける
    box = manifold3d.Manifold.cube([70.0, 70.0, 70.0], center=True)
    skin = inner_skin(*_arrays(box), THICKNESS, EDGE)
    assert 0 <= unreached_volume(skin) < 0.001 * box.volume()


def test_ピースの内側は内側の面で外側は元の形の表面になる(eared):
    surface = eared.surface
    # 板と反対側（下）の、曲面に沿った半径 12 mm の円
    inner_radius = float(np.linalg.norm(surface.vertices, axis=1).mean())
    geodesic = np.arccos(np.clip(-surface.vertices[:, 2] / np.linalg.norm(surface.vertices, axis=1), -1, 1))
    region = clip_region(surface, geodesic * inner_radius - 12.0, eared.reach)
    column = thicken(region, 0.0)
    assert column.status().name == "NoError"
    piece = column ^ eared.outer
    # 柱は元の表面より外まで届いていて、切り取ると球の殻の一部（円錐台）になる
    assert column.volume() > piece.volume()
    cap = 2 * np.pi * (1 - np.cos(12.0 / inner_radius)) / 3
    assert piece.volume() == pytest.approx(cap * (RADIUS**3 - inner_radius**3), rel=0.04)
    points = np.asarray(piece.to_mesh().vert_properties[:, :3], dtype=float)
    assert np.linalg.norm(points, axis=1).max() == pytest.approx(RADIUS, abs=0.1)
    assert np.linalg.norm(points, axis=1).min() == pytest.approx(inner_radius, abs=0.3)


def test_細い板は切り離されて追加のパーツになる(eared):
    assert len(eared.parts) == 1
    low, high = np.array(eared.parts[0].bounding_box()).reshape(2, 3)
    assert high[2] == pytest.approx(PLATE_TOP, abs=0.01)
    # 切り口は板の根元（球の表面のあたり）にある
    assert RADIUS - 2 * THICKNESS < low[2] < RADIUS + THICKNESS
    # 板の体積（球の外に出ている分）は、全部が追加のパーツに入る
    assert eared.parts[0].volume() >= 24.0 * 6.0 * (PLATE_TOP - RADIUS) * 0.98
    # 残りの形に板の先は残らない
    assert np.array(eared.outer.bounding_box()).reshape(2, 3)[1, 2] < RADIUS + THICKNESS


def test_切り離した残りの形には柱が届かない所がほとんど残らない(eared):
    assert 0 <= unreached_volume(eared) < 0.001 * eared.outer.volume()


def test_小さなとげは細い部分にしない():
    # 高さ 6 mm のとげは細長いが、内側の面が入れない太さ（半径 約 15 mm）に比べて短い
    ball = manifold3d.Manifold.sphere(RADIUS, 96)
    spike = manifold3d.Manifold.cylinder(6.5, 2.0, 0.2, circular_segments=24).translate([0.0, 0.0, RADIUS - 0.5])
    assert inner_skin(*_arrays(ball + spike), THICKNESS, EDGE).parts == []


def test_とがった縁のある形から細い部分は出ない():
    box = manifold3d.Manifold.cube([70.0, 70.0, 70.0], center=True)
    skin = inner_skin(*_arrays(box), THICKNESS, EDGE)
    assert skin.parts == []


def test_殻の厚さより細い形は例外():
    thin = manifold3d.Manifold.cube([60.0, 60.0, 10.0], center=True)
    with pytest.raises(ValueError):
        inner_skin(*_arrays(thin), THICKNESS, EDGE)


def test_内側の面が入れない太さの細長い板も切り離す():
    # 厚さ 20 mm の板は殻の厚さの2倍（17 mm）より厚いが、ならした面は中に入らない。
    # 残すと、板の全体が根元のピースから柱として生えてしまう
    top = RADIUS + 90.0
    ball = manifold3d.Manifold.sphere(RADIUS, 96)
    plate = manifold3d.Manifold.cube([30.0, 20.0, top - 30.0], center=True).translate([0.0, 0.0, (top + 30.0) / 2])
    skin = inner_skin(*_arrays(ball + plate), THICKNESS, EDGE)
    assert len(skin.parts) == 1
    assert np.array(skin.parts[0].bounding_box()).reshape(2, 3)[1, 2] == pytest.approx(top, abs=0.01)
    assert np.array(skin.outer.bounding_box()).reshape(2, 3)[1, 2] < RADIUS + 2 * THICKNESS


def test_太くて短い出っ張りは切り離さず柱が先まで届く(stubbed):
    assert stubbed.parts == []
    assert 0 <= unreached_volume(stubbed) < 0.001 * stubbed.outer.volume()
