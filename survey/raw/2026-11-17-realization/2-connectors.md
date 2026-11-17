# 2. ピースのつなぎ方（磁石・印刷できる継手・正解の一意性）

調査日: 2026-11-17。「未確認」は一次情報で裏が取れなかった項目。

## 見つけたもの

### K&J Magnetics 小型ネオジム円盤の仕様（製品、仕様ページ）
- 出典: https://www.kjmagnetics.com/d201-neodymium-disc-magnet , https://www.kjmagnetics.com/d301-n52-neodymium-disc-magnet , https://www.kjmagnetics.com/d203-neodymium-disc-magnet , https://www.kjmagnetics.com/d32-neodymium-disc-magnet （D32ページの「Similar Products」表に全サイズのCase 1がある）
- 何をするものか: 小型ディスク磁石の公称吸着力（Case 1 = 厚い鋼板への垂直引き剥がし力）。数値（lb、括弧内は kg 換算の公表値）:

| 型番 | 直径 x 厚さ | 等級 | Case 1 | 表面磁束密度 |
|---|---|---|---|---|
| D101-N52 | 1.59 x 0.79 mm | N52 | 0.07 lb | 未取得 |
| D201 | 3.17 x 0.79 mm | N42 | 0.2 lb (0.09 kg) | 2952 G |
| D201-N52 | 3.17 x 0.79 mm | N52 | 0.25 lb（D32表。D201ページ本体では未確認） | 未取得 |
| D21 | 3.17 x 1.59 mm | N42 | 0.45 lb | 未取得 |
| D203 | 3.17 x 2.38 mm | N42 | 0.6 lb (0.27 kg) | 5492 G |
| D22 | 3.17 x 3.17 mm | N42 | 0.68 lb | 未取得 |
| D301-N52 | 4.76 x 0.79 mm | N52 | 0.43 lb (0.2 kg) | 2340 G |
| D32 | 4.76 x 3.17 mm | N42 | 1.37 lb (0.62 kg) | 5280 G |
| D401 | 6.35 x 0.79 mm | N42 | 0.53 lb | 未取得 |
| D41 | 6.35 x 1.59 mm | N42 | 1.19 lb | 未取得 |

  - D201のCase 2（両側が鋼板）は 0.84 lb (0.38 kg)。最高使用温度 80 °C（176 °F）。
  - 価格: D201 N42 の10個入り $1.08（数量1〜99）、D203 10個入り $1.68、D32 は1個 $0.30。
- この作品にどう効くか: 直径3〜5 mm・厚さ1〜3 mm の範囲だと、鋼板に対する吸着力は 0.1〜0.6 kg 程度（約 0.9〜6 N）。このカタログ値は磁石1個と鋼板の値で、磁石どうしの吸着や、間に樹脂が入った場合の値ではない。磁石どうし（Case 3）の値はページ上の図にあり、今回は数値を取れていない（未確認）。軽い殻のタイル同士の保持には十分な桁と考えられるが、これは推測で、試作で測る必要がある。
- 材料の入手: 上記K&J（米国）。日本では供給元は未確認。

### supermagnete（メートル系）の小型円盤の仕様（製品、仕様ページ）
- 出典: https://www.supermagnete.de/eng/disc-magnets-neodymium/disc-magnet-4mm-2mm_S-04-02-N , https://www.supermagnete.ch/eng/adhesive-force-calculation , https://www.supermagnete.de/eng/catalog.pdf , https://www.supermagnete.se/eng/disc-magnets-neodymium/disc-magnet-5mm-3mm_S-05-03-N
- 何をするものか: メートル規格の小型円盤磁石。S-03-01-N（Φ3 x 1 mm, N48）は約190 g、S-04-02-N（Φ4 x 2 mm, N45）は約420 g、S-05-03-N（Φ5 x 3 mm, N42）は約700 g。最高使用温度 80 °C。
- この作品にどう効くか: Φ4 x 2 mm が殻の厚さ数mmに収まる寸法。同一の S-04-02-N について、製品ページは約420 g、同社の「吸着力計算」ページは約250 g と食い違う。測定条件は両ページから読み取れていない（未確認）。数値は幅で見て、実測で決める。
- 材料の入手: supermagnete各国サイト。価格は未確認。

