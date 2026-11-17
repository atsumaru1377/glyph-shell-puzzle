# 3. 立体パズルと殻の分割の計算設計、正解を一意にする設計

調査日: 2026-11-17。出典は Web 検索と一部ページの取得で確認した範囲。取得できなかった本文は「未確認」と書く。

## 見つけたもの

### 3D Polyomino Puzzle（2009、論文）
- 出典: https://www.cse.cuhk.edu.hk/~cwfu/papers/polypuzzle/index.htm / https://dblp.org/rec/journals/tog/LoFL09
- 論文: Kui-Yip Lo, Chi-Wing Fu, Hongwei Li, "3D Polyomino Puzzle", ACM Transactions on Graphics (SIGGRAPH Asia 2009) 28(5), Article 157
- 何をするものか: 入力ソリッドを四角形メッシュでパラメータ化し、表面をポリオミノ形のタイルで敷き詰める。内側に交差しないオフセット面を作って厚い殻にし、ピースを殻に収める。ピース順の決め方は「リング順序」、動ける方向の解析は「motion space analysis」、凹凸の作り方は「tab-and-blank」と呼ばれる。著者は「組み立て可能・噛み合う・保守可能」と主張している。
- この作品にどう効くか: 「殻 + 曲面に沿うタイル + 組立順の保証」という要件に最も近い先行例。字形ピースへの置換えは論文の想定外だが、タイル形状を字形にすれば枠組みは使える見込み（私の推測）。論文本文は取得できず（アーカイブの認証で失敗）、一意性の扱いと最後のピースの入れ方の詳細は未確認。
- コードや材料の入手: プロジェクトページにコード記載なし（確認済み）。

### Chopper（2012、論文）
- 出典: https://pixl.cs.princeton.edu/pubs/Luo_2012_CPM/index.php
- 論文: Linjie Luo, Ilya Baran, Szymon Rusinkiewicz, Wojciech Matusik, "Chopper: Partitioning Models into 3D-Printable Parts", ACM TOG (SIGGRAPH Asia 2012) 31(6)
- 何をするものか: 大きなモデルを造形範囲に収まる部品に分け、「組み立てやすさ・部品数の少なさ・目立たない継ぎ目・構造強度」を最適化する。継ぎ目に専用コネクタを付けた部品を出力する。
- この作品にどう効くか: 任意メッシュを切る手順の参考になる。ただし目的は大きさの分割で、字形タイルや一意な配置は扱わない。継ぎ目の位置を目立たなくする考え方は流用できる。
- コードや材料の入手: ページにコードなし（確認済み）。公開の実装は未確認。

### PackMerger（2014、論文）
- 出典: https://diglib.eg.org/handle/10.1111/v33i6pp322-332
- 論文: J. Vanek, J. A. Garcia Galicia, B. Benes, R. Měch, N. Carr, O. Stava, G. S. Miller, "PackMerger: A 3D Print Volume Optimizer", Computer Graphics Forum 33(6), 2014, pp.322-332
- 何をするものか: 閉メッシュを中空の殻にし、殻を分割して詰め込み、サポート材と造形体積を減らす。報告値は、3機種で印刷時間5〜30%減、サポート材15〜65%減、最適化に約1分。
- この作品にどう効くか: 「中空化 → 殻の分割」の流れは同じ。字形のピース分けや一意性は扱わない。印刷向きの置き方の考えは参考になる程度。
- コードや材料の入手: 未確認。

### Dr. KID（2023、論文）
- 出典: https://arxiv.org/abs/2304.02941 （本文 https://ar5iv.labs.arxiv.org/html/2304.02941 を取得）
- 論文: Dawar Khan, Ciril Bohak, Ivan Viola, "Dr. KID: Direct Remeshing and K-set Isometric Decomposition for Scalable Physicalization of Organic Shapes", arXiv 2304.02941（IEEE TVCG 2024 掲載との情報あり。検索結果の記述で、掲載ページは未確認）
- 何をするものか: 有機的な形の表面を三角形メッシュにし、k-means とリメッシュで合同に近い三角形のピースにそろえ、法線方向に厚みを付けて殻のピースにする。ピース同士はヒンジ式コネクタで連結する。
- この作品にどう効くか: 「同じ形のピースを少数種で曲面に敷く」発想の参考。ただし三角形ピースで字形ではなく、組立順・一意性の検証は論文に記述なし（確認済み）。コネクタは樹脂(J750)印刷+金属棒で、家庭用FDMにそのまま移せるかは未確認。
- コードや材料の入手: 検索でコード公開は見つからず。著者記述では C++ 実装、Windows 10 で検証。

