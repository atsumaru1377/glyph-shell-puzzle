# 作例と道具の調査（観点 a, b）

調査日: 2026-11-17。PyPI の版・更新日・macOS arm64 wheel の有無は PyPI の JSON API で確認した（確認済み）。それ以外は検索結果と各ページの取得内容による。取得に失敗した項目、検索結果の要約だけに頼った項目は「未確認」と書いた。

## 見つけたもの

### 作例

### Wikipedia ロゴの球体パズル（2003年原案、2010年再設計、種類: 作例）
- 出典: https://www.wikipedia.org/wiki/Puzzle_ball ／ https://www.wikipedia.org/wiki/Wikipedia_logo
- 何をするものか: 球面をジグソー状のピースで分け、各ピースに別の文字体系の字を載せた意匠。2010年版は全面を設計し、ピース51個（ロゴに見えるのは18個）。
- この作品にどう効くか: 「字が載るピースで球を埋める」意匠の最も有名な前例。ただしピースの形は字形ではなく普通のジグソー形で、字は表面の装飾。本作は「字形そのものがピース外形」である点が違う。ピース数の細部は検索結果の要約のみで未確認。
- 入手: 立体モデルは公式配布を確認できず（未確認）。

### Thingiverse「Sphere Puzzle」（カスタマイズ可能、種類: 作例/OpenSCAD）
- 出典: https://www.stlfinder.com/model/sphere-puzzle-xz2wCqNy/1306825 （Thingiverse 原ページの番号は未確認。ミラー）
- 何をするものか: 球のパズルで各ピースに任意の字や文字列を載せられる（Wikipedia ロゴが着想）。内側が少し小さいピースで組み立て順が効く。他のフォントは ttf2dxf で DXF に変換して指定する。
- この作品にどう効くか: 球で試作1個目を作る際の参照実装。ピースは字形ではなく字を刻む形なので、外形が字形になる本作とは異なる。ライセンス・更新時期は未確認。
- 入手: 上記ミラー。ライセンス未確認。

### Henry Segerman「Sphere Autologlyph」（2009年、種類: 作例）
- 出典: https://gallery.bridgesmathart.org/exhibitions/2010-bridges-conference/henrys ／ https://www.fabbaloo.com/blog/2013/3/25/design-of-the-week-sphere-autologlyph.html
- 何をするものか: 単語 SPHERE の20個のコピーで球面を敷き詰めた作品（対称性 D10）。Illustrator で1語を描き、Rhinoceros 3D で球に射影し、曲線のまわりにパイプを作って Shapeways で印刷。サイズ10.4 cm、PA2200ナイロン。
- この作品にどう効くか: 「字が球面を敷き詰める」点で最も近い芸術作品。字の隙間を許す構造（字を管の網にする）は本作の「隙間を許す」方針の前例。ただし1語の繰り返しで、1字=1ピースの分割はない。
- 入手: 作品情報のみ。モデル配布は未確認。

### 3Dポリオミノ・パズル（種類: 論文。書誌は未確認）
- 出典: https://webarchive.lib.cuhk.edu.hk/20210324163448mp_/http:/www.cse.cuhk.edu.hk/~cwfu/papers/polypuzzle/paper/pjpuzzle.pdf （ファイル名は pjpuzzle。取得失敗。検索結果の要約のみ）
- 何をするものか: 入力立体の表面をパラメータ化し、ポリオミノ形のピースで敷き詰めて表面に巻きつける。
- この作品にどう効くか: 「曲面をパラメータ化して2D形で敷き詰め、立体に戻す」流れが本作と同型。ただしピースは字形でなく、題名・著者・会議・年が未確認。論文の確認が必要。
- 入手: 未確認（コード公開の有無も未確認）。