### FDM造形物への磁石の埋め込み手順（記事・作例）
- 出典: https://makerworld.com/en/community/post/968465 （検索結果の抜粋のみ。直接の取得は403で失敗） , https://makerworld.com/en/community/post/1001494 , https://www.kabk.nl/en/lectorates/design/3d-printed-magnet-embedding-courteney-reitz-graduate-2021-bachelor-interior-architecture-furniture-design , https://forum.bambulab.com/t/perfect-flush-magnet-fit/205491
- 何をするものか: ポケットを造形して、天井層の手前で一時停止し、磁石を入れて再開し、上から塗り込めて封じる方法。記事に出る数値は次のとおり。
  - ポケット径は磁石径に +0.2〜0.3 mm（例: Φ3 磁石に Φ3.3 mm の穴、深さ 1.8 mm）。きついと割れる。縮みで穴が小さくなることもあるので、0.05〜0.1 mm 広げる調整例もある。
  - 深さは磁石の厚さに合わせ、たるみ対策に1層ほど足す、という例がある。再開後は、磁石の上が2層覆われるまで見張る。
  - 接着は瞬間接着剤か高粘度品（Loctite 416、3M PR100）。入れる磁石は1個ずつ。床に近い位置に置いた磁石どうしが引き合って、造形物がプレートから剥がれることがある。
  - 磁石の頭が出たまま再開するとノズルが衝突する。
- この作品にどう効くか: 殻は曲面で、接触面の向きが場所ごとに違う。ポケットを造形方向にそろえる配置と、一時停止の層をピースごとに決める設計が要る。ここは推測。曲面に沿った接触面を水平にして印刷するかどうかは、他の観点（分割・向き）の結果と合わせて決める。出典は個人の記事と作例で、検証データではない。
- 材料の入手: 磁石は上の製品。無償のスライサー機能（Bambu Studio、PrusaSlicer の一時停止）で足りる。

### Mixels: Fabricating Interfaces using Programmable Magnetic Pixels（2022、論文）
- 出典: https://arxiv.org/abs/2208.03804 （論文PDF） , https://hcie.csail.mit.edu/research/mixels/mixels.html （プロジェクトページ）
- 著者・会議: Martin Nisser, Yashaswini Makaram, Lucian Covarrubias, Amadou Bah, Faraz Faruqi, Ryo Suzuki, Stefanie Mueller。UIST 2022（ACM DOI 10.1145/3526113.3545698）。
- 何をするものか: 軟磁性シートに、電磁石ヘッド付きの3軸CNCで磁気ピクセルを書き込む。ピクセルは N / S / 消磁を選べ、ペアの面どうしだけが吸着し、他の組とは吸着も反発もしない（「無関心」）よう、ハダマード行列の置換から選ぶ。
- この作品にどう効くか: 本文に「文字が正しい隣の文字にだけつながる」例（Fig. 12、4個のブロックで UIST の語になる）がある。目的とほぼ同じ発想。ただし、磁気プロッタ用のCNCヘッドの製作が前提で、家庭用FDMだけでは再現できない。市販磁石で似たことをする場合は、下の「Selective Self-Assembly」の符号の考え方だけ借りられる。ピクセル幅は3 mm（コアは3 mm 幅、本文）。
- コードや材料の入手: arXivで論文公開。UIは論文で説明されているが、公開コードのURLは未確認。シートは $0.008/cm2（論文本文）。

