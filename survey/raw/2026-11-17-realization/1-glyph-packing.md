# 観点1: 曲面への字形の詰め込み

調査日: 2026-11-17。検索の一部は回数制限で打ち切られた。確認できなかった点は「未確認」と書く。

## 見つけたもの

### Fabricable Tile Decors（2017、論文）
- 出典: https://chenweikai.github.io/projects/proj_siga17.html / https://history.siggraph.org/?p=210658 / HAL https://hal.archives-ouvertes.fr/hal-01592098
- 題名・著者・会議: "Fabricable Tile Decors", Weikai Chen, Yuexin Ma, Sylvain Lefebvre, Shiqing Xin, Jonàs Martínez, Wenping Wang. ACM TOG 36(6), SIGGRAPH Asia 2017, DOI 10.1145/3130800.3130817
- 何をするものか: 利用者が指定したタイルを基底曲面にぎっしり詰め、つながった「タイルの殻」にする。最小全域木でパッチに分け、各パッチは平面に展開でき、サポート無しで印刷できる。パッチ間はヒンジとスナップフィットでつなぐ。
- この作品にどう効くか: 目的に最も近い。曲面に沿ったタイル、タイル種別ごとの大きさと向きの局所調整、印刷可能な接続まで含む。例は球の飾り、ハンドバッグ、テディベア（ページ記載）。ただしタイルは字形ではなく一般の形。字形を入れられるか、任意メッシュで動くか、隣接の接触保証の厳密さは本文未確認（ページには「connected tiles」とあるのみ）。
- コードや材料の入手: 公開コードは見つからず（ページにリンク無し）。ライセンス不明。再実装が必要。

### Synthesis of Filigrees for Digital Fabrication（2016、論文）
- 出典: https://chenweikai.github.io/projects/proj_sig16.html / https://hal.archives-ouvertes.fr/hal-01401520 / 再現性レビュー https://graphicsreplicability.github.io/replicability.graphics/papers/10.1145-2897824.2925911/index.html
- 題名・著者・会議: "Synthesis of Filigrees for Digital Fabrication", Weikai Chen, Xiaolong Zhang, Shiqing Xin, Yang Xia, Sylvain Lefebvre, Wenping Wang. ACM TOG (SIGGRAPH 2016), DOI 10.1145/2897824.2925911
- 何をするものか: 入力の基本要素（骨格表現）で目標曲面を覆うレース状の殻を作る。外観を保つ部分重なりを許して完全な詰め込みを緩め、確率的探索と良い配置の再利用で最適化する。重なりでつながり、印刷できる強度にする。
- この作品にどう効くか: 「つながった構造を保証する」発想の原典。ただし要素は線の骨格で、太い字形のタイルとは違う。字を線画（骨格）として扱う作品なら使える。「隣と小さな接触面でつながる」は重なりで実現しており、磁石接触面とは別物。任意メッシュ対応と回転・拡縮の自由度はページに記載なし（未確認）。
- コードや材料の入手: 公開コード無し。再現性レビューは「著者のソースコードは見つからない」、疑似コードは論文にあるが実装しやすさは5段階で1と評価。論文ページは「個人利用のみ、再配布不可」の著作権表示。

### Calligraphic Packing（2007、論文）
- 出典: https://cgl.uwaterloo.ca/jiexu/projects/packing.htm / https://cgl.uwaterloo.ca/jiexu/paper/xu_GI07.pdf（論文本文を確認）
- 題名・著者・会議: "Calligraphic Packing", Jie Xu, Craig S. Kaplan. Graphics Interface 2007, pp.43-50
- 何をするものか: 2Dの領域をクラスタリングで小領域に分け、各領域に指定の文字列の文字を1回ずつワープして入れる。エネルギー関数で歪みを最小化する。文字の順序の暗示は利用者が一部制御する。
- この作品にどう効くか: 字形を隙間少なく詰めて領域を埋める発想の原典。ただし2D限定（例はすべて2D、3D・曲面の言及なし）で、字形を大きく変形する前提（読めなくなっても可と本文に記載）。この作品は字形をほぼ保つ必要があるので、そのままは合わない。「領域分割してワープ」の考え方だけ借りられる。
- コードや材料の入手: コード公開の記載なし（未確認）。

### Jigsaw Image Mosaics / 2D詰め込みの先行研究（2002、論文、孫引き）
- 出典: Xu & Kaplan 論文の関連研究の節（上記PDF）が Kim and Pellacini の枠組みに言及。論文の書誌（題名・会議）は本調査では未確認。
- 何をするものか: データベースの形を容器に詰め、エネルギーで品質を測りつつ少し変形する枠組みとして Xu & Kaplan が紹介している。
- この作品にどう効くか: 詰め込み評価の考え方の参考。深追いは不要。
- コードや材料の入手: 未確認。

