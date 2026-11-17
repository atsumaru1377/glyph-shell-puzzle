# glyph-shell-puzzle

中が空の殻を、文字や記号の形をしたピースに分けた立体パズルを作る道具。
字1つが1ピースで、隣どうしは接触面に埋めた磁石でつながる。

- 何を作るか、何を決めたか: `REQUIREMENTS.md`
- 何を確かめるか、いまの合否: `TESTLIST.md`
- 使える技術の調査: `survey/map.md`

## 使い方

```sh
uv sync

# 1. 球（直径 150 mm）に字を敷き詰める。約45分かかる
uv run python -m glyphshell.build
#    → out/layout.npz（配置）、out/layout_preview.png（6方向から見た図）

# 2. ピースの立体を作り、検証して書き出す。数秒
uv run python -m glyphshell.export
#    → out/stl/piece_番号_字.stl   印刷用。外側の面が上、底が z=0
#    → out/assembled.stl           組み上がった位置の全ピース
#    → out/verify_report.json      検証の結果
#    → out/viewer_data.json        ビューワー用のデータ

# テスト
uv run pytest
```

球のほかの形に敷き詰めるときは、閉じた1つの立体のメッシュを渡す。

```sh
uv run python -m glyphshell.build  --mesh data/bunny/bunny.off --height 200 --out out_bunny
uv run python -m glyphshell.export --mesh data/bunny/bunny.off --height 200 --out out_bunny
```

うさぎのメッシュは libigl の教材データ
（<https://raw.githubusercontent.com/libigl/libigl-tutorial-data/master/bunny.off>）を
`data/bunny/` に置いて使った。`data/` は git に入れていない。

書体を選ぶための見本は `uv run python -m glyphshell.specimen` で `out/font_specimen.svg` に出る。

## 印刷と組み立て

1. `out/stl/` の STL を1つずつ印刷する。外側の面が上を向いているので、下の反りにはサポートが要る
2. 磁石（直径 6 mm、厚さ 3 mm）を、接触面の穴に横から押し込んで接着する
   - 穴の真下（殻の内側の面）に丸い突起がある穴は、**N 極を接触面の外へ向ける**
   - 突起がない穴は、S 極を外へ向ける
   - この向きを守ると、正しい隣とは必ず引き合い、間違った場所では少なくとも1か所が反発する
3. `out/verify_report.json` の `assembly_order` の順に、外側から入れていく
   - `test4_insert_before` に載っている組は、左の字を右の字より先に入れる

ビューワー（<https://claude.ai/artifact/46PfsrqPBAawqQpkXYJCyS>）で、ばらした状態、
磁石の極の向き、組み立ての順を確かめられる。データを作り直したときは、
`viewer/puzzle_viewer.html` と `out/viewer_data.json` を公開し直す。

## しくみ

| 段 | ファイル | すること |
|---|---|---|
| 字の形 | `glyphs.py`、`sdf.py` | 書体から輪郭を取り出し、1つにつながった字だけを残して、距離の格子にする |
| 曲面 | `surface.py` | 球やメッシュを読み、字を写すための局所座標（対数写像）を作る |
| 配置 | `layout.py` | いちばん広い空きに、隣と重なる相手が最も多く、最も広く覆う字を置く。繰り返す |
| 接触 | `contacts.py` | 重なった字を切り分ける面を接触面にし、磁石の穴が入る台を字の中に足す |
| 立体 | `solids.py` | ピースを曲面から切り出し、厚みを付け、磁石の穴と極の印を付ける |
| 検証 | `verify.py` | 重なり、穴の肉厚、抜く順、別の場所にはまらないことを、立体の演算で確かめる |

字どうしは最大 3 mm の深さまで重ねて置く。重なった所を平らに切った面が接触面になるので、
接続部は字の輪郭の内側に収まる。字が細い所や丸い所では、磁石の穴のまわりの壁（台）の角が
輪郭から少しはみ出す。

寸法の定数とその根拠は、`build.py` と `export.py` の先頭にまとめてある。