### Selective Self-Assembly using Re-Programmable Magnetic Pixels（2022、論文）
- 出典: https://arxiv.org/abs/2208.03799 、https://hcie.csail.mit.edu/research/selective/selective.html
- 著者・会議: Martin Nisser, Yashaswini Makaram, Faraz Faruqi, Ryo Suzuki, Stefanie Mueller。IROS 2022。
- 何をするものか: 立方体の面に磁気ピクセルの符号を書き込み、意図した相手の面だけを強く吸着させ、他の面とはどの位置・回転でも吸着しないようにする。符号の数（本文より）:
  - 4x4 の ±1 行列は 2^16 = 65,536 通り。そのうちハダマード行列は 768 個（1.2%）。
  - 互いに混ざらない（相互に無関心な）符号の最大の組（クリーク）は、位置・回転を含めた最悪の吸着値が -0.36 で 12 個。このときの完全な無関心（0）は得られていない。
  - 8x8 の探索や、回転を 0/90/180/270° に限った計算など、計算の上限が本文にある。
  - 立方体は25 mm、PLA製、面に26 mil厚の軟磁性シートを貼る（市販の冷蔵庫用マグネットシート）。
- この作品にどう効くか: 「4x4 の磁気ピクセルなら、混ざらない符号は12組程度、ただし完全には無関心にならない」という数値が、極性の並びで区別できる組み合わせの数の目安になる。直径3 mm の磁石を使う場合、4x4 配置は約16 mm 角が要る（3 mm x 4 + 間隔）。これは寸法からの計算で、出典に直接の記載はない。軟磁性シートに書き込む方式なので、そのままは使えない。
- コードや材料の入手: 論文のみ。コードは未確認。

### Magnetically Controlled Modular Cubes with Reconfigurable Self-Assembly and Disassembly（2021、論文）
- 出典: https://arxiv.org/abs/2107.10167 、https://par.nsf.gov/servlets/purl/10381786
- 著者・雑誌: Anuruddha Bhattacharjee, Yitong Lu, Aaron T. Becker, MinJun Kim。IEEE Transactions on Robotics（DOI 10.1109/tro.2021.3114607）。年は検索結果の記載から2021とした（雑誌の巻号は未確認）。
- 何をするものか: 3Dプリントした立方体に永久磁石を埋め込み、各面の極（N/S）で結合しやすさを決め、外部の一様磁場で組み立て・分解する。
- この作品にどう効くか: 極性の違いだけで「つながる相手」を決める例。ただし1面に磁石1個の符号は2通りで、一意な正解を作るには足りない。作例はロボット向けで、パズルの設計には直接使えない（μm級のSLA造形が前提の例もある）。
- コードや材料の入手: 論文のみ。

### 極性符号の組み合わせ数の数え方（鍵と錠の特許・百科事典、参考）
- 出典: https://en.wikipedia.org/wiki/Magnetic_keyed_lock 、https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/4562711 、https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8872608 （Correlated Magnetics の符号特許）
- 何をするものか: 磁石 n 個を2極性で並べると 2^n 通り。Wikipedia は「組み合わせ数 = C x 4^m」（m は磁石ペア数）の式を載せるが、同ページは「citation needed」とされている。Correlated Magnetics のバーカー符号の特許は、鏡像の符号を対にして、位置が合ったときだけ吸着力のピークを作る。
- この作品にどう効くか: 接触面ごとに磁石 n 個、互いに補の並び（N と S を反転）を相手に置けば、並びが違う相手とは「一部は引き合い、一部は反発して合力が小さい」になる。ただし、並びの違いが1個だけだと、合力は正解の相手に近く、誤接続を弾けない。誤接続の合力を下げるには、符号どうしの距離（異なるビット数）を大きく取る必要がある。これは上の論文の考え方を適用した私の整理で、数値は未検証。n と 2^n の関係は計算で、出典は式の例のみ。
- コードや材料の入手: 特許は公開情報。実装の公開コードは未確認。

