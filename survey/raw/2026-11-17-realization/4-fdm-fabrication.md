# 観点4: 家庭用FDMでの製造上の事実（調査日 2026-11-17）

注記: 出典のうち「WebSearch要約のみ」は検索結果の要約で確認しただけで、ページ本文は読んでいない。「本文確認」は取得して読んだもの。

## 見つけたもの

### CNC Kitchen「Conical Slicing」（記事、種類: 記事/ツール）
- 出典: https://www.cnckitchen.com/blog/conical-slicing-a-different-angle-of-3d-printing （本文確認）
- 何をするものか: STLを逆円錐状に変形してから通常のスライサーで切り、G-codeを逆変換して、層を円錐状に傾けて印刷する。3軸機で動く。ZHAW RotBotのPythonスクリプトを使う。
- この作品にどう効くか: 球の殻ならサポート無しで印刷できる可能性がある。ただし手作業が多く不安定。内向き張り出しと外向き張り出しが同じ高さにあると解がない。ピースが多い本作品では、1枚ずつ手作業で処理するのは非現実的。小さなタイルには過剰で、通常の平面印刷+向きの工夫で足りる可能性が高い。

### QuickCurve（2024、種類: 論文）
- 出典: https://arxiv.org/abs/2406.03966 （本文確認。Ottonello, Hugron, Parmiggiani, Lefebvre, "QuickCurve: revisiting slightly non-planar 3D printing", arXiv cs.GR 2024。会議・雑誌名は未確認）
- 何をするものか: 曲がったスライス面を最適化し、上面を再現する非平面の積層経路を作る。3軸のFFFで衝突を避ける。平面層との混在も可能。
- この作品にどう効くか: 曲面タイルの外側の階段状の段差を減らす用途に合う。ただし実装が公開されていても、一般スライサーのプラグインではない（本調査では配布形態を未確認）。家庭用で日常的に使える段階かは未確認。

### CurviSlicer（2019、種類: 論文/ツール）
- 出典: https://cims.nyu.edu/gcl/papers/2019-CurviSlicer.pdf 、実装 https://github.com/mfx-inria/curvislicer （GitHubはWebSearch要約のみ）。Etienne, Ray, Panozzo, Lefebvre 他、SIGGRAPH 2019（著者・会議は私の記憶。PDF本文では未確認）
- 何をするものか: モデルを変形して通常のスライスを行い、経路を元の形へ写す。ノズル衝突を制約に入れる。
- この作品にどう効くか: 曲面の殻の表面品質には効く可能性。CLIツールで、Curaのプラグインではない（UltiMakerフォーラムの開発者回答、WebSearch要約のみ）。

### Prusa「Insert pause or custom G-code at layer」（公式文書）
- 出典: https://help.prusa3d.com/article/insert-pause-or-custom-g-code-at-layer_120490 （本文確認）
- 何をするものか: PrusaSlicerのレイヤースライダーから、指定層の前に一時停止（M601）を入れる。
- この作品にどう効くか: 磁石埋め込みの標準手順。磁石が緩いとヘッドに貼り付くので、きつめの穴か瞬間接着剤の少量で固定せよとある。許容値の数値は書かれていない。逐次印刷（Sequential printing）では使えない。MK3系はファームウェア3.9.1以上が必要。

### Printables「Embedded Magnets Negative Volume Generator for PrusaSlicer」（作例/ツール）
- 出典: https://www.printables.com/model/222274-embedded-magnets-negative-volume-generator-for-pru （ページ取得に失敗。WebSearch要約のみ）
- 何をするものか: 円柱磁石用の穴をネガティブボリュームとして作る。
- この作品にどう効くか: 磁石穴の形状を手で作る手間を減らせるが、ピース数が多いなら自作スクリプトで穴をCADから生成する方が現実的。値は未確認。

### PrintPal「3D Puzzle Maker」（製品/ツール）
- 出典: https://printpal.io/tools/puzzle-maker （本文確認）
- 何をするものか: メッシュを分割するパズル生成。推奨クリアランスは既定0.40 mm、FDMで0.2〜0.5 mm（ページ内で記述が割れている）。
- この作品にどう効くか: 隙間の目安として使える。ただし同ページ内で0.2〜0.4、0.25〜0.35、0.3〜0.5と食い違い、一次情報ではない。必ず自機で試す。切断面を印刷ベッドに平らに置く、壁3周、層高0.16〜0.20 mmの助言は参考になる。

### Hubs「How to design snap-fit joints for 3D printing」（公式的な設計ガイド）
- 出典: https://www.hubs.com/knowledge-base/how-design-snap-fit-joints-3d-printing/ （本文確認）
- 何をするものか: スナップフィットの設計指針。FDMの公称クリアランスを0.5 mmと記載。
- この作品にどう効くか: スナップを接続の候補にするなら、クリアランスは0.5 mmから始める目安。ただし磁石案や小さな接触面には大きすぎる値の可能性がある。クリップ幅の最小5 mmは、小さな接触面と両立しない。

