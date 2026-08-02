# Phase 0 Research Charter

- 文書状態: H0承認待ちドラフト
- 作成日: 2026-08-02
- Step ID: P01
- Role: Research Charter Designer
- 上位計画: `plan/Phase0_現代に適した取引アセット調査計画書.md`
- 実行基盤: `plan/Phase0_Step0前_実行基盤準備.md`
- P00確認: `research/asset_selection/00_foundation/00_foundation_status_v0.1_2026-08-02.md`

> 本Charterは研究・システム設計のための調査憲章であり、投資助言ではない。候補アセットの期待収益や将来成績を保証しない。

---

## 1. 調査目的

タートルズ型トレンドフォロー自動売買システムに適した現代の取引対象を、体系的な調査、公式Evidence、Hard Gate、構造採点、固定Protocol Backtest、独立監査を通じて選定する。

最終的な目的は次の2つである。

1. 最終候補として30～50の異なるExposureを選ぶ。
2. システム実装・Shadow・Paper試験へ進める初期3～5 Exposureを選ぶ。

本調査では、過去収益だけで候補を選ばない。日本居住者の利用可能性、API可用性、ロング・ショート、最小取引単位、証拠金、データ品質、費用、流動性、運用リスク、分散価値、固定ルールでの頑健性を総合評価する。

---

## 2. 利用者制約

| 項目 | 制約 |
|---|---|
| 利用者 | 日本居住者 |
| 第一Broker候補 | Interactive Brokers Japan |
| Live開始資金 | 100万円未満 |
| 初期月額費用 | データ、クラウド、監視等を含め1万円未満を目標 |
| 方向 | LongとShortの双方を評価 |
| 戦略 | 原典版と現代版を並行比較 |
| 初期対象 | 3～5市場 |
| 最終対象 | 30～50 Exposure |
| データ粒度 | 初期3～5市場は利用可能な全期間1分足を目標 |
| 研究環境 | 自宅PC |
| Shadow/Paper/Live | 東京リージョンのクラウドVM |

---

## 3. 調査Scope

### 3.1 対象資産クラス

次の資産クラスをLonglist対象とする。

| 資産クラス | 主なExposure例 | 主なVehicle候補 |
|---|---|---|
| 株価指数 | 国・地域・大型株・小型株・Sector指数 | 先物、Micro先物、ETF、CFD |
| 金利 | 国債、短期金利、イールドカーブ関連 | 先物、ETF、CFD |
| FX | Major、Cross、Emerging通貨 | FX先物、Micro先物、Spot FX、CFD |
| Energy | 原油、石油製品、天然ガス | 先物、Micro先物、CFD、ETF |
| Metal | 金、銀、銅、その他金属 | 先物、Micro先物、CFD、ETF |
| Grain/Oilseed | 小麦、トウモロコシ、大豆等 | 先物、Mini先物、CFD |
| Soft | 砂糖、コーヒー、綿花等 | 先物、CFD |
| Livestock | 生牛、豚等 | 先物、CFD |
| Volatility | 株式Volatility関連 | 先物、ETP |
| Crypto | BTC、ETH等Major | Spot、先物、Perpetual |
| Real estate | REIT指数等 | ETF、先物、CFD |
| Environmental/Power | Carbon、Power等 | 先物、CFD |

### 3.2 対象外資産クラス

次は本調査の標準対象外とする。ただし、調査中に強い合理性が出た場合はHuman Gateで追加承認する。

| 対象外 | 理由 |
|---|---|
| 個別株の大規模Universe | Survivorship、Corporate action、Borrow、データ整備の負荷が高く、Phase 0初期の目的に対して広すぎる |
| オプション単体戦略 | タートルズ型Trend followingの主対象ではなく、Vol surface、満期、Greeks、流動性評価が別設計になる |
| Leveraged/Inverse ETFの主採用 | 日次リセット、Path dependency、長期保有の歪みが強い。候補発見時は別枠 |
| 流動性が極端に低い商品 | 小口でもSpread、約定、データ品質、停止リスクが大きい |
| 日本居住者利用可否が確認不能な取引所・Broker | Critical Gateを通過できない |
| API発注または口座照合ができない商品 | 自動売買システムの必須条件を満たさない |

---

## 4. 評価単位

### 4.1 Exposure

Exposureは、経済的な値動きの対象を指す。例は米国大型株指数、金、WTI原油、米国10年金利、日本円対米ドルなどである。

最終30～50件は、原則としてExposure単位で数える。

### 4.2 Vehicle

Vehicleは、Exposureを実際に取引する商品である。例は先物、Micro先物、ETF、Spot FX、CFD、Crypto perpetualなどである。

### 4.3 Candidate

Candidateは、`Exposure × Vehicle × Broker/Venue`の組合せである。

