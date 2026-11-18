import manifold3d
import numpy as np
import pytest

from glyphshell.verify import (
    ContactFrame,
    assign_polarity,
    attracts,
    fit_transforms,
    overlapping_contacts,
    removal_plan,
    facing_normals,
    facing_points,
    false_fits,
    overlap_volume,
    removal_direction,
    removal_blocked_by,
    wall_normals,
    wall_shortfall,
)


def cube(size, at=(0.0, 0.0, 0.0)):
    return manifold3d.Manifold.cube([size, size, size]).translate(list(at))


# test list 2: ピースどうしが重ならない
def test_離れた立体の重なりは0():
    assert overlap_volume(cube(10), cube(10, at=(20, 0, 0))) == 0.0


def test_面で接する立体の重なりは0():
    assert overlap_volume(cube(10), cube(10, at=(10, 0, 0))) == pytest.approx(0.0, abs=1e-6)


def test_食い込んだ立体の重なりは食い込んだ体積():
    assert overlap_volume(cube(10), cube(10, at=(9, 0, 0))) == pytest.approx(100.0)


# test list 4: どのピースも外から入れられる
def test_接触面から離れる向きを選ぶ():
    outward = np.array([0.0, 0.0, 1.0])
    # 隣が +x と +y の側にいる。抜く向きは、どちらの隣にも近づかない
    direction = removal_direction(outward, [np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0])])
    assert direction @ np.array([1.0, 0.0, 0.0]) <= 1e-9
    assert direction @ np.array([0.0, 1.0, 0.0]) <= 1e-9
    assert direction @ outward > 0


def test_向かい合う隣に挟まれていても外向きに抜ける():
    outward = np.array([0.0, 0.0, 1.0])
    direction = removal_direction(outward, [np.array([1.0, 0.0, 0.0]), np.array([-1.0, 0.0, 0.0])])
    assert direction == pytest.approx(outward)


def test_抜く経路をふさぐ立体を見つける():
    piece = cube(10)
    side = cube(10, at=(10, 0, 0))  # 横で接しているだけ
    lid = cube(10, at=(0, 0, 12))  # 真上にあって、抜く経路をふさぐ
    blocked = removal_blocked_by(piece, [side, lid], np.array([0.0, 0.0, 1.0]), travel=8.0, step=1.0)
    assert blocked == [1]


def test_経路が空いていればふさぐ立体はない():
    piece = cube(10)
    side = cube(10, at=(10, 0, 0))
    assert removal_blocked_by(piece, [side], np.array([0.0, 0.0, 1.0]), travel=8.0, step=1.0) == []


# test list 6: 磁石の穴の周りに肉厚がある
def test_穴の周りの肉厚が足りれば不足は0():
    block = cube(20, at=(-10, -10, -10))
    # x=10 の面の中心から −x へ掘る穴（直径 6、深さ 3）。周りの肉は十分ある
    shortfall = wall_shortfall(
        block, start=np.array([10.0, 0.0, 0.0]), into=np.array([-1.0, 0.0, 0.0]),
        hole_diameter=6.0, hole_depth=3.0, wall=0.8,
    )
    assert shortfall == pytest.approx(0.0, abs=1e-3)


def test_穴が縁に近すぎると不足が出る():
    block = cube(20, at=(-10, -10, -10))
    # 穴の中心が上の面から 3.2 しか離れていない（半径 3 + 壁 0.8 = 3.8 に足りない）
    shortfall = wall_shortfall(
        block, start=np.array([10.0, 0.0, 6.8]), into=np.array([-1.0, 0.0, 0.0]),
        hole_diameter=6.0, hole_depth=3.0, wall=0.8,
    )
    assert shortfall > 0.1


# test list 5: 置き場所が1つに決まる
UP = np.array([0.0, 0.0, 1.0])


def _frames(points):
    return [ContactFrame(np.array(p, dtype=float), np.array(d, dtype=float), UP) for p, d in points]


def test_接触の並びが違うピースは別の場所にはまらない():
    a = _frames([((0, 0, 0), (-1, 0, 0)), ((30, 0, 0), (1, 0, 0)), ((10, 25, 0), (0, 1, 0))])
    b = _frames([((0, 0, 0), (-1, 0, 0)), ((45, 0, 0), (1, 0, 0)), ((30, 12, 0), (0, 1, 0))])
    assert false_fits([a, b], position_tolerance=3.0, angle_tolerance=np.radians(20)) == []