### Discrete Element Textures（2011、論文）
- 出典: https://www.microsoft.com/en-us/research/?p=161088 / https://history.siggraph.org/?p=114649
- 題名・著者・会議: "Discrete Element Textures", Chongyang Ma, Li-Yi Wei, Xin Tong. ACM TOG 30(4), SIGGRAPH 2011, Article 62
- 何をするものか: 小さな見本から、要素の位置・大きさ・形・向きの分布を保って大きな領域に要素を合成する。
- この作品にどう効くか: 要素を「ばらまく」手法で、隣接の接触や一意な置き場所は扱わない。字を1個ずつ指定して敷き詰める用途には不向き。曲面上の対応は検索で確認できず（未確認）。関連の薄いので参考止まり。
- コードや材料の入手: 未確認。

### Autologlyph 球体（2009、作例）
- 出典: https://math.okstate.edu/people/segerman/papers/recent_3d_printed_sculptures.pdf（検索結果の要約のみ。本文取得はできず） / https://gallery.bridgesmathart.org/exhibitions/2010-bridges-conference/henrys / https://dcmpx.remotevs.com/org/segerman/www/PL/autologlyphs.html
- 何をするものか: Henry Segerman の作品。"SPHERE" の語を20回、球面にD10対称で敷き詰め、字の線を管のネットワークにして印刷した（10.4cm、SLSナイロン、Bridges gallery記載）。
- この作品にどう効くか: 「字の骨格を球面に敷き詰めてつながった殻にする」作例。字は線（管）で太さは管径、外側が元の曲面に沿うタイルとは別。字の配置は対称性を使った手作業寄りと思われる（未確認）。
- コードや材料の入手: Shapeways 販売が2013年時点（Fabbaloo https://www.fabbaloo.com/blog/2013/3/25/design-of-the-week-sphere-autologlyph.html）。現在の入手は未確認。

### Automated Typogram Generation from 3D Models（2023、学部論文）
- 出典: https://www.cg.tuwien.ac.at/research/publications/2023/rippl-2023-atg/rippl-2023-atg-.pdf （サイズ超過で本文は読めず。書誌は https://cg.tuwien.ac.at/research/publications/2023/rippl-2023-atg の検索結果から）
- 題名・著者・会議: Andreas Josef Rippl, TU Wien 学士論文, 2023年9月, 指導 Renata Georgia Raidou
- 何をするものか: 任意の3Dモデル向けに文字による造形（typogram）を作る計算機支援ワークフロー。範囲は内部ラベリング（字を形の内側に置く）に絞ると記載。
- この作品にどう効くか: 近い題材だが、内容（手法、字の変形、つながり）は未確認。
- コードや材料の入手: 論文ページに追加リンクなし。コード未確認。

### SVGnest（OSS、ツール）
- 出典: https://github.com/Jack000/SVGnest
- 何をするものか: 不規則な輪郭を容器に詰めるブラウザ上のネスティング。軌道配置と遺伝的アルゴリズムで順序と回転を最適化し、他の部品の穴にも置く。回転の候補数は指定可（4で直角のみ）。
- この作品にどう効くか: 曲面を2Dに展開した後に、字形の配置を試す部品として使える。ただし曲面の歪みと、接触してつながる条件は扱わない。
- コードや材料の入手: MIT、JavaScript、ブラウザで動く（svgnest.com）。macOSで動くかはブラウザなので問題ない見込み（未確認）。

### libigl の LSCM（等角パラメータ化、ツール）
- 出典: https://libigl.github.io/libigl-python-bindings/tut-chapter4 / https://libigl.github.io/libigl-python-bindings/igl_docs
- 何をするものか: メッシュを角度歪み最小で2Dに展開する。固定する頂点2点を指定する。Pythonでは `igl.lscm(v, f, b, bc)` の形（版により戻り値の形が違う可能性あり）。
- この作品にどう効くか: 「2Dで字を配置し、曲面に貼り戻す」自作パイプラインの土台。球は閉曲面なので切れ目か複数パッチに分ける必要がある。角度を保つので字形が崩れにくいが、面積は歪む（一般論。本調査では数値未確認）。
- コードや材料の入手: libigl（ライセンスは本調査で未確認、MPL2の可能性。要確認）。Python bindings あり。macOS対応は未確認。