### On the Construction of Freeform Volumetric 3D Puzzles（2025、論文）
- 出典: https://www.mdpi.com/2673-3951/6/3/90 （検索結果の要約のみ。本文取得は403）
- 論文: Gershon Elber, Modelling 6(3), 90, 2025
- 何をするものか: 自由曲面モデル（三変数NURBS）の中にパズル要素を関数合成で埋め込み、組み立ての難しさを連続的に調整する。印刷と組立の作例あり。前作として Elber と Myung-Soo Kim による「関数合成による自由曲面の殻ジグソー」を引用している（書誌は未確認）。
- この作品にどう効くか: 曲面に沿うジグソー形状を作る別の道。NURBS前提でメッシュ入力の本作品には変換が必要。
- コードや材料の入手: 未確認。

### DESIA（2018、論文＋ツール）
- 出典: https://github.com/KIKI007/DESIA / https://infoscience.epfl.ch/record/263672
- 論文: Ziqi Wang, Peng Song, Mark Pauly, "DESIA: A General Framework for Designing Interlocking Assemblies", ACM TOG (SIGGRAPH Asia 2018)
- 何をするものか: 方向性ブロッキンググラフ(DBG)の族を使い、ボクセルの噛み合い組立を総当たりなしで探す。部品が組立順序の中で動けるかをグラフで解析する。
- この作品にどう効くか: 「最後の数ピースが入るか」「噛み合い（動けなさ）」を調べる考え方の出典。ただしボクセル立方体向けで、曲面殻や任意メッシュには直接使えない。ブロッキンググラフ自体は一般の形状に応用できる概念。
- コードや材料の入手: MIT ライセンス、C++17 + CMake + Boost、macOS対応(Xcode 11.5以上)。独自形式 .puz。

### Computational design of high-level interlocking puzzles / Recursive interlocking puzzles（2022 / 2012、論文）
- 出典: https://history.siggraph.org/?p=117924 / https://history.siggraph.org/?p=207956
- 論文: Ziqi Wang, Peng Song, Bernd Bickel, "Computational design of high-level interlocking puzzles"（年は2022頃、会議名は未確認）。Peng Song, Chi-Wing Fu, Daniel Cohen-Or, "Recursive interlocking puzzles", ACM TOG (SIGGRAPH Asia 2012)
- 何をするものか: ピースを1つずつ動かさないと外れない噛み合いパズルの生成。組立順序の長さ（難しさ）を定義する。
- この作品にどう効くか: 組立順序が一意になる条件の定式化の参考。本作品は噛み合いより磁石接続が第一候補なので、使うとすれば「外れない構造」にしたい場合の発想。
- コードや材料の入手: 未確認。

### Masonry Shell Structures with Discrete Equivalence Classes（2023、論文＋ツール）
- 出典: https://github.com/Linsanity81/TileableShell / https://sutd-cgl.github.io/supp/Publication/projects/2023-SIGGRAPH-TileableShell/index.html
- 論文: Rulin Chen, Pengyun Qiu, Peng Song, Bailin Deng, Ziqi Wang, Ying He, ACM TOG 42(4), Article 115, 2023（SIGGRAPH 2023）
- 何をするものか: 開境界の多角形曲面を、少数種のテンプレート要素で継ぎ目なく覆い、組立可能性まで誤差指標で評価する。階層的クラスタリング + 最適化で要素種を絞る。
- この作品にどう効くか: 「少数種のタイルで曲面を覆う」という目的が近い。ただし対象は開いた曲面（閉じた殻ではない）で、建築の組積構造向け。字形は扱わない。
- コードや材料の入手: MIT ライセンス（商用は要相談）、C++、CMake、libigl。macOSとUbuntu対応、テスト環境はUbuntu。

### Ravensburger Puzzleball（製品）
- 出典: https://www.ravensburger.co.uk/en-GB/products/3d-puzzles/3d-puzzle-balls
- 何をするものか: 球状に曲がったプラスチック製ジグソーピースをのり無しではめて球にする。72/108/180/540ピース、直径約13〜22cm（販売ページの記述）。裏面に番号がある。
- この作品にどう効くか: 製品としての先例。ただしロック機構や一意性の設計手法は公開情報から確認できず（未確認）。
- コードや材料の入手: なし。