### 磁石の極性を使った3Dプリントパズル（作例）
- 出典: https://thangs.com/m/972920 （Force Field Puzzle）、https://makerworld.com/models/2900368 （MagTetra）、https://makerworld.com/models/680441 、https://www.myminifactory.com/object/3d-print-low-poly-dog-magnetic-3d-puzzle-749108
- 何をするものか: 磁石ポケットの極性を図や刻印で指定し、正しい向きでだけ組み上がるようにするパズル。Force Field Puzzle は N52 のΦ3 x 6 mm、5x2 mm や 4x2 mm の小型円盤を使う作例が多い（検索結果の記載）。
- この作品にどう効くか: 「全ピースを同じ手順で組み、極性が違えば反発する」という動作が、市販磁石と家庭用FDMだけで再現できる実績。極性の向き違いは組む人が気づきにくいため、ポケットに刻印を入れる作例がある。ライセンスが制限付きのものがあり、コードや形状の流用は不可（Thangsのページに「restricted」の記載）。
- コードや材料の入手: 各ページの配布。流用は各ライセンスの確認が必要（未確認）。

### 球面ジグソーの作例（Ravensburger Puzzleball、3Dプリントの球パズル）（製品・作例）
- 出典: https://ravensburger.us/en-US/products/3d-puzzles/3d-puzzle-balls 、https://makerworld.com/en/models/3058738-pixelated-sphere-puzzle 、https://blog.kenperlin.com/?p=7375
- 何をするものか: Puzzleball は曲面プラスチックピースが接着なしで噛み合う。72ピースで直径13 cm、108ピースで15 cm。プリント向けでは、10ピースの球パズル（MakerWorld）がある。
- この作品にどう効くか: ピース形状で一意にする案の参考。Puzzleball の内部の継手（タブ）の寸法は、今回の調査では取れていない（未確認）。MakerWorld の球パズルは、噛み合う張り出しに支持材が要るとされる。Ken Perlin のブログは、球面ジグソーは緯度経度の格子で作られ、極に近いほどピースが小さくなると述べる。字形ピースの敷き詰めには別の分割が要る。
- コードや材料の入手: 製品は市販。MakerWorld のモデルは共有・販売が制限される（ページの記載）。

### FDM向けスナップフィット・蟻継ぎの寸法ガイド（記事）
- 出典: https://www.hubs.com/knowledge-base/how-design-snap-fit-joints-3d-printing 、https://qidi3d.com/blogs/print-lab/3d-printed-snap-fit-joints-clearance-guide 、https://www.sovol3d.com/blogs/news/3d-printed-snap-fit-joints-how-to-design-clips-that-work
- 何をするものか: Hubs は、片持ちの根元に厚さの0.5倍以上のR、幅は5 mm以上、先端に向けてテーパ、FDMの公称クリアランスは0.5 mm。Z方向に立てた片持ちは層間強度のため避ける。ABS・ナイロン・TPU が向く。QIDI系の記事は、PLA/PETG で 0.2〜0.3 mm、摺動の蟻継ぎで片側 0.2〜0.3 mm（0.2 mm 未満は摩擦が急増）、片持ちの長さは厚さの4〜10倍。
- この作品にどう効くか: 殻の厚さ数 mm、かつ字形の接触面が小さい条件では、幅5 mm 以上の片持ち（Hubs の推奨）を入れられるかが怪しい。蟻継ぎは曲面タイルの横から差し込む方向を一意にできるが、数値は記事ごとに食い違い、ベンダの記事で検証は少ない。試し刷りで決めるべき項目。
- コードや材料の入手: 記事のみ。

### 空隙による吸着力の低下（記事・メーカー解説）
- 出典: https://www.kjmagnetics.com/blog/how-much-will-a-magnet-hold 、https://www.kjmagnetics.com/faq.asp 、https://totalelement.com/blogs/about-neodymium-magnets/how-air-gaps-impact-magnet-strength
- 何をするものか: 磁石と相手の間の隙間は樹脂でも吸着力を下げる。K&J の各製品ページに、距離ごとの Case 1〜3 の吸着力の曲線がある。
- この作品にどう効くか: 磁石をポケットに入れて天井層で封じると、接触面との間に樹脂が0.4〜1 mm 残る。この分の低下は、カタログ値の数分の一になりうる。ただし具体的な数値は、K&J の曲線を読んでいないため未確認。設計上は、磁石を接触面にほぼ露出（薄い樹脂の膜）にするか、封じずに接着する案と、保持力を実測する案を比べる必要がある。