### Escherization（2000、論文）と周辺
- 出典: https://history.siggraph.org/?p=118304 / https://cs.uwaterloo.ca/~csk/publications/Papers/kaplan_salesin_2004.pdf
- 題名・著者・会議: "Escherization", Craig S. Kaplan, David H. Salesin. SIGGRAPH 2000。続編 "Dihedral Escherization" (Kaplan, Salesin, Graphics Interface 2004)
- 何をするものか: 与えた閉じた図形に最も近く、平面を隙間なく敷き詰められる形を求める。
- この作品にどう効くか: 隙間なしの敷き詰めを字形で行う発想。ただし字は1種ずつ異なり、敷き詰めの前提（同じ形の反復）と合わない。参考止まり。
- コードや材料の入手: 未確認。

### From Tilings of Orientable Surfaces to Topological Interlocking Assemblies（2024、論文）
- 出典: https://mdpi.com/2076-3417/14/16/7276
- 題名・著者・会議: Akpanya, Goertzen, Niemeyer. Applied Sciences 14(16), 2024（著者名は検索要約から。詳細未確認）
- 何をするものか: 任意の向き付け可能な曲面の敷き詰めから、互いに噛み合って外れない組立体を作る。球や凸多面体への拡張がある。
- この作品にどう効くか: 「置き場所が1つに決まる」「接着なしで組み上がる」ための理論的な手がかり。字形ではなく、タイル形状の自由度も未確認。
- コードや材料の入手: 未確認。

### Image-Space Collage and Packing with Differentiable Rendering（2024、論文）
- 出典: https://arxiv.org/abs/2406.04008（プロジェクトページ https://szuviz.github.io/pixel-space-collage-technique/）
- 題名・著者・会議: Zhenyu Wang, Min Lu. arXiv:2406.04008（2024年6月、v3は2025年5月）。会議名は未確認
- 何をするものか: 微分可能レンダラで画像空間の損失を最小化して形を詰める。高速化を主張（著者の報告）。
- この作品にどう効くか: 字形を2Dに詰める最適化の近年の例。3Dは扱わない（記載なし）。展開後の2D詰め込みに応用する場合の参考。
- コードや材料の入手: arXivページにコードリンク無し。プロジェクトページ側は未確認。

## この観点の結論

### 使えそうな手段の上位3つ
1. 自作パイプライン「曲面をパッチに分けてLSCMで2Dに展開、字形を2Dで配置（SVGnest等で試行）、曲面に貼り戻して殻の厚みを付ける」。理由: 任意メッシュ向けで字形を保つ公開済みの完成品が見つからず（本調査の範囲で）、部品（libigl、SVGnest、Blender）は公開されていてmacOSで動かせる見込みがあり、既に使える環境と相性が良い。まず球で試す小規模から始められる。
2. Fabricable Tile Decors を設計の手本にする（再実装）。理由: 曲面タイル、局所的な大きさ・向きの調整、サポート無しで印刷できるパッチ分割、ヒンジ・スナップ接続まで一式の考え方が揃う。コードは未公開なので、論文を読んで必要な部分だけ真似る。
3. Segerman の autologlyph 型（字を線として球面に対称配置し、管でつなぐ）。理由: 球で動く実物の作例があり、手作業の対称配置なら任意メッシュを諦める代わりに最小の実装で済む。字の「面」ではなく線にする点は担当者の判断が要る。

### 担当者が決める必要がある点
- 字を面のタイル（外側が曲面に沿う）にするか、線の骨格にするか。面なら手本は Fabricable Tile Decors、線なら Filigrees と autologlyph。
- 配置を自動最適化にするか、球では対称性で手配置にするか。任意メッシュへの拡張を最初から狙うかも含む。
- 字形の変形をどこまで許すか（Xu & Kaplan は大変形を許すが、この作品は読める必要がある。許容する歪みの上限は担当者が決める）。
- 字の間の隙間と、接触の面積・位置の決め方（接触点を先に決めて字を置くか、字を置いてから接触を探すか）。
- 「置き場所が1つに決まる」を、形の違いだけで満たすか、噛み合い（topological interlocking の考え方）まで使うか。

### 分からなかったこと
- 字形の曲面詰め込みを、任意メッシュ向けに公開コード付きで実装した既存研究・ツール（検索範囲では未発見。検索は回数制限で一部打ち切り）。
- Fabricable Tile Decors が字形を入力にできるか、接触の保証の仕方、任意メッシュへの適用範囲（本文未読）。
- Rippl 2023 の手法の中身（PDFが大きすぎ読めず）。
- libigl のライセンスと macOS での導入しやすさ。
- 磁石を埋める接触面と詰め込み配置を同時に最適化する研究は未発見。
