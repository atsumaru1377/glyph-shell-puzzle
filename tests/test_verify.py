import manifold3d
import numpy as np
import pytest

from glyphshell.verify import (
    ContactFrame,
    assign_polarity,
    attracts,
    fit_transforms,
    overlapping_contacts,
    removal_order,
    false_fits,
    overlap_volume,
    removal_direction,
    removal_blocked_by,
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
def test_ふさぐピースを先に抜く順を返す():
    # 0 は 1 にふさがれ、1 は 2 にふさがれる
    assert removal_order([[1], [2], []]) == [2, 1, 0]


def test_互いにふさぎ合うと例外():
    with pytest.raises(ValueError):
        removal_order([[1], [0]])
