# P5-08 Binance Data Vision方針転換・Crypto暫定対象

- Document ID: `P5-ART-ALT-DATA-DECISION-001`
- Decision ID: `DEC-P5-BINANCE-001`
- Step ID: `P5-08`（方針転換記録）
- Phase ID: `PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12`
- Plan: `P5-PLAN-001`
- 実施日: 2026-08-14（Asia/Tokyo）
- 状態: `PROVIDER_DECIDED / SCOPE_AMENDMENT_REQUIRED`
- 正式HTML: [Binance Data Vision方針転換・Crypto暫定対象](../../../doc/phase5/06_方針転換/02_Binance_Data_Vision方針転換・Crypto暫定対象.html)

## 1. 運用者の決定

運用者から次の方針変更を受領した。

> 安価なヒストリカルデータ入手方法を調べた。Binance Data Vision にする。それに伴い、現状初期運用の候補としている銘柄は、一旦白紙。銘柄選定で候補に入ったcryptoの銘柄を初期運用の暫定対象とする。

この指示を、次のように記録する。

| 項目 | 現在の決定 |
|---|---|
| Provider | Binance Data Visionの公開アーカイブ |
| 旧初期候補 | `MCL`、`M6A`、`MZC`、`MZS`、`MZW`。履歴として保持し、初期運用候補から外す |
| 具体的に確認できるCrypto候補 | `BTC`、`ETH`、`BTC/USDT` |
| Binance暫定symbol | `BTCUSDT`、`ETHUSDT` |
| 市場区分 | `Binance Spot`を推奨暫定値。Futuresは自動追加しない |
| 初期追加アルト | 具体名がないため追加しない |
| P5-08実行 | まだ開始しない。Binance用の新Gate、request、Runner、Evidenceが必要 |

## 2. 入力履歴からの銘柄抽出

`plan/backtest_and_turtles_full_chat_history.md` のCrypto部分を再読した結果は次のとおり。

- Binance Data VisionをCryptoの推奨Data sourceとして記載。
- Crypto市場の例としてBTC、ETH、主要アルトコインを記載。
- まとめで「BTC、ETHなどの主要銘柄」を記載。
- 最初の具体的な例として「BTC/USDTなど」を記載。

したがって、具体名を持つ暫定対象はBTCとETHだけである。「主要アルトコイン」はカテゴリ名なので、BNB、SOL、XRPなどを推測して追加しない。`BTCUSDT` と `ETHUSDT` は、履歴のBTC／ETHとBTC/USDT表記をBinance Spotのsymbol表記へ落としたものだが、実ファイルの存在・対象期間・取引状態はP5-08実行時に確認する。

## 3. 公式一次情報の確認

確認日は2026-08-14。Web調査のみで、実Dataファイルの取得はしていない。

| ID | 公式URL | 確認内容 | P5での使い方 |
|---|---|---|---|
| OFF-P5-BINANCE-001 | <https://data.binance.vision/> | Binance Data Collectionの公開入口。 | HTTPSの公開Historical経路。API keyは使わない。 |
| OFF-P5-BINANCE-002 | <https://github.com/binance/binance-public-data/blob/master/README.md?plain=1> | 日次／月次、Spot／USD-M／COIN-M、Kline列、interval、timestamp注意、checksum、archive updateを記載。 | Provider capability、Raw path、unit、Quality、Manifestの根拠。 |
| OFF-P5-BINANCE-003 | <https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md?plain=1> | Spot Klineのsymbol／interval／UTC start・end、最大1000件など。 | RESTを主経路にせず、Data Vision ZIPとの意味を確認。 |
| OFF-P5-BINANCE-004 | <https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/> | Spot monthly Kline pathの確認用URL。 | 実行時に対象月のファイル存在を確認する。未取得のため現在はEvidenceではない。 |

READMEから確認した重要点は次のとおり。

1. 公開Dataは日次または月次ファイルで提供される。
2. SpotとUSD-M／COIN-M Futuresは別の市場区分である。
3. Spot KlineにはOHLC、Volume、Quote volume、Trade count、Taker buy volume等がある。
4. Spotの2025-01-01以降はtimestampがmicrosecondsになる注意書きがある。
5. Klineの`1m`、`15m`、`30m`、`1h`、`4h`、`1d`等がサポートされる。
6. ZIPと同じフォルダの`.CHECKSUM`でSHA-256検証ができる。
7. 問題発見後にアーカイブが更新される場合があるため、URLだけでは再現性にならない。

