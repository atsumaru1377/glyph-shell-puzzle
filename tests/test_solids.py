import manifold3d
import numpy as np
import pytest

from glyphshell.solids import Pocket, clip_region, drill, joint_site, piece_solid, thicken
from glyphshell.surface import icosphere
from glyphshell.verify import facing_points

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
    drilled = piece_solid(plain, THICKNESS, [pocket], hole_diameter=6.2, hole_depth=3.0)
    removed = plain.volume() - drilled.volume()
    assert removed == pytest.approx(np.pi * 3.1**2 * 3.0, rel=0.1)
    assert drilled.status().name == "NoError"


def test_N極を外へ向ける穴には内側の面に印の突起が付く(sphere):
    region = clip_region(sphere, _cap_field(sphere, (0, 0, 1), 15.0))
    edge = np.array([np.sin(15.0 / RADIUS), 0.0, np.cos(15.0 / RADIUS)])
    inward = np.array([-np.cos(15.0 / RADIUS), 0.0, np.sin(15.0 / RADIUS)])
    base = thicken(region, THICKNESS)
    plain = piece_solid(base, THICKNESS, [Pocket(edge * RADIUS, edge, inward)], 6.2, 3.0)
    marked = piece_solid(base, THICKNESS, [Pocket(edge * RADIUS, edge, inward, north_out=True)], 6.2, 3.0)
    added = marked.volume() - plain.volume()
    assert added == pytest.approx(np.pi * 1.2**2 * 0.8, rel=0.15)
    # 突起は殻の内側の面（半径 RADIUS − THICKNESS）より中心側へ出る
    inner_most = np.linalg.norm(np.asarray(marked.to_mesh().vert_properties)[:, :3], axis=1).min()
    assert inner_most == pytest.approx(RADIUS - THICKNESS - 0.8, abs=0.1)


def test_外へ押し出す長さを渡すと面の外側にも厚みが付く(sphere):
    reach = np.full(len(sphere.vertices), 5.0)
    region = clip_region(sphere, _cap_field(sphere, (0, 0, 1), 15.0), reach)
    solid = thicken(region, THICKNESS)
    assert solid.status().name == "NoError"
    cap = 2 * np.pi * (1 - np.cos(15.0 / RADIUS)) / 3
    exact = cap * ((RADIUS + 5.0) ** 3 - (RADIUS - THICKNESS) ** 3)
    assert solid.volume() == pytest.approx(exact, rel=0.02)


def test_隣り合う領域を押し出した立体は壁がぴったり合う(sphere):
    # 押し出す長さが頂点ごとに大きく違っても、境の壁は両側で同じ三角形になる
    reach = 5.0 + 10.0 * (np.sin(sphere.vertices[:, 0] * 2.0) > 0)
    field = _cap_field(sphere, (0, 0, 1), 15.0)
    outside = np.maximum(-field, _cap_field(sphere, (0, 0, 1), 30.0))
    disc = thicken(clip_region(sphere, field, reach), THICKNESS)
    ring = thicken(clip_region(sphere, outside, reach), THICKNESS)
    assert (disc ^ ring).volume() == pytest.approx(0.0, abs=1e-6)
    both = thicken(clip_region(sphere, _cap_field(sphere, (0, 0, 1), 30.0), reach), THICKNESS)
    # 境で切らずに作った立体と体積が合う（境の上の頂点は外側の面がわずかに折れるので、0.1% まで許す）
    assert disc.volume() + ring.volume() == pytest.approx(both.volume(), rel=1e-3)


# test list 19: 追加のパーツは、磁石1個で字のピースにつながる
def _box(size, low):
    return manifold3d.Manifold.cube(list(size)).translate(list(low))


def test_追加のパーツをつなぐ場所は接する面の真ん中あたりに見つかる():
    plate = _box((40, 40, 10), (0, 0, 0))
    far = _box((40, 40, 10), (100, 0, 0))  # 離れたピースは選ばれない
    post = _box((12, 12, 30), (14, 14, 10))  # 板の真ん中に立つ棒
    points, normals = facing_points(post, plate, spacing=1.0)
    site = joint_site(post, [far, plate], points, normals, hole_diameter=6.2, hole_depth=3.0, wall=0.8, tolerance=0.01)
    assert site is not None
    piece, mouth, into = site
    assert piece == 1
    assert mouth == pytest.approx([20.0, 20.0, 10.0], abs=1.0)
    assert into == pytest.approx([0.0, 0.0, -1.0], abs=1e-6)
    # 両側に穴を開けると、円柱ぶんの体積が減る
    for solid, direction in ((plate, into), (post, -into)):
        removed = solid.volume() - drill(solid, mouth, direction, 6.2, 3.0).volume()
        assert removed == pytest.approx(np.pi * 3.1**2 * 3.0, rel=0.02)


def test_下のピースが薄すぎるとつなぐ場所は見つからない():
    plate = _box((40, 40, 3), (0, 0, 7))  # 厚さ 3 mm。穴 3 mm と奥の壁 0.8 mm が入らない
    post = _box((12, 12, 30), (14, 14, 10))
    points, normals = facing_points(post, plate, spacing=1.0)
    assert joint_site(post, [plate], points, normals, hole_diameter=6.2, hole_depth=3.0, wall=0.8, tolerance=0.01) is None


def test_丸い面で接していてもつなぐ場所が見つかる():
    # 耳の切り口は丸く盛り上がる。穴の口のふちが面からわずかに浮くぶんは、肉の不足に数えない
    dome = manifold3d.Manifold.sphere(20.0, 96)
    post = _box((16, 16, 30), (-8, -8, 10)) - dome
    points, normals = facing_points(post, dome, spacing=1.0)
    site = joint_site(post, [dome], points, normals, hole_diameter=6.2, hole_depth=3.0, wall=0.8, tolerance=0.01)
    assert site is not None
    assert np.linalg.norm(site[1]) == pytest.approx(20.0, abs=0.1)