## この観点の結論

### 使えそうな手段の上位3つ
1. 磁石 + 形状の併用（磁石は保持と極性による誤接続の防止、形状は位置決めと一意化）。理由: 磁石だけでは、1つの接触面に入る磁石が1〜2個のため、極性の符号は2〜4通りで区別が足りない。ジグソー状の位置決めの形（凸凹や段差）を併用すれば、符号の弱さを形状で補える。Mixels と Selective Self-Assembly が示すとおり、混ざらない符号を12組取るには4x4 程度のピクセル配置が要り、接触面が小さい本作品では物理的に入らない見込み。
2. 極性（N/S）による誤接続の排除。理由: 向きを間違えると反発する作例（MagTetra、Force Field Puzzle）が、市販の小型円盤磁石と家庭用FDMで既に成立している。ポケットへの極性の刻印と、一時停止での埋め込み（ポケット径 +0.2〜0.3 mm）という作り方も公開されている。ピースの数が少なければ、磁石 2〜3個の極性の並びで隣接ごとの一意性を取れる可能性がある。ただし、並びの違いが1個だと誤接続の合力が小さくならないため、設計で確かめる必要がある。
3. 印刷できる機械的な継手（蟻継ぎ、スナップ）を主、磁石を補助にする案。理由: 磁石なしで組めるので、磁石の入れ忘れや極性の間違いが起きない。蟻継ぎは差し込み方向を1つに決めやすい。欠点は、殻厚数 mm・接触面が小さい条件で、スナップ（片持ち幅5 mm 以上が推奨）の寸法が取れるか不明な点と、FDM の寸法精度（クリアランス 0.2〜0.5 mm の幅）が、鍵の識別に使えるほどの細かさがないこと。

### 担当者が決める必要がある点
- 一意性の担保を、(A) 磁石の極性のみ、(B) 形状のみ（タブ、蟻継ぎ）、(C) 併用、のどれで取るか。（A）は組み合わせ数が少なく、（B）は寸法精度に依存し、（C）は設計と試作が増える。
- 磁石を封じるか（A: 天井層を印刷して封じる。吸着力は下がるが見た目はきれい）、露出して接着するか（B: 吸着力は大きいが磁石が見える）。
- 磁石のサイズ（Φ3 x 1〜2 mm か Φ4 x 2 mm か）。吸着力はカタログ値で 0.2〜0.6 kg 程度の範囲だが、ピースの重さに対する余裕は試作で決める。
- 誤接続をどこまで許すか。完全に弾く（反発させる）か、弱く引き合う程度を許すか。Selective Self-Assembly の論文でも完全な無関心（0）は得られていない（最悪値 -0.36）。
- ピース数（字の数）の上限。符号の数（12組程度）や、形状の識別数が足りるか、の判断に使う。

### 分からなかったこと
- 磁石どうしの吸着力（Case 3）と、樹脂の隙間（0.4〜1 mm）を挟んだ場合の実際の吸着力の数値。K&J の曲線を読めていない。
- 磁石を埋め込める接触面の最小の大きさの、一次情報での数値。目安は寸法からの計算で、Φ3.17 mm 磁石 + 片側の隙間 0.15 mm + 壁（印刷の2周で約0.8〜0.9 mm）x 2 で約 5 mm 程度。ただし、この壁厚の根拠は未確認の仮定で、出典なし。
- 磁石2個の極性の並びで区別できる組み合わせの数の、一次情報での実測。数式上の 2^n 通りは出るが、誤接続の合力がどこまで小さくなるかは未確認。
- Ravensburger Puzzleball の継手の寸法と、曲面タイルを横からつなぐ FDM 向けの作例の寸法。
- Mixels・Selective Self-Assembly の公開コードの有無。
- 磁石の日本国内での入手先と価格。