READMEのLicense表示から、データアーカイブの再配布・商用利用条件まで断定しない。P5の新Gateでは外部再配布を禁止し、必要なら利用条件を別途確認する。

## 4. Binance版P5-DATA-G1の推奨値

| 申請項目 | 推奨値 | 状態・根拠 |
|---|---|---|
| Provider | Binance Data Vision / Binance Public Data | 方針決定済み。 |
| Public URL | `https://data.binance.vision/` | 公式公開入口。 |
| Secret | 使用しない。既存環境変数のAPI keyも読まない | 公開Historical ZIPにAPI keyを持ち込まない。 |
| asset type | `crypto` | Cryptoのsymbol・24/7・quote assetをCatalogへ分離。 |
| market segment | `spot`（暫定） | BTC/USDT表記に合わせた安全側の初期値。Futuresは別Gate。 |
| symbols | `BTCUSDT`、`ETHUSDT` | 履歴で具体的に確認できるBTC／ETHだけ。 |
| Raw | Spot monthly Kline `1m` ZIP、必要箇所の日次ZIP | 1mを基底に上位足を生成。Tick／Order bookは初期対象外。 |
| derived timeframe | `D1`、`H4`、`H1`、`M30`、`M15` | 既存P5時間足を継承。保存・集計はUTC。 |
| Calendar | `CRYPTO_24_7_UTC`（version／hashは新Runで固定） | CMEの休日・DST・限月・Rollを適用しない。 |
| period | `2025-02-24T00:00:00Z`以上、`2026-08-01T00:00:00Z`未満 | 旧P5共通期間の比較用暫定継承。全履歴採用ではない。 |
| timestamp | 2025-01-01以降のSpotはmicroseconds想定 | unitをManifestに固定し、UTCへ正規化。 |
| Raw path | `tests/evidence/phase5/RUN-P5-08-BINANCE-001/raw/spot/klines/1m/{symbol}/{YYYY-MM}.zip` と`.CHECKSUM` | 旧Databento rootと分離。ZIP・checksum・展開CSVをhash化。 |
| normalized | `P5-NORMALIZED-BAR-v1.0.0` | Rawのtimestamp unit、symbol、quote asset、hashを参照。 |
| Provider cost | 0 USD | 公開アーカイブのProvider Data費用。内部保存・通信・実行費用は別budget control。 |
| Quality | checksum、列数、単調性、重複、OHLC、欠損、月次／日次境界、未来Data | 実Data未取得。実行時にEvidence化する。 |
| retention／redistribution | 承認済みローカルのみ、外部再配布・公開・Cloud禁止 | 利用条件未確認のまま権利を拡張しない。 |
| Run ID | `RUN-P5-08-BINANCE-001`（新規作成予定） | 旧Databento `RUN-P5-08-DATABENTO-001`と混在させない。 |

## 5. 旧範囲との扱い

- 旧P5-DATA-G1のDatabento、`GLBX.MDP3`、`MCL/M6A/MZC/MZS/MZW`、CME `America/Chicago` Calendar、`DATABENTO_API_KEY`、Databento Runnerは、旧承認・旧検討の履歴である。
- 旧承認をBinance Data Visionへ読み替えない。Provider、資産種類、symbol、Calendar、timestamp、cost、Secret境界が変わっているため、新しいP5-DATA-G1 amendmentが必要。
- 旧DatabentoのP5-08 requestは廃棄・改変せず、取得0件の失敗・停止Evidenceとして保持する。
- 旧Sierra等の代替調査は調査履歴として保持する。今回のBinance決定後の現行候補ではない。

## 6. REQ／UC／Data object／Test／Evidence／Gate

既存P5-01の行を次のように新Providerへ再接続する。

