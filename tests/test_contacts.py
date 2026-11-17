import numpy as np
import pytest
from shapely.geometry import box

from glyphshell.contacts import (
    Contact,
    PadSize,
    dense_fields,
    find_contacts,
    piece_fields,
    stable_pieces,
)
from glyphshell.layout import LayoutParams, pack
from glyphshell.sdf import glyph_field
from glyphshell.surface import icosphere

PAD = PadSize(length=7.6, width=7.8)
MIN_WIDTH = 3.0  # 長方形の角どうしの重なりは幅が狭いので、試験では小さい幅を使う
PARAMS = LayoutParams(
    sizes=(24.0, 18.0, 13.0),
    max_overlap=2.5,
    min_contact=MIN_WIDTH,
    rotations=8,
    candidates=6,
    min_neck=3.8,
    min_extent=7.8,
    seed=3,
)


@pytest.fixture(scope="module")
def sphere():
    return icosphere(radius=40.0, subdivisions=5)


@pytest.fixture(scope="module")
def placements(sphere):
    # 大きさの違う長方形を多めに用意し、球が埋まって隣どうしが重なるようにする
    shapes = {
        chr(ord("a") + k): box(0, 0, 0.8 + 0.05 * (k % 7), 0.8 + 0.07 * (k % 5)) for k in range(20)
    }
    return pack(sphere, [glyph_field(c, s) for c, s in shapes.items()], PARAMS)


@pytest.fixture(scope="module")
def contacts(sphere, placements):
    return find_contacts(sphere, placements, MIN_WIDTH, PAD)


def test_重なった字どうしに接触が見つかる(contacts):
    assert len(contacts) >= 3


def test_接触の向きは曲面に接し長さ1(contacts):
    for contact in contacts:
        assert np.linalg.norm(contact.direction) == pytest.approx(1.0)
        assert abs(contact.direction @ contact.normal) < 1e-6


def test_接触面の幅は決めた幅以上(contacts):
    assert all(contact.width >= MIN_WIDTH for contact in contacts)


# 接続部は字の輪郭の内側に収まる（突起にしない）
def test_接触面の中心は両方の字の輪郭の内側にある(sphere, placements, contacts):
    fields = dense_fields(placements, len(sphere.vertices))
    for contact in contacts:
        vertex = int(np.linalg.norm(sphere.vertices - contact.point, axis=1).argmin())
        assert fields[contact.a, vertex] < 1.0  # 頂点1つぶんのずれは許す
        assert fields[contact.b, vertex] < 1.0


def test_ピースが字の輪郭からはみ出すのは接触の台の中だけ(sphere, placements, contacts):
    glyphs = dense_fields(placements, len(sphere.vertices))
    pieces = piece_fields(sphere, placements, contacts, PAD)
    reach = np.hypot(PAD.length / 2, PAD.width / 2)
    for piece, vertex in zip(*np.nonzero((pieces < 0) & (glyphs >= 0))):
        own = [c for c in contacts if piece in (c.a, c.b)]
        assert any(np.linalg.norm(sphere.vertices[vertex] - c.point) <= reach for c in own)


def test_接触の台は3つ目の字にかからない(sphere, placements, contacts):
    glyphs = dense_fields(placements, len(sphere.vertices))
    for contact in contacts:
        offset = sphere.vertices - contact.point
        along = offset @ contact.direction
        across = offset @ np.cross(contact.normal, contact.direction)
        inside = (
            (np.abs(along) < PAD.length / 2)
            & (np.abs(across) < PAD.width / 2)
            & (np.linalg.norm(offset, axis=1) < PAD.width)
        )
        others = np.delete(glyphs[:, inside], [contact.a, contact.b], axis=0)
        assert (others >= 0).all()


def test_接触面の両側は別々のピースになる(sphere, placements, contacts):
    pieces = piece_fields(sphere, placements, contacts, PAD)
    for contact in contacts:
        for piece, sign in ((contact.a, -1), (contact.b, 1)):
            probe = contact.point + sign * contact.direction * 3.0
            vertex = int(np.linalg.norm(sphere.vertices - probe, axis=1).argmin())
            assert pieces[piece, vertex] < 0


# test list 2 の頂点の上での確認: ピースどうしが重ならない
def test_どの頂点も2つ以上のピースの内側にならない(sphere, placements, contacts):
    pieces = piece_fields(sphere, placements, contacts, PAD)
    assert ((pieces < 0).sum(axis=0) <= 1).all()


# test list 3: どのピースも3か所以上で隣とつながる
def test_接触が足りないピースを外すと残りは全て足りる():
    def contact(a, b):
        zero = np.zeros(3)
        return Contact(a, b, zero, zero, zero, 5.0)

    # 0,1,2,3 は互いに全部つながる（各3か所）。4 は 0 と 1 にだけつながる（2か所）
    contacts = [contact(a, b) for a in range(4) for b in range(a + 1, 4)] + [contact(0, 4), contact(1, 4)]
    assert stable_pieces(5, contacts, minimum=3) == [0, 1, 2, 3]


def test_外したピースのせいで足りなくなったピースも外す():
    def contact(a, b):
        zero = np.zeros(3)
        return Contact(a, b, zero, zero, zero, 5.0)

    # 鎖のようにつながるだけなので、端から順に全部外れる
    contacts = [contact(0, 1), contact(1, 2), contact(2, 3)]
    assert stable_pieces(4, contacts, minimum=3) == []


def test_台の中では接触面の平面でピースが分かれる(sphere, placements, contacts):
    pieces = piece_fields(sphere, placements, contacts, PAD)
    for contact in contacts:
        offset = sphere.vertices - contact.point
        along = offset @ contact.direction
        across = offset @ np.cross(contact.normal, contact.direction)
        # 台の縁から頂点1つぶん内側の頂点だけを見る
        inner = (
            (np.abs(along) < PAD.length / 2 - 1.5)
            & (np.abs(across) < PAD.width / 2 - 1.5)
            & (np.linalg.norm(offset, axis=1) < PAD.width)
        )
        assert (pieces[contact.a, inner & (along < 0)] < 0).all()
        assert (pieces[contact.b, inner & (along > 0)] < 0).all()


def test_接触面でピースどうしの間に隙間ができない(sphere, placements, contacts):
    pieces = piece_fields(sphere, placements, contacts, PAD)
    for contact in contacts:
        offset = sphere.vertices - contact.point
        along = offset @ contact.direction
        across = offset @ np.cross(contact.normal, contact.direction)
        inner = (
            (np.abs(along) < PAD.length / 2 - 1.5)
            & (np.abs(across) < PAD.width / 2 - 1.5)
            & (np.linalg.norm(offset, axis=1) < PAD.width)
        )
        # 接触面の近くでは、値が接触面からの距離そのものになる（傾きが 1）
        beside = inner & (np.abs(along) < 1.0)
        assert pieces[contact.a, beside] == pytest.approx(along[beside], abs=1e-9)
        assert pieces[contact.b, beside] == pytest.approx(-along[beside], abs=1e-9)


def test_接触面の中心は曲面の上にあり法線はその場所のもの(sphere, contacts):
    for contact in contacts:
        assert np.linalg.norm(contact.point) == pytest.approx(40.0, abs=0.05)
        assert contact.normal @ contact.point / np.linalg.norm(contact.point) == pytest.approx(1.0, abs=1e-3)