### 磁石でつなぐ球・立体パズルの例（CRYPTORB 02、MagnoSphere ほか、種類: 製品/作例）
- 出典: https://www.cgtrader.com/3d-print-models/games-toys/toy/cryptorb-02 ／ https://makerworld.com/models/680441 ／ https://www.printables.com/model/1059470-dodecahedron-magnetic-moon
- 何をするものか: CRYPTORB 02 は検索要約によると14ピース、約12 cm、ø4×3 mm ネオジム磁石48個。MagnoSphere は多色で、磁極が1つでも逆だと成立しないと注意書きがある。Dodecahedron Magnetic Moon は磁石で組む月で、辺を下にして印刷すると良好と書かれている。
- この作品にどう効くか: 磁石の寸法（ø4×3 mm など）、極性の管理、印刷向きの実例。磁極の割り当てが正解の一意性に使える可能性がある（自分の推論）。ただし3件とも直接取得できず（CGTrader は取得結果が空、MakerWorld は403）、数値は検索要約のみで未確認。
- 入手: 各URL。ライセンスは未確認。

### 道具: 字形と2D処理

### fontTools（種類: ツール）
- 出典: https://github.com/fonttools/fonttools ／ https://pypi.org/project/fonttools/
- 何をするものか: フォントを読み、グリフの輪郭（TrueType の2次/OpenType の3次ベジェ）を取り出す。pens API で輪郭を点列やパスに変換できる。
- この作品にどう効くか: 字形の外形を2D曲線として取るのに十分。曲線の平坦化は自前か shapely 等が要る。
- 入手: MIT。4.68.0（2026-10-27）。macOS universal2 wheel あり（確認済み）。保守は活発。

### skia-pathops（種類: ツール）
- 出典: https://github.com/fonttools/skia-pathops ／ https://pypi.org/project/skia-pathops/
- 何をするものか: 2Dパスの和・差・交差。グリフの重なった輪郭を整理したり、字形同士の衝突判定・余白（ギャップ）の確保に使える。
- この作品にどう効くか: 字形のオフセット（隙間の確保）には別途 shapely（BSD-3-Clause、2.2.0、2026-10-07、macOS arm64 wheel 確認済み）の buffer が使える。
- 入手: BSD-3-Clause。0.9.2（2026-02-16）。macOS universal2 wheel あり（確認済み）。

### freetype-py（種類: ツール）
- 出典: https://pypi.org/project/freetype-py/
- 何をするものか: FreeType の Python バインディング。アウトライン取得は fontTools で足りるので、使うならヒンティング無しのメトリクス取得程度。
- この作品にどう効くか: fontTools で足りるので優先度は低い。
- 入手: 2.5.1（2024-08-29、最後の更新がやや古い）。macOS universal2 wheel あり。ライセンスは未確認（PyPI 欄が空）。

### 道具: 2Dを曲面に写す

### potpourri3d（種類: ツール）
- 出典: https://github.com/nmwsharp/potpourri3d ／ https://pypi.org/project/potpourri3d/
- 何をするものか: geometry-central の Python バインディング。熱法による測地距離、ベクトル熱法による対数写像（log map）、測地線のトレース、測地経路の直線化、パラレル輸送。
- この作品にどう効くか: 「字の中心点から測地的な極座標を作って2D形を曲面に写す」（exponential map／デカール写像の考え方）の土台として最有力。log map は近傍の局所2D座標を直接返すので、字形の輪郭点を曲面に載せるのに使える。広い字や曲率の大きい所で歪みが出る点は要検証。
- 入手: MIT。1.4.0（2026-03-25）。macOS arm64 wheel（cp310/cp311）あり（確認済み）。保守は継続。

### mouette（BFF 実装、種類: ツール）
- 出典: https://gcoiffier.github.io/mouette/algorithms/parametrization/bff ／ https://github.com/GCoiffier/mouette ／ https://pypi.org/project/mouette/
- 何をするものか: Boundary First Flattening（Sawhney & Crane, "Boundary First Flattening", ACM Transactions on Graphics, 2017）の Python 実装。円盤トポロジーの三角形メッシュの共形平坦化。境界の尺度か曲率を指定できる。
- この作品にどう効くか: 殻を「字の形に切った円盤状パッチ」ごとに平坦化する経路で使える。逆に、字形を曲面に写す用途では、パッチ形状が先に決まっている必要がある。
- 入手: MIT。1.3（2026-11-01）。純Python系で wheel の macOS 表記は未確認（インストールは未検証）。公式C++実装は https://github.com/GeometryCollective/boundary-first-flattening （MIT、CLI。Python バインディングは見つからず）。

