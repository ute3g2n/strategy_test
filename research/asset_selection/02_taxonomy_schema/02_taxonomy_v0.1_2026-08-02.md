# Phase 0 Taxonomy

- 文書状態: draft
- 作成日: 2026-08-02
- Step ID: P02
- Role: Taxonomy and Schema Architect
- 入力: `research/asset_selection/01_charter/01_research_charter_v0.1_2026-08-02.md`
- H0: approved

> 本文書はP03以降のLonglist、Evidence検証、Hard Gate、採点で使う分類体系とID規則を固定する。投資助言ではない。

---

## 1. 分類の原則

- 最終選定はExposure単位で数える。
- Candidateは`Exposure x Vehicle x Broker/Venue`で定義する。
- 同じ経済Exposureに複数Vehicleがある場合は、Candidateを分けて管理する。
- Primary/Fallback VehicleはP11で決める。P02時点では決めない。
- Longlist作成時点では、過去収益で候補を絞らない。
- `Unknown`はPassにしない。

---

## 2. Asset Class Taxonomy

| asset_class | 日本語名 | 定義 | P03での主な探索対象 |
|---|---|---|---|
| `equity_index` | 株価指数 | 国、地域、時価総額、Sectorなどの株式指数Exposure | Index futures, micro futures, ETFs, CFDs |
| `rates` | 金利 | 国債、短期金利、金利先物、利回り関連Exposure | Treasury futures, STIR futures, bond ETFs |
| `fx` | 外国為替 | 通貨ペアまたは通貨指数Exposure | FX futures, spot FX, micro FX, CFDs |
| `energy` | エネルギー | 原油、石油製品、天然ガス、電力等 | Futures, micro futures, CFDs, ETFs |
| `metals` | 金属 | 貴金属、産業金属Exposure | Futures, micro futures, CFDs, ETFs |
| `grains_oilseeds` | 穀物・油糧種子 | 小麦、トウモロコシ、大豆等 | Futures, mini futures, CFDs |
| `softs` | ソフトコモディティ | 砂糖、コーヒー、綿花、ココア等 | Futures, CFDs |
| `livestock` | 畜産 | 生牛、豚等 | Futures, CFDs |
| `volatility` | ボラティリティ | VIX等の株式Volatility Exposure | Futures, ETPs |
| `crypto` | 暗号資産 | BTC、ETH等の暗号資産Exposure | Spot, futures, perpetuals |
| `real_estate` | 不動産 | REIT指数、不動産関連指数 | ETFs, futures, CFDs |
| `environmental_power` | 環境・電力 | Carbon、Power等 | Futures, CFDs |
| `other_review` | 要審査 | 上記に入らないが調査上記録する候補 | Human Gateで採否判断 |

---

## 3. Exposure Taxonomy

Exposureは、次の軸で分類する。

| column | 説明 | 例 |
|---|---|---|
| `exposure_id` | Exposureの安定ID | `EXP-EQ-US-SP500` |
| `exposure_name_ja` | 日本語名 | 米国大型株指数 |
| `exposure_name_en` | 英語名 | S&P 500 Index |
| `asset_class` | 資産クラス | `equity_index` |
| `risk_cluster` | リスククラスター | `global_equity_us_large` |
| `economic_driver` | 主な価格変動要因 | US equity risk premium |
| `region` | 主な地域 | `US` |
| `base_currency` | Exposureの基準通貨 | `USD` |
| `direct_or_proxy` | 直接ExposureかProxyか | `direct` / `proxy` |
| `tradable_thesis` | Trend followingで調査する理由 | 長期トレンドが出やすい大型指数 |

### 3.1 Exposure ID生成規則

形式:

```text
EXP-{ASSET}-{REGION}-{NAME}
```

例:

| Exposure | exposure_id |
|---|---|
| S&P 500 | `EXP-EQ-US-SP500` |
| Nikkei 225 | `EXP-EQ-JP-NIKKEI225` |
| Gold | `EXP-METAL-GLOBAL-GOLD` |
| WTI Crude Oil | `EXP-ENERGY-US-WTI` |
| EUR/USD | `EXP-FX-G10-EURUSD` |
| Bitcoin | `EXP-CRYPTO-GLOBAL-BTC` |

規則:

- ASCII uppercaseを使う。
- 空白は使わない。
- 名称変更があってもIDは原則維持する。
- 同じExposureが別名で見つかった場合は、最初のIDへ統合し、migration mapを作る。

---

## 4. Vehicle Taxonomy

| vehicle_type | 日本語名 | 定義 |
|---|---|---|
| `future_standard` | 標準先物 | 標準サイズの取引所先物 |
| `future_micro` | Micro先物 | 小口サイズの取引所先物 |
| `future_mini` | Mini先物 | 標準未満、Micro以上または取引所定義のMini先物 |
| `spot_fx` | Spot FX | Brokerの現物または証拠金FX |
| `etf` | ETF | 上場投資信託 |
| `etn` | ETN | 上場投資証券 |
| `cfd` | CFD | 差金決済取引 |
| `crypto_spot` | 暗号資産Spot | 暗号資産現物 |
| `crypto_perp` | 暗号資産Perpetual | 無期限先物・Perpetual |
| `crypto_future` | 暗号資産先物 | 期限付き暗号資産先物 |
| `other_review` | 要審査 | 標準分類外 |