### Hubs「Key design considerations for 3D printing」（設計ガイド）
- 出典: https://www.hubs.com/knowledge-base/key-design-considerations-3d-printing/ （本文確認）
- 何をするものか: FDMの最小肉厚0.8 mm、張り出し約45度などの設計規則。
- この作品にどう効くか: 厚さ数mmの殻なら肉厚は足りる。字形の細い線は0.8 mm以上を目安に設計。45度超の張り出しはサポートが要る。

### PrusaSlicer「Arachne perimeter generator」「Layers and perimeters」（公式文書）
- 出典: https://help.prusa3d.com/article/arachne-perimeter-generator_352769 、https://help.prusa3d.com/en/article/layers-and-perimeters_1748 （前者は本文確認、後者はWebSearch要約）
- 何をするものか: Arachneは壁の幅を可変にして細い形を印刷する。最小形状サイズ未満の壁は印刷されない。Classic+Detect thin wallsでも、押出幅より薄い壁は無視されやすい。
- この作品にどう効くか: 字形の細い画の再現に直結。Arachneの既定値は文書に書かれておらず、未確認（自分のプロファイルで確認が必要）。

### K&J Magnetics「仕様と公差」（製品仕様）
- 出典: https://www.kjmagnetics.com/specs.asp 、ディスクの例 https://kjmagnetics.com/proddetail.asp?prod=DB01 （WebSearch要約のみ。specs.aspは本文未確認）
- 何をするものか: ネオジム磁石の寸法公差は±0.1 mm（DB01の記載）。他社は±0.05〜±0.2 mm（Magfine、Indigo Instruments）。N35の最高使用温度は80度（Arnold、Goudsmit）。
- この作品にどう効くか: 磁石穴の余裕は、磁石の公差とプリンタの穴の縮みの合計を見込む必要がある。PLA部品は80度未満なので普通は問題ないが、ベッド温度や車内放置に注意。

### 磁石埋め込みの作例（フォーラム）
- 出典: https://forum.prusa3d.com/forum/how-do-i-print-this-printing-help/how-to-safely-insert-magnets-into-a-print 、https://forum.bambulab.com/t/dealing-with-magnets-glued-in/96743 （WebSearch要約のみ）
- 何をするものか: 実測した磁石径に0.1〜0.3 mmの余裕を足した穴を作り、蓋になる層の直前で止めて入れる。
- この作品にどう効くか: 数値の実例。一次情報ではなく個人の経験則。複数個を同時に印刷すると、磁石同士が引き合って印刷物がベッドから剥がれる事例が報告されている（要約のみ）。

### 公差の積み上げ（参考）
- 出典: 検索では3Dプリントに特化した出典は見つからなかった。一般的な公差の累積の講義資料 https://gab.wallawalla.edu/~ralph.stirling/classes/engr480/lectures/2003/lecture3_2003apr4.pdf （WebSearch要約のみ）
- 何をするものか: 隙間は部品寸法の加減で決まり、最悪値は接合が増えるほど累積する。
- この作品にどう効くか: 殻が閉じない問題は、接触ごとの誤差が周方向に足し合わされる。3Dプリント向けの実測値は未確認。小さな試験片で自機の収縮・穴の縮みを測り、モデル側で補正するのが実務的な助言（出典: 3dprinterly https://3dprinterly.com/pla-abs-petg-shrinkage-compensation-in-3d-printing/ 、WebSearch要約のみ）。

## 数値の目安（表）