### 論文 Interactive Decal Compositing with Discrete Exponential Maps（種類: 論文）
- 出典: https://cindygr.github.io/files/sig2006tm.pdf ／ https://prism.ucalgary.ca/handle/1880/46212
- 何をするものか: Ryan Schmidt, Cindy Grimm, Brian Wyvill, ACM Transactions on Graphics 25(3), 2006（SIGGRAPH 2006）。点と測地半径から離散的な指数写像を作り、デカールを貼る。Dijkstra にわずかな追加で O(N log N)。
- この作品にどう効くか: 字を曲面に貼る手法の原典。局所共形パラメータ化より「四角さ」が保たれると述べられている。自前で数十行で実装でき、potpourri3d の log map で代替もできる。
- 入手: 公式コードは未確認。

### libigl Python バインディング（種類: ツール）
- 出典: https://github.com/libigl/libigl-python-bindings ／ https://pypi.org/project/libigl/
- 何をするものか: 幾何処理ライブラリ libigl の Python 版。LSCM・調和パラメータ化・厳密測地距離・ブーリアン等が使えるはず。ただし個々の関数が pip 版に入っているかは取得ページでは確認できず（未確認）。
- この作品にどう効くか: LSCM などの局所平坦化が必要なときの予備。potpourri3d と役割が重なる。
- 入手: 2.6.3（2026-09-01）。macOS arm64 wheel（cp310/cp311）あり（確認済み）。ライセンスはリポジトリに GPL-3.0 と MPL-2.0 の両方が置かれており、適用範囲は未確認（個人作品なら問題になりにくいが、配布するなら要確認）。ドキュメントが古いという注意書きあり。

### gpytoolbox（種類: ツール）
- 出典: https://gpytoolbox.org ／ https://pypi.org/project/gpytoolbox/
- 何をするものか: libigl 風の幾何処理を Python で。メッシュ処理、ラプラシアン、測地距離など。機能の詳細は未確認。
- この作品にどう効くか: 純粋な補助。上の2つで足りなければ検討。
- 入手: MIT。0.3.8（2026-10-06）。macOS arm64 wheel あり（確認済み）。

### 道具: 殻の厚み付け、ブーリアン、オフセット

### manifold3d（種類: ツール）
- 出典: https://github.com/elalish/manifold ／ https://pypi.org/project/manifold3d/
- 何をするものか: 常に多様体を保つ高速メッシュブーリアン。符号付き距離関数から面を作る level set 関数もある。
- この作品にどう効くか: ピース切り出し（殻と字形押し出しの交差）、磁石穴の差、隙間確保で使う。ブーリアンの頑健さと速度が長所。メッシュの3Dオフセット専用関数があるかは取得ページでは未確認（level set で代用は可能と読めるが未検証）。
- 入手: Apache-2.0。3.5.5（2026-11-13）。macOS arm64 wheel あり（確認済み）。保守は活発。

### trimesh（種類: ツール）
- 出典: https://github.com/mikedh/trimesh ／ https://pypi.org/project/trimesh/
- 何をするものか: メッシュの読み書き、検査、変換。ブーリアンは外部エンジン（manifold3d など）を呼ぶ形。
- この作品にどう効くか: STL の入出力、水密性の検査、体積計算、manifold3d との橋渡し。
- 入手: MIT。5.2.1（2026-11-12）。純Python。保守は活発。

### PyMeshLab（種類: ツール）
- 出典: https://github.com/cnr-isti-vclab/PyMeshLab ／ https://pypi.org/project/pymeshlab/
- 何をするものか: MeshLab のフィルタ（再メッシュ、スムージング、修復、ブーリアン等）を Python から使う。
- この作品にどう効くか: バニーのような複雑なメッシュの前処理（再メッシュ、穴埋め）に有用。
- 入手: GPL-3.0。2025.7.post1（2026-01-30）。macOS arm64 wheel あり（確認済み）。