### 一意性の確認方法（厳密カバー問題 + DLX）（技術、一般論）
- 出典: https://shreevatsa.github.io/knuth-literate-programs/programs/dlx3.pdf （Knuth の DLX3 の注釈付き資料）
- 何をするものか: 「置き方の候補」を行、「殻上の領域」を列にした厳密カバー問題にし、DLXで解を数える。解を2つ探して1つしか出なければ一意、という使い方が一般的に知られている。
- この作品にどう効くか: 字形ピースの敷き詰めの一意性は、候補配置を列挙してこの形で検証できると考えられる。ただし「球面向けにこの設定で検証した文献」は見つからなかった。以下は私の設計案で、出典はない: 領域をセル（例: 球を分けた小片）に分け、ピースの配置・向き・反転を行にする。磁石の極性まで含める場合は、極が合わない配置を行から除く。
- コードや材料の入手: DLXは公開実装が多数ある。具体的なURLは未確認。

### 磁石の極性による配置制約（参考）
- 出典: https://groups.csail.mit.edu/hcie/files/research-projects/mixels/mixels.pdf （Mixels、UIST 2022）
- 何をするものか: 磁気ピクセルのパターンで、特定の組み合わせだけ引き合い、他は反発する。見た目が同じ物同士の選択的な組み合わせを可能にする。
- この作品にどう効くか: 極の割付で配置を一意にする発想の参考。ピース数が増えると極の組み合わせが足りなくなるかは未確認。本作品の設計に必要な数値（磁石径・保持力）は他の担当の調査に任せる。
- コードや材料の入手: 未確認。

### 調べて見つからなかったもの
- 字形ピースで球面を敷く作例: 検索で見つからず（フラットな文字タイルしか出なかった）。
- Chopper、3D Polyomino Puzzle、Dr. KID の公開コード: 見つからず。

## この観点の結論

### 使えそうな手段の上位3つ
1. 自作パイプライン（Python + Blender、必要なら libigl）で作り、検証を DLX で行う。理由: 字形タイルの曲面敷き詰めに合う公開コードが見つからず、既存論文はどれも対象が違う（ポリオミノ、三角形、建築の開曲面）。表面の領域分割、殻化、字形の貼り付け、一意性の検証は個別には単純で、まず球で試せる。
2. 3D Polyomino Puzzle（Lo, Fu, Li 2009）を設計の骨格として読む。理由: 殻、曲面タイル、組立順序の保証を一続きで扱った唯一の先例。タイルをポリオミノから字形へ替える案が成り立つかの判断材料になる。本文は未確認なので、ACM DL か著者から入手して読む必要がある。
3. DESIA（MIT、macOS対応）のブロッキンググラフの考え方で組立可能性を確かめる。理由: 「どのピースがどの方向に動けるか」を調べる枠組みで、最後の数ピースが入るかの検証に応用できる。ただしコードはボクセル向けで、直接は使えない。

補足（私の推論、出典なし）: 殻の厚み方向に接合面を傾ける（外側が広く、内側が狭い形）と、各ピースは外側から1方向に入るので、最後のピースの挿入可否は「接合面にアンダーカットがないか」の確認に絞れる。磁石接続だけなら噛み合いの検証は不要になる。これは設計案で、検証されたものではない。

### 担当者が決める必要がある点
- 一意性の範囲: (a) 字形・向き・位置が全部一意 / (b) 位置だけ一意で、同じ字形は入れ替え可 / (c) 磁石の極性で強制する。(a)は字形の重複を避ければ検証が楽。(c)は磁石の極性の数で上限が決まる。
- 組立の担保: (a) 磁石のみで保持し、接合面は傾けて外側から入れる / (b) 噛み合いも持たせる（DESIA 系の解析が要る）。
- 最後のピースの扱い: (a) 閉じた殻にして最後の1〜数ピースは外から押し込む / (b) 殻に開口（蓋）を作る。
- 隙間の許容: 字と字の間の隙間をどこまで許すか（面積比や最大幅）。
- 論文本文を取りに行くか（ACM DL、著者）。

### 分からなかったこと
- 3D Polyomino Puzzle の本文詳細（一意性、最後のピースの入れ方、殻の厚み、数値）。
- Ravensburger の設計手法。
- Chopper・3D Polyomino Puzzle・Dr. KID・Elber の公開コードの有無（見つからなかったが、無いと断定はできない）。
- 字形タイルを閉曲面に敷いた作例。
- 球面向けの一意性検証の既存手法。
