"""書体の見本を SVG に書き出す。書体を選ぶための資料。

    uv run python -m glyphshell.specimen

字ごとに、ピースに使えるか（1つにつながっているか）と、磁石を埋められる最小の
キャップハイト（mm）を示す。
"""

from pathlib import Path
from statistics import median

from shapely.geometry import Polygon

from glyphshell.glyphs import glyph_shape, is_single_piece, load_font, neck_width

SUPPLEMENTAL = "/System/Library/Fonts/Supplemental/"
FONTS = [
    ("Arial Black", SUPPLEMENTAL + "Arial Black.ttf", 0),
    ("Impact", SUPPLEMENTAL + "Impact.ttf", 0),
    ("Arial Rounded MT Bold", SUPPLEMENTAL + "Arial Rounded Bold.ttf", 0),
    ("Futura Bold", SUPPLEMENTAL + "Futura.ttc", 2),
    ("Futura Condensed ExtraBold", SUPPLEMENTAL + "Futura.ttc", 4),
    ("Avenir Next Heavy", "/System/Library/Fonts/Avenir Next.ttc", 8),
]
CHARS = [chr(code) for code in range(33, 127)]

# 磁石（厚さ 3 mm）を接触面から押し込むのに要る線の幅。
# 磁石の厚さ 3 mm + 奥に残す壁 0.8 mm（REQUIREMENTS.md の最小の肉厚）。
REQUIRED_NECK_MM = 3.0 + 0.8
# 首の幅を測る刻み。キャップハイト 40 mm のとき 0.2 mm に当たる。
NECK_STEP = 0.0025

COLUMNS = 24
CELL = 64
CAP_PX = 34
OUT = Path("out/font_specimen.svg")


def _path(polygon: Polygon, x0: float, y0: float) -> str:
    """ポリゴンを SVG のパスにする。(x0, y0) はベースラインの左端の画面座標。"""
    parts = []
    for ring in [polygon.exterior, *polygon.interiors]:
        points = " L ".join(f"{x0 + x * CAP_PX:.1f} {y0 - y * CAP_PX:.1f}" for x, y in ring.coords)
        parts.append(f"M {points} Z")
    return " ".join(parts)


def main() -> None:
    rows_per_font = -(-len(CHARS) // COLUMNS)
    block_height = 44 + rows_per_font * CELL + 16
    width = COLUMNS * CELL + 32
    height = 64 + len(FONTS) * block_height
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="Helvetica, sans-serif">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        '<text x="16" y="24" font-size="15" fill="#111">書体の見本: 黒は使える字、'
        "赤は使えない字（離れた部分がある、または輪郭が壊れている）</text>",
        '<text x="16" y="44" font-size="12" fill="#444">字の下の数字は、'
        f"線の幅が {REQUIRED_NECK_MM} mm 以上になる最小のキャップハイト（mm）</text>",
    ]
    for font_index, (name, path, face_index) in enumerate(FONTS):
        font = load_font(path, face_index)
        top = 64 + font_index * block_height
        cells = []
        min_heights = []
        for i, char in enumerate(CHARS):
            x0 = 16 + (i % COLUMNS) * CELL + 8
            y0 = top + 44 + (i // COLUMNS) * CELL + CAP_PX + 4
            try:
                shape = glyph_shape(font, char)
            except ValueError:
                cells.append(
                    f'<text x="{x0}" y="{y0}" font-size="12" fill="#c62828">なし</text>'
                )
                continue
            if not is_single_piece(shape):
                polygons = getattr(shape, "geoms", [])
                d = " ".join(_path(p, x0, y0) for p in polygons)
                cells.append(f'<path d="{d}" fill="#e57373" fill-rule="evenodd"/>')
                continue
            min_height = REQUIRED_NECK_MM / neck_width(shape, NECK_STEP)
            min_heights.append(min_height)
            cells.append(f'<path d="{_path(shape, x0, y0)}" fill="#111" fill-rule="evenodd"/>')
            cells.append(
                f'<text x="{x0}" y="{y0 + 20}" font-size="10" fill="#1565c0">'
                f"{min_height:.0f}</text>"
            )
        summary = (
            f"{name}　使える字 {len(min_heights)}/{len(CHARS)}　"
            f"最小のキャップハイトの中央値 {median(min_heights):.0f} mm"
        )
        svg.append(f'<text x="16" y="{top + 24}" font-size="14" font-weight="bold">{summary}</text>')
        svg.extend(cells)
        print(summary)
    svg.append("</svg>")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(svg), encoding="utf-8")
    print(f"書き出した: {OUT}")


if __name__ == "__main__":
    main()
