"""球に字を敷き詰め、プレビューを書き出す。

    uv run python -m glyphshell.build
"""

import time
from pathlib import Path

import numpy as np

from glyphshell.glyphs import glyph_shape, is_single_piece, load_font
from glyphshell.layout import LayoutParams, pack, separation
from glyphshell.preview import region_fields, render, write_png
from glyphshell.sdf import glyph_field
from glyphshell.surface import icosphere

FONT = ("/System/Library/Fonts/Avenir Next.ttc", 8)  # Avenir Next Heavy
CHARS = [chr(code) for code in range(33, 127)]
RADIUS = 75.0
SUBDIVISIONS = 6  # 辺の長さは約 1.4 mm

# 磁石は直径 6 mm、厚さ 3 mm。穴の余裕は直径 +0.2 mm、最小の肉厚は 0.8 mm（REQUIREMENTS.md）
MAGNET_DIAMETER, MAGNET_THICKNESS, HOLE_MARGIN, MIN_WALL = 6.0, 3.0, 0.2, 0.8

PARAMS = LayoutParams(
    sizes=(64.0, 50.0, 40.0, 32.0),
    min_gap=1.5,  # メッシュの辺の長さ 1.4 mm 以上
    reach=4.0,
    rotations=24,
    min_neck=MAGNET_THICKNESS + MIN_WALL,
    min_extent=MAGNET_DIAMETER + HOLE_MARGIN + 2 * MIN_WALL,
    seed=1,
)
OUT = Path("out")


def main() -> None:
    font = load_font(*FONT)
    started = time.time()
    fields = []
    for char in CHARS:
        shape = glyph_shape(font, char)
        if is_single_piece(shape):
            fields.append(glyph_field(char, shape))
    print(f"使える字 {len(fields)} 個の距離の格子を作った（{time.time() - started:.0f} 秒）")

    surface = icosphere(RADIUS, SUBDIVISIONS)
    started = time.time()
    placements = pack(surface, fields, PARAMS)
    print(f"{len(placements)} 字を置いた（{time.time() - started:.0f} 秒）")

    dense = np.full((len(placements), len(surface.vertices)), np.inf)
    for i, placement in enumerate(placements):
        dense[i, placement.index] = placement.distance
    _, glyph, bridge = region_fields(dense, PARAMS.reach)
    OUT.mkdir(exist_ok=True)
    write_png(OUT / "layout_preview.png", render(surface, glyph, bridge, pixels_per_unit=3.0))

    neighbours = [
        sum(separation(a, b) <= PARAMS.reach for b in placements if b is not a) for a in placements
    ]
    covered = float((glyph < 0).mean())
    for placement, count in zip(placements, neighbours):
        print(f"  {placement.char}  大きさ {placement.size:.0f}  近い隣 {count}")
    print(f"字が覆う割合 {covered:.0%}、近い隣が3つ未満の字 {sum(n < 3 for n in neighbours)} 個")


if __name__ == "__main__":
    main()