def test_接触の並びが同じピースは入れ替わる():
    a = _frames([((0, 0, 0), (-1, 0, 0)), ((30, 0, 0), (1, 0, 0)), ((10, 25, 0), (0, 1, 0))])
    # a を平行移動して回しただけの並び
    turn = np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    b = [ContactFrame(turn @ f.point + np.array([100.0, 5.0, 0.0]), turn @ f.outward, UP) for f in a]
    assert false_fits([a, b], position_tolerance=3.0, angle_tolerance=np.radians(20)) == [(0, 1), (1, 0)]


def test_対称な並びのピースは向きを変えても同じ場所にはまる():
    # 正三角形の頂点に、外向きの接触がある。120度回しても同じ並びになる
    angles = np.radians([90, 210, 330])
    a = [
        ContactFrame(20 * np.array([np.cos(t), np.sin(t), 0.0]), np.array([np.cos(t), np.sin(t), 0.0]), UP)
        for t in angles
    ]
    assert false_fits([a], position_tolerance=3.0, angle_tolerance=np.radians(20)) == [(0, 0)]


def test_裏返さないと重ならない鏡写しの並びははまらない():
    a = _frames([((0, 0, 0), (-1, 0, 0)), ((30, 0, 0), (1, 0, 0)), ((10, 25, 0), (0, 1, 0))])
    flip = np.array([-1.0, 1.0, 1.0])
    mirrored = [ContactFrame(f.point * flip, f.outward * flip, UP) for f in a]
    assert false_fits([a, mirrored], position_tolerance=3.0, angle_tolerance=np.radians(20)) == []


# test list 5 と 9: 磁石の向きで、間違った置き方を反発させる
def _numbered(points, first):
    """接触の番号つきの並び。points は (番号, 位置, 外向き) の列。"""
    return [
        ContactFrame(np.array(p, dtype=float), np.array(d, dtype=float), UP, contact=c, first=first)
        for c, p, d in points
    ]


def test_動かしたピースと重なる接触の組を返す():
    a = _numbered([(0, (0, 0, 0), (-1, 0, 0)), (1, (30, 0, 0), (1, 0, 0)), (2, (10, 25, 0), (0, 1, 0))], True)
    shift = np.array([100.0, 5.0, 0.0])
    b = [ContactFrame(f.point + shift, f.outward, UP, contact=3 + k, first=True) for k, f in enumerate(a)]
    transforms = fit_transforms(a, b, False, 3.0, np.radians(20))
    assert len(transforms) == 1
    assert overlapping_contacts(a, b, transforms[0], 3.0, np.radians(20)) == [(0, 0), (1, 1), (2, 2)]


def test_同じ向きの磁石どうしの置き方は引き合い1つでも逆なら引き合わない():
    a = _numbered([(0, (0, 0, 0), (-1, 0, 0)), (1, (30, 0, 0), (1, 0, 0)), (2, (10, 25, 0), (0, 1, 0))], True)
    b = _numbered([(3, (0, 0, 0), (-1, 0, 0)), (4, (30, 0, 0), (1, 0, 0)), (5, (10, 25, 0), (0, 1, 0))], True)
    pairs = list(zip(a, b))
    assert attracts(pairs, np.array([True, True, True, True, True, True]))
    assert not attracts(pairs, np.array([True, True, True, True, True, False]))


def test_決めた磁石の向きでは間違った置き方がどれも引き合わない():
    a = _numbered([(0, (0, 0, 0), (-1, 0, 0)), (1, (30, 0, 0), (1, 0, 0)), (2, (10, 25, 0), (0, 1, 0))], True)
    b = _numbered([(3, (0, 0, 0), (-1, 0, 0)), (4, (30, 0, 0), (1, 0, 0)), (5, (10, 25, 0), (0, 1, 0))], True)
    c = _numbered([(6, (0, 0, 0), (-1, 0, 0)), (7, (30, 0, 0), (1, 0, 0)), (8, (10, 25, 0), (0, 1, 0))], False)
    wrong = [list(zip(a, b)), list(zip(b, c)), list(zip(a, c))]
    polarity = assign_polarity(9, wrong, seed=0)
    assert not any(attracts(pairs, polarity) for pairs in wrong)


def test_接触が入れ替わるだけの置き方は向きを混ぜれば反発する():
    # 3回対称のピースを回す置き方。接触が 0→1→2→0 と入れ替わるので、3つが同じ向きのときだけ引き合う
    a = _numbered([(0, (0, 0, 0), (-1, 0, 0)), (1, (30, 0, 0), (1, 0, 0)), (2, (10, 25, 0), (0, 1, 0))], True)
    rotated = [(a[0], a[1]), (a[1], a[2]), (a[2], a[0])]
    polarity = assign_polarity(3, [rotated], seed=0)
    assert len(set(polarity.tolist())) == 2