同一Exposureに複数Vehicleがある場合は、候補段階では別Candidateとして管理する。最終選定では原則としてPrimary Vehicleを1つ選び、必要に応じてFallback Vehicleを記録する。

---

## 5. 最終30～50件の定義

最終候補30～50件は、次の条件を満たす異なるExposureの集合とする。

- 各ExposureにPrimary Vehicleが1つある。
- 必要ならFallback Vehicleがある。
- `Research-only`はLive候補30～50件には含めない。
- 同一Exposureの複数Vehicle採用は原則禁止し、採用する場合は運用上の明確な理由を必要とする。
- 1資産クラスへの過度な集中を避ける。
- 通常時相関と危機時相関の両方を確認する。
- 同一Broker、Venue、Currency、Funding mechanismへの集中を表示する。

---

## 6. 初期3～5件の定義

初期3～5 Exposureは、最終候補の中から実装、データ取得、Paper試験に向いた候補を選ぶ。

初期候補の優先基準は次の通り。

- 日本居住者利用可否とBroker/API evidenceが強い。
- 100万円未満の資金でも最小数量と証拠金が過大でない。
- LongとShortの双方を現実的に運用できる。
- 1分足履歴とRealtimeデータの入手性が高い。
- 契約仕様、取引時間、ロール、受渡し、Funding等の運用リスクを管理できる。
- 資産クラスや取引時間が偏りすぎず、システム機能の検証範囲を広げられる。
- 期待収益上位だけで選ばない。

---

## 7. Hard Gate正式定義

採点前に、次のGateで実行不可能または証拠不足の候補を除外、保留、Research-onlyへ分類する。

| Gate | 名称 | Pass条件 | Failまたは保留条件 |
|---|---|---|---|
| G1 | 日本利用 | 日本居住者が口座・商品を利用できる公式根拠がある | 利用不可、またはCritical evidenceなし |
| G2 | API | 発注、注文確認、Position確認、Account確認がAPIで可能 | API不可、または重要機能が確認不能 |
| G3 | 双方向 | LongとShortの双方を継続的に運用できる | Short不可、売禁・Borrow不安定が重大、または不明 |
| G4 | データ | 検証可能な履歴データとLive価格が入手可能 | 履歴またはLiveデータが入手不能 |
| G5 | 商品定義 | Tick、Multiplier、最小数量、取引時間、限月等を確認可能 | 商品仕様が確認不能 |
| G6 | Capital fit | 最小数量のNリスク、2N Stop、証拠金が資金制約内 | 100万円未満でLive運用困難 |
| G7 | 流動性 | 想定注文量に対してSpread、Volume、Depthが十分 | 流動性不足または評価不能 |
| G8 | Cost | 手数料、Spread、Slippage、Funding/RollがNに対して過大でない | Cost過大、または推定不能 |
| G9 | Operational safety | 受渡し、Borrow、Funding、清算、取引停止等を管理可能 | 運用リスクが管理不能 |
| G10 | Evidence | Critical項目に公式一次情報または十分強い根拠がある | Unknown、重大Conflict、古いSource |

`Unknown`はPassにしない。Critical項目がUnknownの場合は、`pending_evidence`または`fail`にする。

---

## 8. 小口資金Gate

資金制約が100万円未満であるため、以下の3Scenarioで評価する。

| Scenario | 金額 |
|---|---:|
| S1 | 500,000 JPY |
| S2 | 750,000 JPY |
| S3 | 1,000,000 JPY upper-bound |

評価項目:

- 最小数量の1Nリスク額。
- 1Nリスクの口座比率。
- 2N Stop損失。
- Gap stress損失。
- 4 Unit積み増し後の理論損失。
- Initial/Maintenance margin比率。
- 3市場・5市場同時保有時の証拠金利用率。
- FX換算10%逆行時の影響。

分類:

| 分類 | 意味 |
|---|---|
| `Tradable-original` | 原典1N=1%基準でも100万円Scenarioで概ね実行可能 |
| `Tradable-modern-only` | 原典1%は困難だが、0.25～0.5%等で実行可能性あり |
| `Research-only` | 研究対象にはできるが100万円未満Liveには不適 |
| `Exclude` | 研究対象としても不適 |
| `Pending-evidence` | 必須情報不足 |

---

## 9. Scorecard 100点配分

Hard Gate通過候補だけを採点する。

| 大項目 | 配点 | 小項目 |
|---|---:|---|
| Execution・流動性 | 20 | Spread/N 6、Slippage 4、Volume/Depth 5、取引時間・停止 2、注文機能 3 |
| 小口資金適合 | 20 | 最小1Nリスク 8、2N+Gap 5、証拠金 4、Sizing粒度 3 |
| Access・運用 | 15 | 日本/Broker/API 5、Long/Short 3、運用複雑性 3、Roll/Borrow/Funding/Counterparty 4 |
| データ品質・費用 | 15 | 履歴年数 5、1分足 4、商品定義 3、License・月額費用 3 |
| 分散価値 | 15 | Exposure独自性 5、通常時相関 4、危機時相関 3、資産クラス寄与 3 |
| Trend頑健性 | 15 | 固定ルールOOS 5、複数速度・期間 4、Parameter安定性 3、Cost stress耐性 3 |
| 合計 | 100 |  |

