# P03 Longlist Coverage Report v0.1

- Step ID: P03
- Role: Longlist Builder
- Status: H1 approved with conditions on 2026-08-02
- Created at: 2026-08-02T13:36:30+09:00
- Candidate file: `research/asset_selection/03_longlist/03_longlist_candidates_v0.1_2026-08-02.csv`
- Source index: `research/asset_selection/sources/03_source_index_v0.1_2026-08-02.csv`

## 1. P03の目的

P03の目的は、Phase 0のAsset Selectionで後続評価にかけるための、資産クラス横断のLonglistを作成することである。

このStepでは、取引適格性を確定しない。具体的には、以下はP04以降で検証する。

- 日本居住者が当該Broker/APIで実際に取引できるか。
- API経由で発注、約定照会、口座管理ができるか。
- 十分な流動性、スプレッド、約定品質があるか。
- Turtle/Trend Followingに適した価格系列・期限構造・ロール処理が成立するか。
- 空売りまたはショート相当ポジションが可能か。
- 税務、規制、証拠金、取引時間、データライセンス上の制約。

## 2. 調査方針

P03では、原則として取引所・市場運営者・Broker公式ページを一次情報として使用した。

使用した主な情報源は以下。

- CME Group Product Slate
- CME Group Micro Products
- JPX Derivatives List of Products
- ICE Futures U.S.
- Eurex Product Search
- SGX Derivatives / FX Products
- Cboe VIX Futures
- Interactive Brokers Products, Exchanges and Contracts Search
- Nasdaq Commodities Data

全ソースは `research/asset_selection/sources/03_source_index_v0.1_2026-08-02.csv` に登録した。

## 3. Longlist件数

| 指標 | 件数 |
|---|---:|
| Candidate/Vehicle rows | 154 |
| Unique exposure_id | 129 |
| Source index rows | 13 |

P03の機械実行プロンプトで想定していた「100〜200程度の資産候補」としては、Unique exposure 129件で範囲内に収まっている。Vehicle rowsは154件で、標準・ミニ・マイクロ等の同一Exposureに対する複数Vehicleを含む。

## 4. Asset class coverage

| Asset class | Candidate rows |
|---|---:|
| equity_index | 35 |
| rates | 20 |
| fx | 25 |
| energy | 15 |
| environmental_power | 13 |
| metals | 15 |
| grains_oilseeds | 12 |
| livestock | 3 |
| crypto | 6 |
| softs | 5 |
| volatility | 4 |
| real_estate | 1 |

## 5. Venue coverage

| Venue | Candidate rows |
|---|---:|
| CME | 36 |
| CBOT | 15 |
| NYMEX | 9 |
| COMEX | 6 |
| ICEUS | 10 |
| ICEEU | 4 |
| OSE | 31 |
| TOCOM | 9 |
| EUREX | 14 |
| SGX | 13 |
| CFE | 2 |
| NASDAQ | 5 |

## 6. Coverage評価

### 強いCoverage

- 先物中心のTrend Following向けコア資産は広く含めた。
- 株価指数、債券・金利、FX、エネルギー、金属、農産物、ソフト、ボラティリティ、暗号資産先物、環境・電力系を含めた。
- 日本居住者・日本時間運用の観点で、JPX/OSE/TOCOM/SGXを明示的に含めた。
- 小口運用・初期運用に関係するMicro/Mini系VehicleをCME/JPX中心に含めた。

### 弱いCoverage / P04以降で補完すべき点

- ETF/現物株/スポットFX/CFDは、P03 v0.1では主対象にしていない。先物中心のLonglistである。
- Crypto spot/perpetualは、取引所リスク・規制・API差が大きいため、P03ではCMEの上場Crypto futures中心に留めた。
- NASDAQ Commoditiesは市場データソースとして確認したが、個別Contractの取引可能性はP04で別途検証が必要。
- ICE Europe、EEX、LME、ASX、HKEX等は、P03 v0.1では網羅していない。必要ならP03拡張版で追加する。

## 7. Bias対策の適用状況

- Backtest結果や過去リターンを使った候補絞り込みは行っていない。
- Candidate別Parameter最適化は行っていない。
- 「有名だから採用」ではなく、公式商品リストに基づく存在確認を優先した。
- Delisted/Survivorshipの問題は、このStepでは未評価。P06以降のHistorical data auditで扱う。
- UnknownはPass扱いにしていない。取引適格性は原則Pendingである。

## 8. Gate状態

| Gate/Status | 判定 | 理由 |
|---|---|---|
| H0 | Approved | 2026-08-02にユーザー承認済み |
| P03 Longlist作成 | Complete | Candidate 154 rows / Unique exposure 129件を作成 |
| H1 | Approved with conditions | 2026-08-02にユーザー承認。先物Track主導でP04へ進行 |
| P04開始可否 | Unblocked | H1承認済みのためEligibility/API/Access検証へ進行可能 |

## 9. H1で承認してほしい内容

H1では、次を承認対象とする。

1. P03 v0.1のLonglistをP04以降の評価母集団として使用してよいか。
2. P03 v0.1は先物中心であり、ETF/CFD/Spot FX/Crypto spotは必要に応じて別Trackで扱う方針でよいか。
3. P04で、各Candidateの「日本居住者アクセス」「Broker/API対応」「口座種別」「ショート可否」「最小取引単位」「データ取得方法」を検証する方針でよいか。
4. P03拡張が必要な場合、追加対象Venue/Asset classを指定するか。