| 項目 | 値 | 出典 |
|---|---|---|
| FDMの最小肉厚（全プリンタで印刷可能） | 0.8 mm超 | Hubs https://www.hubs.com/knowledge-base/key-design-considerations-3d-printing/ |
| 押出幅（0.4 mmノズル、Prusa既定付近） | 約0.45 mm（フォーラム記述） | https://forum.prusaprinters.org/forum/original-prusa-i3-mk3s-mk3-how-do-i-print-this-printing-help/gaps-in-printing-walls/ （要約のみ） |
| 0.4 mm壁は0.4 mmノズルの既定設定では不可 | 押出幅より薄い壁は無視される | PrusaSlicer文書 https://help.prusa3d.com/en/article/layers-and-perimeters_1748 |
| Arachneの最小形状サイズ・最小壁幅の既定値 | 未確認（文書に記載なし） | https://help.prusa3d.com/article/arachne-perimeter-generator_352769 |
| 張り出し角（サポート不要の限界） | 約45度 | Hubs（上記）、PrusaSlicer既定45度 |
| 層高の目安（0.4 mmノズル） | 最小約0.08、最大約0.28 mm（ノズル径の約75%）。経験則 | https://www.obico.io/blog/orca-slicer-adaptive-and-variable-layer-height-guide-smoother-3d-prints/ 等（要約のみ。公式文書では確認できず） |
| パズル用クリアランス（FDM） | 既定0.40 mm、範囲0.2〜0.5 mm | PrintPal https://printpal.io/tools/puzzle-maker |
| スナップフィットの公称クリアランス（FDM） | 0.5 mm | Hubs https://www.hubs.com/knowledge-base/how-design-snap-fit-joints-3d-printing/ |
| スナップフィットのクリアランス（PLA/PETG） | 0.2〜0.3 mm（ベンダーブログ） | https://qidi3d.com/blogs/print-lab/3d-printed-snap-fit-joints-clearance-guide （要約のみ） |
| 圧入に近いはめ合い | 0.0〜0.1 mm（Bambu向けガイド） | 上記検索結果の要約のみ。単一出典で弱い |
| 磁石穴の余裕 | 磁石の径・高さに各+0.1〜0.3 mm。例: 10×3 mm磁石に10.3×3.1 mmの穴 | Prusaフォーラム、Bambuフォーラム（要約のみ。経験則） |
| 磁石の蓋層 | 穴を磁石より約0.4 mm深くし、磁石の上を覆う層の直前で停止 | Bambuフォーラム等（要約のみ） |
| ネオジム磁石の寸法公差 | ±0.1 mm（K&J、Magfine小径）、±0.05〜0.2 mm（他社） | https://kjmagnetics.com/proddetail.asp?prod=DB01 等 |
| N35磁石の最高使用温度 | 80度（長期は60〜70度が無難との意見あり） | Arnold https://www.arnoldmagnetics.com/wp-content/uploads/2017/11/N35-151021.pdf 等（要約のみ） |
| PLAの収縮 | 0.2〜3%と出典で幅がある。方向で異なる。穴は約0.2 mm小さくなる例 | 3dprinterly、Prusaフォーラム（要約のみ） |
| 円錐スライスの傾き | 小物で16〜20度。印刷速度は周壁15 mm/s、内部25 mm/s | CNC Kitchen（本文確認） |
| 平面スライスで出せる最小の張り出し | 水平から約10〜15度未満はたれる | CNC Kitchen（本文確認） |
| 多数ピースの印刷時間・ベッド配置 | 未確認 | － |

## この観点の結論

### 使えそうな手段の上位3つ
1. 通常の平面印刷で、曲面タイルを凹面または凸面を上にして置き、サポートを使うか、層高を小さく（可変層高）して階段状の段差を許容する。理由: 設備を足さずに済み、ピース数が多くても自動化できる。ただし、この点に直接答える一次情報は見つけられず、推奨できる向きは未確認。実際に試作して決める必要がある。
2. 磁石は、穴を磁石寸法+0.1〜0.3 mmで作り、蓋の層の直前にPrusaSlicerのM601で停止して入れる。理由: 公式文書に手順があり、経験則の数値も複数ある。ただし停止回数がピース数×磁石数になる。ピースを小さく平らにして1枚の板に並べれば、全ピースの停止層を揃えられる可能性がある（本調査では確認していない）。
3. 小さな試験片（隣接2〜3ピース）を先に印刷し、クリアランスと穴の縮みを実測してからモデル側で補正する。理由: 出典ごとに0.2〜0.5 mmと値が割れており、積み上げの影響を机上で見積もれない。

非平面印刷（円錐スライス、CurviSlicer、QuickCurve）は、まず球1個の試作では使わない方がよいと考える。手作業が多く、家庭用での定常運用は未確認。

### 担当者が決める必要がある点（選択肢）
- 接続方式: (a) 磁石を埋める（停止作業あり、公差の余裕0.1〜0.3 mm）、(b) FDMだけのスナップ/はめ込み（クリアランス0.2〜0.5 mm、接触面が小さいと壊れやすいおそれ）、(c) 両方を試作して比較。
- 印刷の向き: (a) 曲面を上にして階段状の段差を受け入れ、後処理で仕上げる、(b) サポートを使う、(c) 非平面印刷に挑戦する。
- 磁石の停止作業: (a) 全ピースの停止層を揃えて一括で入れる、(b) 磁石を後から接着で入れる（停止不要、接着強度の確認が要る）。
- 殻の厚さと肉厚: 字形の細い画の最小幅をいくつにするか（0.8 mmを下限の目安にするか）。

### 分からなかったこと
- 曲面タイルの印刷向きと階段状の段差の定量比較（一次情報なし）。
- 多数ピースの印刷時間の目安、ベッド配置の効率化の公的な事例。
- 公差の積み上げで殻が閉じなくなる問題の、3Dプリント特化の数値と対策の文献。
- Arachneの最小形状サイズ・最小壁幅の既定値。
- Printables磁石ジェネレータの穴の余裕の具体値（ページ取得失敗）。
- 非平面印刷の家庭用での実用性の一次情報（QuickCurveの配布形態と対応機種、CurviSlicerの実機での成功率）。