Backtest前のStep 7では、Trend頑健性15点を採点しない。残り85点を100点へ比例換算し、`structural_score_pretest`として扱う。

---

## 10. Evidence Confidence定義

| Confidence | Factor | 定義 |
|---|---:|---|
| A | 1.00 | Critical項目が公式一次情報で確認済み |
| B | 0.95 | 主要項目は公式確認済みで、一部が信頼できる二次情報 |
| C | 0.85 | 重要な不確実性が残る |
| Unknown | 採点禁止 | Hard Gateの再調査が必要 |

Evidenceには最低限、次を記録する。

- source_url。
- source_title。
- publisher。
- accessed_at。
- published_dateまたはeffective_date。
- candidate_id、exposure_id、vehicle_id。
- fact_type。
- 要点の日本語要約。
- primary_or_secondary。
- confidence。
- conflict_status。
- expiry_dateまたは再確認期限。

---

## 11. 情報鮮度基準

| 情報 | 再確認目安 |
|---|---|
| 日本居住者の取扱可否・口座権限 | 最終決定前7日以内 |
| 現行証拠金 | 最終決定時およびPaper開始前 |
| Borrow・空売り可否 | 動的情報として都度確認 |
| Commission・市場データ料金 | 最終決定前30日以内 |
| Contract specification | 最終決定前30日以内、取引開始前にも再確認 |
| Volume・Open interest・Spread | 複数期間集計に加え、開始直前に更新 |
| 法規制・税務 | 最終決定時に公的・公式情報を再確認 |
| 履歴Data仕様・License | 購入直前に再確認 |

鮮度期限を超えたEvidenceは削除せず、`stale`として扱う。Critical判定の根拠には再検証完了まで使わない。

---

## 12. Bias対策

### 12.1 過剰適合対策

- CandidateごとにLookback、Stop、Roll ruleを最適化しない。
- 固定候補は20/10、55/20、100/50、200/100を中心に事前登録する。
- Backtest Protocolは結果を見る前にH3で承認する。
- すべての試行回数をExperiment registryへ記録する。
- 最良結果だけでなく、中央値、一貫性、Worst acceptable case、Cost stress耐性を評価する。
- Backtest結果を見た後にScorecard weightを変更しない。

### 12.2 Selection bias対策

- Longlist作成時に過去収益や人気ランキングで候補を絞らない。
- 公式商品一覧、Broker商品、Data vendor coverageから広く候補を作る。
- 採点前にHard Gateを実施する。
- 最終選定はScore順だけでなく、Exposure重複、相関、資産クラス、運用集中を考慮する。
- 選定しなかった候補にも理由を記録する。

### 12.3 Survivorship bias対策

- ETF、株式、ETN、Crypto、先物限月では上場廃止、期限切れ、構成変更を確認する。
- 期限切れ先物とContract definitionを取得可能か確認する。
- Point-in-timeで入手可能だった情報を優先する。
- Delisted assetsを含められないデータ源は、制約として記録する。

### 12.4 Look-ahead bias対策

- Entry当日値をChannel計算に含めない。
- ロール後の連続系列が人工的なブレイクアウトを作らないよう、Signal系列とTradable系列を分離する。
- 当時利用不能だった構成銘柄、契約仕様、取引時間、証拠金情報を使わない。

### 12.5 AI誤読・捏造対策

- 検索結果Snippetだけで判定しない。
- Source URLを開いて確認する。
- 重要事実は公式一次情報を優先する。
- 矛盾する情報は平均せず、`conflict_status`として残す。
- Red TeamでSource切れ、古い情報、計算誤りを監査する。

---

## 13. H0承認対象

H0では、次を承認対象とする。

- 調査目的。
- 対象資産クラス。
- 対象外資産クラス。
- Exposure、Vehicle、Candidateの評価単位。
- 最終30～50件の定義。
- 初期3～5件の定義。
- Hard Gate G1～G10。
- 小口資金Gate。
- Scorecard 100点配分。
- Evidence confidence定義。
- 情報鮮度基準。
- Bias対策。

H0承認前に、P03のWeb Longlist調査へ進まない。

---

## 14. H0後に許可される作業

H0承認後、次に進める。

1. `P02: Step 1 Taxonomy・Schema設計`
2. P02完了後、`P03: Step 2 Web Longlist作成`

H0承認だけでは、Data購入、Backtest、最終選定、Live設定反映は許可されない。