### 4.1 Vehicle ID生成規則

形式:

```text
VEH-{TYPE}-{VENUE}-{SYMBOL}
```

例:

| Vehicle | vehicle_id |
|---|---|
| CME Micro E-mini S&P 500 | `VEH-FUTMICRO-CME-MES` |
| CME E-mini S&P 500 | `VEH-FUTSTD-CME-ES` |
| NYSE Arca SPY ETF | `VEH-ETF-ARCA-SPY` |
| IBKR EUR.USD Spot FX | `VEH-SPOTFX-IBKR-EURUSD` |

規則:

- 取引所またはVenueは公式略称を優先する。
- Broker固有商品はVenueにBroker名を使う。
- CFDはBrokerごとにVehicleを分ける。

---

## 5. Candidate ID生成規則

形式:

```text
CAN-{EXPOSURE_ID_WITHOUT_EXP}-{VEHICLE_ID_WITHOUT_VEH}-{BROKER_OR_VENUE}
```

例:

```text
CAN-EQ-US-SP500-FUTMICRO-CME-MES-IBKR
CAN-METAL-GLOBAL-GOLD-FUTMICRO-CME-MGC-IBKR
CAN-FX-G10-EURUSD-SPOTFX-IBKR-EURUSD-IBKR
```

規則:

- Candidateは実際に調査する取引可能性の単位である。
- 同じExposureでもVehicleまたはBrokerが違えば別Candidate。
- Candidate IDは一度発行したら再利用しない。
- Candidateが除外されてもIDは削除しない。

---

## 6. Risk Cluster Taxonomy

Risk clusterは、原典の4/6/10/12 Unit制限や相関評価に使う。

| risk_cluster prefix | 意味 | 例 |
|---|---|---|
| `global_equity` | 株式ベータ系 | US大型株、日本株、欧州株 |
| `rates_dm` | 先進国金利 | 米国債、独国債、日本国債 |
| `fx_g10` | G10通貨 | EUR/USD, USD/JPY |
| `fx_em` | Emerging通貨 | MXN, ZAR等 |
| `energy_crude` | 原油系 | WTI, Brent |
| `energy_gas` | ガス・電力系 | Natural Gas, Power |
| `metals_precious` | 貴金属 | Gold, Silver |
| `metals_industrial` | 産業金属 | Copper |
| `agri_grain` | 穀物 | Wheat, Corn |
| `agri_oilseed` | 油糧種子 | Soybeans |
| `agri_soft` | Soft commodity | Sugar, Coffee |
| `livestock` | 畜産 | Live cattle |
| `vol_equity` | 株式Volatility | VIX |
| `crypto_major` | 主要暗号資産 | BTC, ETH |
| `real_estate_reit` | REIT | US REIT, JP REIT |
| `environmental_power` | 環境・電力 | Carbon, Power |
| `other_review` | 要審査 | 未分類 |

規則:

- Risk clusterは最終選定時の重複排除と集中表示に使う。
- 数値相関だけでなく、経済的な共通ドライバーも考慮する。
- P03時点では暫定でよい。P05で統合・修正する。

---

## 7. Evidence fact_type一覧

| fact_type | 意味 | Critical |
|---|---|---|
| `japan_resident_eligibility` | 日本居住者利用可否 | yes |
| `broker_product_availability` | Broker取扱商品 | yes |
| `api_order_capability` | API発注可否 | yes |
| `api_account_position_capability` | API口座・Position照合可否 | yes |
| `long_short_availability` | Long/Short可否 | yes |
| `contract_specification` | Tick、Multiplier、最小数量等 | yes |
| `trading_hours_calendar` | 取引時間、休日、短縮日 | yes |
| `first_notice_last_trade` | First Notice、Last Trade | futures only |
| `delivery_settlement_risk` | 受渡し・決済リスク | futures only |
| `margin_requirement` | 証拠金 | yes |
| `commission_fee` | 手数料 | yes |
| `spread_liquidity` | Spread、Volume、Depth、OI | yes |
| `historical_data_availability` | 履歴データ入手性 | yes |
| `minute_data_availability` | 1分足入手性 | yes |
| `realtime_data_availability` | Realtimeデータ入手性 | yes |
| `data_license_cost` | Data license、費用 | yes |
| `borrow_funding_roll_cost` | Borrow、Funding、Roll cost | vehicle dependent |
| `delisting_survivorship` | 上場廃止・Survivorship | ETF/stock/crypto |
| `regulatory_tax_note` | 法規制・税務メモ | conditional |
| `other_note` | その他 | no |

---

## 8. 出力ファイルの関係

P03以降の基本関係は次の通り。

```text
Exposure -> Vehicle -> Candidate
Candidate -> Evidence
Candidate -> Gate Result
Candidate -> Score
Exposure -> Final Selection
```

P03ではLonglist候補を広く作る。P04でEvidenceを検証し、P05でExposure/Vehicleを整理する。P06以降でGateと採点を行う。