| Trace | 接続 |
|---|---|
| P5-TR-001 | `REQ-V2-0025/0026` → `UC-V2-007/011/014` → CatalogRecord／LogicalInstrumentMapping（BTCUSDT／ETHUSDT） → `TEST-P5-01-CATALOG-001` → symbol／market manifest → `P5-DATA-G1-BINANCE-AMENDMENT-001` |
| P5-TR-002 | `REQ-V2-0027/0028` → `UC-V2-008/011〜014` → TimeframeBinding／CalendarVersionRef（UTC／24-7） → `TEST-P5-01-TIMEFRAME-001/002` → timeframe／calendar hash → new Gate |
| P5-TR-003 | `REQ-V2-0029/0032` → `UC-V2-009〜014/054` → RawDatasetRef／NormalizedDatasetRef／QualityReport → `TEST-P5-01-QUALITY-001〜003` → ZIP／checksum／Normalized Evidence → new Gate → P5-08／09 |
| P5-TR-004 | `REQ-V2-0030` → `UC-V2-014/034` → DataManifest／ProviderFileRef／HashRef → `TEST-P5-01-MANIFEST-001` → URL／month／unit／hash manifest → new Gate |
| P5-TR-005 | `REQ-V2-0031/0091` → `UC-V2-003/009/013/041〜050/067` → ExternalAcquisitionRequest／ProviderCapability → `TEST-P5-01-EXTERNAL-BOUNDARY-001` → Data Vision allowlist／Secret非使用 → new Gate |
| P5-TR-006 | `REQ-V2-0044/0096`、`UNK-P3-05` → `UC-V2-024/025/030〜032` → CostAssumptionSet／SlippageObservation／GapRuleVersion → `TEST-P5-01-COST-GAP-BOUNDARY-001` → Provider費用0とSpot費用仮定の分離 → new Gate／P5-H2 |
| P5-TR-007 | `REQ-V2-0054/0055` → `UC-V2-032/033/035` → PeriodSplitManifest／HoldoutAssessment → `TEST-P5-01-HOLDOUT-001/002` → split hash → new Gate／P5-H2 |

## 7. Unknown・停止・非対象

| ID | 内容 | 状態 |
|---|---|---|
| `UNK-P5-BINANCE-001` | Spotを暫定採用したが、Futuresを意図しないことの明示 | OPEN |
| `UNK-P5-BINANCE-002` | 主要アルトコインの具体名なし | OPEN |
| `UNK-P5-BINANCE-003` | BTCUSDT／ETHUSDTの実ファイル・範囲・欠損 | OPEN |
| `UNK-P5-BINANCE-004` | archive update、月次／日次差、利用・再配布条件 | OPEN |
| `P5-EXTERNAL-WORKER-UNKNOWN` | Binance用Runner、request、host isolation、Evidence root | OPEN |

次の条件では必ず停止する。

- Spot／Futuresの階層を取り違えた。
- symbolが対象表にない、または対象月が欠落している。
- checksum不一致、CSV列不一致、timestamp unit不明、重複・逆行・OHLC不整合。
- 欠損をゼロ埋め、未来Data、月次／日次差を黙って採用した。
- Data Vision以外へ通信した、Secretを読んだ、外部再配布条件を確認せず保存した。
- 新Gate／Runner／request／target paths／Evidence rootが未確定。

P5対象外は、Binance Futures、他取引所、Tick／Order book、Funding／Liquidation、Broker、Paper、Live、実資金、実Risk、Cloud、Core、P4 DB／migrationである。

## 8. 実施していないこと

- Binance Data Visionへの実HTTP取得: 0件
- API key／Secret値の読取り: 0件
- ZIP／CSV／Raw／Normalizedの作成: 0件
- 外部Run、費用発生、Broker／Paper／Live: 0件
- Core、P4 DB、migration、依存、実運用: 変更なし

## 9. 完了チェック

- [x] 運用者のProvider変更・初期候補白紙化・Crypto暫定対象方針を記録した。
- [x] 履歴から具体的に名前があるBTC／ETHだけを抽出した。
- [x] Binance公式URL、Spot／Futures区分、Kline、timestamp、checksum、archive updateを確認日付きで記録した。
- [x] 旧Databento範囲を履歴として分離し、Binanceへ自動読み替えないと明記した。
- [x] 新しいP5-DATA-G1、Runner、request、Evidenceが必要であることを明記した。
- [x] UnknownをPassにしていない。
- [x] 実Data、Secret、外部I/O、費用、Core、P4 DBを変更していない。

判定: `DECIDED_FOR_RESCOPING / P5-08_BLOCKED_UNTIL_BINANCE_GATE_AND_RUNNER_READY`。次はBinance用の申請表 amendmentと最小requestを作成する段階であり、実取得ではない。