def test_反発させようのない置き方があれば例外():
    # 重なるのが「同じ接触の同じ側」だけなら、向きをどう決めても引き合う
    a = _numbered([(0, (0, 0, 0), (-1, 0, 0))], True)
    with pytest.raises(ValueError):
        assign_polarity(1, [[(a[0], a[0])]], seed=0)


# test list 4: 決まった順に入れれば、どのピースも外から入れられる
def _prism(outline):
    """xz 平面の輪郭（反時計回り）を、y 方向に 10 mm 押し出した立体。"""
    section = manifold3d.CrossSection([outline])
    return manifold3d.Manifold.extrude(section, 10.0).rotate([90.0, 0.0, 0.0])


def test_くさびに挟まれたピースは隣を抜いた後に斜めへ抜く():
    # 真ん中は上が狭い台形で、左右の隣が上からかぶさっている。3つとも外向きは +z
    left = _prism([(-30, 0), (-10, 0), (-5, 10), (-30, 10)])
    middle = _prism([(-10, 0), (10, 0), (5, 10), (-5, 10)])
    right = _prism([(10, 0), (30, 0), (30, 10), (5, 10)])
    slope = np.array([2.0, 0.0, -1.0]) / np.sqrt(5.0)  # 左の隣から真ん中へ向かう、壁の法線
    mirror = slope * [-1.0, 1.0, 1.0]
    up = np.array([0.0, 0.0, 1.0])
    contact_normals = [[(1, slope)], [(0, -slope), (2, -mirror)], [(1, mirror)]]
    order, directions, stuck = removal_plan(
        [left, middle, right], [up, up, up], contact_normals, travel=15.0, step=1.0, tolerance=1e-6
    )
    assert stuck == []
    assert order == [0, 1, 2]
    assert directions[0] == pytest.approx(up)
    # 真ん中は、残っている右の隣の壁に沿って、左上へ抜く
    assert directions[1] @ (-mirror) == pytest.approx(0.0, abs=1e-9)
    assert directions[1][0] < 0 < directions[1][2]


def test_面で接している所の法線を返す():
    normals = facing_normals(cube(10), cube(10, at=(10, 0, 0)), spacing=1.0)
    assert len(normals) >= 1
    assert normals == pytest.approx(np.tile([1.0, 0.0, 0.0], (len(normals), 1)), abs=1e-6)


def test_面で接している所の点を返す():
    points, normals = facing_points(cube(10), cube(10, at=(10, 0, 0)), spacing=1.0)
    assert len(points) > 50
    assert points[:, 0] == pytest.approx(10.0, abs=1e-6)
    assert normals == pytest.approx(np.tile([1.0, 0.0, 0.0], (len(normals), 1)), abs=1e-6)


def test_離れている立体には接している所がない():
    assert len(facing_normals(cube(10), cube(10, at=(15, 0, 0)), spacing=1.0)) == 0


def test_接触の台が無い隣の壁も避けて抜く():
    # 真ん中は上が狭い台形。隣との接触（磁石の台）を1つも渡さなくても、壁の向きから抜く向きを決める
    left = _prism([(-30, 0), (-10, 0), (-5, 10), (-30, 10)])
    middle = _prism([(-10, 0), (10, 0), (5, 10), (-5, 10)])
    right = _prism([(10, 0), (30, 0), (30, 10), (5, 10)])
    solids = [left, middle, right]
    walls = wall_normals(solids, spacing=1.0)
    assert [sorted({j for j, _ in wall}) for wall in walls] == [[1], [0, 2], [1]]
    up = np.array([0.0, 0.0, 1.0])
    order, directions, stuck = removal_plan(solids, [up, up, up], walls, travel=15.0, step=1.0, tolerance=1e-6)
    assert stuck == []
    assert order == [0, 1, 2]


def test_互いにふさぎ合うピースは抜けないものとして返す():
    piece = cube(10)
    cage = cube(30, at=(-10, -10, -10)) - cube(12, at=(-1, -1, -1))  # まわりを全部囲む
    up = np.array([0.0, 0.0, 1.0])
    order, directions, stuck = removal_plan([piece, cage], [up, up], [[], []], travel=8.0, step=1.0, tolerance=1e-6)
    assert order == []
    assert stuck == [0, 1]
    assert directions == [None, None]
