# glyph-shell-puzzle

中が空の殻を、文字や記号の形をしたピースに分けた立体パズルを作る道具。
字1つが1ピースで、隣どうしは接触面に埋めた磁石でつながる。

- 何を作るか、何を決めたか: `REQUIREMENTS.md`
- 何を確かめるか、いまの合否: `TESTLIST.md`
- 使える技術の調査: `survey/map.md`

## 使い方

```sh
uv sync

# 1. 球（直径 150 mm）に字を敷き詰める
uv run python -m glyphshell.build
#    → out/layout.npz（配置）、out/layout_preview.png（6方向から見た図）

# 2. ピースの立体を作り、検証して書き出す。約30秒
uv run python -m glyphshell.export
#    → out/stl/piece_番号_字.stl   印刷用。外側の面が上、底が z=0
#    → out/assembled.stl           組み上がった位置の全ピース
#    → out/verify_report.json      検証の結果
#    → out/viewer_data.json        ビューワー用のデータ
#    → out/pieces_preview.png      ピースの立体を6方向から見た図

# テスト
uv run pytest
```

球のほかの形に敷き詰めるときは、閉じた1つの立体のメッシュを渡す。

```sh
# 高さ 300 mm のうさぎ。敷き詰めに約10分、書き出しに約5分
uv run python -m glyphshell.build  --mesh data/bunny/bunny.off --height 300 --out out_bunny
uv run python -m glyphshell.export --mesh data/bunny/bunny.off --height 300 --out out_bunny
#    → out_bunny/stl/extra_番号.stl  字のピースにならない追加のパーツ（耳）
```

メッシュを渡したときは、元の形の内側に作ったなめらかな面に字を敷き詰める。ピースの内側は
なめらかで、外側は元の形の表面になる。耳のように細長い部分は、先に切り離して追加のパーツにし、
磁石1個で字のピースにつなぐ。

うさぎのメッシュは libigl の教材データ
（<https://raw.githubusercontent.com/libigl/libigl-tutorial-data/master/bunny.off>）を
`data/bunny/` に置いて使った。`data/` は git に入れていない。

球の敷き詰めは、字を足すのをやめる条件を入れる前に約45分かかった。条件を入れた後の時間は
測っていない（球はやり直していない。保存済みの `out/layout.npz` を使っている）。

うさぎは高さ 300 mm で 46 ピースになり、検証を全項目通った（`TESTLIST.md` の「うさぎでの結果」）。
高さ 200 mm では内側の面が狭く、字が入りきらない。

書体を選ぶための見本は `uv run python -m glyphshell.specimen` で `out/font_specimen.svg` に出る。

## 印刷と組み立て

1. `out/stl/` の STL を1つずつ印刷する。外側の面が上を向いているので、下の反りにはサポートが要る
2. 磁石（直径 6 mm、厚さ 3 mm）を、接触面の穴に横から押し込んで接着する
   - 穴の真下（殻の内側の面）に丸い突起がある穴は、**N 極を接触面の外へ向ける**
   - 突起がない穴は、S 極を外へ向ける
   - この向きを守ると、正しい隣とは必ず引き合い、間違った場所では少なくとも1か所が反発する
3. `out/verify_report.json` の `assembly_order` の順に、外側から入れていく
   - くぼんだ所のピースは、まっすぐ外からではなく、少し斜めから入れる。向きはビューワーの
     「組立の手順」で見られる
4. うさぎの耳（`extra_番号.stl`）は、切り口の穴と、頭のピースの穴に磁石を1個ずつ入れ、
   引き合う向きに接着してから、最後に付ける

ビューワーで、ばらした状態、磁石の極の向き、組み立ての順を確かめられる。

- 球: <https://claude.ai/artifact/46PfsrqPBAawqQpkXYJCyS>（`viewer/puzzle_viewer.html` と `out/viewer_data.json`）
- うさぎ: <https://claude.ai/artifact/Q1dVR7jdAiFcMJKYHPnur7>（同じページの題名だけを変えた `out_bunny/bunny_viewer.html` と `out_bunny/viewer_data.json`）

データを作り直したときは、同じ組を公開し直す。

## しくみ

| 段 | ファイル | すること |
|---|---|---|
| 字の形 | `glyphs.py`、`sdf.py` | 書体から輪郭を取り出し、1つにつながった字だけを残して、距離の格子にする |
| 曲面 | `surface.py` | 球やメッシュを読み、字を写すための局所座標（対数写像）を作る |
| 内側の面 | `skin.py` | メッシュの細長い部分（耳）を切り離し、残りの内側に、ならした面を作る。その面から外へ押し出す長さを決める |
| 配置 | `layout.py` | いちばん広い空きに、隣と重なる相手が最も多く、最も広く覆う字を置く。繰り返す |
| 接触 | `contacts.py` | 重なった字を切り分ける面を接触面にし、磁石の穴が入る台を字の中に足す |
| 立体 | `solids.py` | ピースを曲面から切り出し、厚みを付け、磁石の穴と極の印を付ける。耳をつなぐ場所を探す |
| 検証 | `verify.py` | 重なり、穴の肉厚、抜く順と向き、別の場所にはまらないことを、立体の演算で確かめる |

字どうしは最大 3 mm の深さまで重ねて置く。重なった所を平らに切った面が接触面になるので、
接続部は字の輪郭の内側に収まる。字が細い所や丸い所では、磁石の穴のまわりの壁（台）の角が
輪郭から少しはみ出す。

寸法の定数とその根拠は、`build.py` と `export.py` の先頭にまとめてある。
