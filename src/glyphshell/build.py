"""球に字を敷き詰め、接触面を決めて、プレビューを書き出す。

    uv run python -m glyphshell.build           # 配置からやり直す
    uv run python -m glyphshell.build --reuse   # 保存した配置（out/layout.npz）を使う
"""

import dataclasses
import string
import sys
import time
from pathlib import Path

import numpy as np

from glyphshell.glyphs import glyph_shape, is_single_piece, load_font
from glyphshell.contacts import PadSize, find_contacts, piece_fields, stable_pieces
from glyphshell.layout import LayoutParams, load_layout, pack, save_layout
from glyphshell.preview import render, write_png
from glyphshell.sdf import glyph_field
from glyphshell.surface import icosphere

# 字の出どころ。(書体のファイル, 書体の番号, 使う字)
# 小さい記号（. , ' ` - など）は使わない。絵の記号は Avenir Next に無いので別の書体から取る。
SOURCES = [
    (
        "/System/Library/Fonts/Avenir Next.ttc",  # Avenir Next Heavy
        8,
        string.ascii_uppercase + string.ascii_lowercase + string.digits + "#$&@",
    ),
    ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 0, "♥♠♣♦★✿☂☻✦✚✔"),
]
RADIUS = 75.0
SUBDIVISIONS = 6  # 辺の長さは約 1.4 mm

# 磁石は直径 6 mm、厚さ 3 mm。穴の余裕は直径 +0.2 mm、最小の肉厚は 0.8 mm（REQUIREMENTS.md）
MAGNET_DIAMETER, MAGNET_THICKNESS, HOLE_MARGIN, MIN_WALL = 6.0, 3.0, 0.2, 0.8

# ピースの縁は、メッシュの辺の上の点を直線でつないで作るので、角が丸まって少し内側に入る。
# その分の余裕。辺の長さ 1.4 mm の約3割
CONTOUR_ALLOWANCE = 0.4
# 接触の台。長さは両側の「磁石の厚さ＋奥の壁」、幅は「磁石の穴の直径＋両側の壁」。壁には余裕を足す
PAD = PadSize(
    length=2 * (MAGNET_THICKNESS + MIN_WALL + CONTOUR_ALLOWANCE),
    width=MAGNET_DIAMETER + HOLE_MARGIN + 2 * (MIN_WALL + CONTOUR_ALLOWANCE),
)
# 接触として採用する切り口の最小の幅。磁石の直径の半分。
# これより狭い重なりでは、台が字の輪郭から片側 2.8 mm より大きくはみ出す
MIN_CONTACT = MAGNET_DIAMETER / 2
# 1つのピースに要る接触の数。2か所だと、その2点を軸に回って外れる（TESTLIST.md の3番）
MIN_CONTACTS_PER_PIECE = 3
# 接触が足りない字を外して入れ直す回数の上限。回を重ねても減らなくなったら途中で止める
REFILL_ROUNDS = 8
# 接触の印（プレビューの橙の丸）の半径
MARK_RADIUS = 2.0

PARAMS = LayoutParams(
    sizes=(60.0, 52.0, 46.0),
    # 字どうしが重なってよい深さ。線の端の丸み（半径 約6.5 mm）どうしが磁石の穴と壁の幅 7.8 mm で
    # 接するには、両側あわせて約 2.6 mm 重なる必要がある
    max_overlap=3.0,
    min_contact=MIN_CONTACT,
    rotations=24,
    candidates=16,
    min_neck=MAGNET_THICKNESS + MIN_WALL,
    min_extent=PAD.width,
    seed=1,
)
OUT = Path("out")


def _layout(surface) -> list:
    """字を敷き詰める。接触が足りない字は外し、空いた所に別の字を入れ直す。"""
    if "--reuse" in sys.argv:
        return load_layout(OUT / "layout.npz")
    started = time.time()
    fields = []
    for path, face_index, chars in SOURCES:
        font = load_font(path, face_index)
        for char in chars:
            shape = glyph_shape(font, char)
            if is_single_piece(shape):
                fields.append(glyph_field(char, shape))
    placements = pack(surface, fields, PARAMS)
    best = []
    for round_ in range(1, REFILL_ROUNDS + 1):
        contacts = find_contacts(surface, placements, MIN_CONTACT, PAD)
        kept = stable_pieces(len(placements), contacts, MIN_CONTACTS_PER_PIECE)
        print(f"  {round_} 回目: {len(placements)} 字のうち、接触が足りる字 {len(kept)} 個（{time.time() - started:.0f} 秒）")
        if len(kept) > len(best):
            best = [placements[i] for i in kept]
        if len(kept) == len(placements):
            break
        # 外した字とは別の字を試すよう、乱数の種を変える
        params = dataclasses.replace(PARAMS, seed=PARAMS.seed + round_)
        placements = pack(surface, fields, params, existing=[placements[i] for i in kept])
    save_layout(OUT / "layout.npz", best)
    return best


def main() -> None:
    OUT.mkdir(exist_ok=True)
    surface = icosphere(RADIUS, SUBDIVISIONS)
    placements = _layout(surface)
    contacts = find_contacts(surface, placements, MIN_CONTACT, PAD)
    kept = stable_pieces(len(placements), contacts, MIN_CONTACTS_PER_PIECE)
    dropped = [p.char for i, p in enumerate(placements) if i not in kept]
    placements = [placements[i] for i in kept]
    contacts = find_contacts(surface, placements, MIN_CONTACT, PAD)
    pieces = piece_fields(surface, placements, contacts, PAD)

    mark = np.full(len(surface.vertices), np.inf)
    for contact in contacts:
        away = np.linalg.norm(surface.vertices - contact.point, axis=1)
        mark = np.minimum(mark, away - MARK_RADIUS)
    write_png(OUT / "layout_preview.png", render(surface, pieces, mark, pixels_per_unit=3.0))

    counts = np.zeros(len(placements), dtype=int)
    for contact in contacts:
        counts[contact.a] += 1
        counts[contact.b] += 1
    print("  ".join(f"{p.char}:{c}" for p, c in zip(placements, counts)))
    print(f"接触が足りずに外した字: {' '.join(dropped) or 'なし'}")
    print(
        f"ピース {len(placements)} 個、接触 {len(contacts)} か所（磁石 {2 * len(contacts)} 個）、"
        f"字が覆う割合 {float((pieces.min(axis=0) < 0).mean()):.0%}、"
        f"接触が {MIN_CONTACTS_PER_PIECE} か所未満のピース {int((counts < MIN_CONTACTS_PER_PIECE).sum())} 個、"
        f"切り口の幅が台の幅以上の接触 {sum(c.width >= PAD.width for c in contacts)} か所"
    )


if __name__ == "__main__":
    main()