### Blender（bpy モジュール、種類: ツール）
- 出典: https://pypi.org/project/bpy/ ／ https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/booleans.html
- 何をするものか: Blender を Python モジュールとして使う。テキストオブジェクトのメッシュ化、Solidify（厚み付け）、Shrinkwrap（曲面への投影）、Boolean が使える。
- この作品にどう効くか: Solidify で殻、Shrinkwrap で平面のタイルを曲面に近づけることができる。Boolean の Manifold ソルバーの有無はマニュアルの該当節を読めず未確認。
- 入手: GPL-3.0。bpy 5.3.0（2026-11-10）。macOS arm64 wheel は cp313 のみ確認。過去の版では Python 3.11 との不一致でインストールが失敗する報告あり（https://projects.blender.org/blender/blender/issues/120181）。ヘッドレスの Blender 本体を使う既存環境があるなら bpy は不要。

### 道具: 配置の最適化

### 配置の最適化に使える既成のコード
- 出典: 検索では見つからず。
- 内容: 曲面上の字形の敷き詰め・配置最適化を行う公開コードは確認できなかった。球で1個目を作る段階では、球面を等角・等面積で区切る初期配置（正多面体や Fibonacci 格子）と、字形の衝突判定（shapely、skia-pathops）を使い、字の選択と回転を探索する自前実装が現実的と思われる（推論。未検証）。
- 近縁の論文候補: Elber と Kim の自由曲面上の3Dジグソー合成（"Synthesis of 3D Jigsaw Puzzles over Freeform 2-Manifolds"、掲載誌・年は未確認）。https://handandmachine.org/classes/computational_fabrication/2024/12/09/daniels-final-project/ 経由で言及を確認しただけで、原典は未確認。

## この観点の結論

### 使えそうな手段の上位3つ
1. **fontTools + potpourri3d の log map + shapely で字形を曲面に写す。** 全て macOS arm64 の pip wheel があり、MIT/BSD、2026年に更新済みで、字形 → 曲面上の輪郭の流れを Python だけで組める。
2. **manifold3d + trimesh でピース生成。** Apache-2.0 / MIT で、最新版が11月に出ている。殻とピース柱の交差、磁石穴の差、隙間の確保を頑健に行える。
3. **Segerman「Sphere Autologlyph」とWikipedia球体パズルを設計の手本にする。** 字が球面を敷き詰める作品が実在し、前者は字を管の網にして隙間を許す方式で、本作の方針に近い。

### 担当者が決める必要がある点
- 曲面への写し方: (A) potpourri3d の log map（字ごとの局所写像。字の大きさは曲率に依存） / (B) 殻を字形のパッチに切って BFF（mouette）で平坦化（歪みは小さいが、パッチ形状が先に決まる） / (C) 平面の字形を押し出して殻と交差させるだけ（球なら最も簡単、複雑な形では歪む）
- ブーリアンの環境: (A) manifold3d + trimesh（pip のみ） / (B) bpy（既存の Blender 環境を流用）
- 配置の最適化を自前で作るか、まず球で手動配置して様子を見るか。
- 公開・配布を考えるなら、libigl（GPL/MPL）、PyMeshLab・bpy（GPL）のライセンスを使うか避けるか。

### 分からなかったこと
- 文字・数字・記号でできた殻状の立体で、字形そのものがピースになる3Dプリント作例（磁石接続を含む）は、検索では見つからなかった。「ない」とは言えない。
- 3Dポリオミノ・パズル論文の書誌とコード公開の有無、Elber & Kim の書誌。
- libigl の pip 版に必要な関数（exact_geodesic、LSCM、ブーリアン）が入っているか。
- manifold3d の3Dオフセット機能、Blender Boolean の Manifold ソルバーの有無。
- CRYPTORB 02、MagnoSphere、Thingiverse Sphere Puzzle の一次ページの内容（ライセンス、更新日）。
- 字形の曲面への写像で、字の大きさ・曲率と歪みの関係の定量的な数値。
