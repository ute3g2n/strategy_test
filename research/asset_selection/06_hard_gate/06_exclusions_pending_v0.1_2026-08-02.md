# P06 Hard Gate Exclusions and Pending Report v0.1

- Step ID: P06
- Role: Feasibility and Capital Gate Analyst
- Status: H2 approval pending
- Created at: 2026-08-02T15:17:35.0009807+09:00

## Summary

- Candidate rows evaluated: 154
- Tradable-original: 0
- Tradable-modern-only: 0
- Pending-evidence: 149
- Research-only: 5
- Exclude: 0

## Why no candidate passed

P06 applies the rule from the execution plan: Unknown margin, N, multiplier, or minimum quantity cannot pass.

At P04/P05, the universe has broker/API framework evidence, but candidate-level numeric inputs remain missing. Therefore no candidate can be classified as Tradable-original or Tradable-modern-only yet.

The missing inputs are not cosmetic. They directly determine whether a 500,000 JPY, 750,000 JPY, or 1,000,000 JPY account can hold even one unit without violating Turtle-style risk limits.

## Turtle calculation basis used

- 1 Unit is sized so that a 1N move is approximately 1% of notional account in the original rule.
- Initial stop is normally 2N, so the first Unit has roughly 2% planned stop risk before slippage and gap risk.
- Modern small-account mode should also evaluate 0.25% to 0.50% 1N risk.
- 4 Unit pyramiding can create materially larger market-level stop exposure, so 4 Unit theoretical stop loss is required before pass.

## Classification counts

- Pending-evidence: 149
- Research-only: 5

## Asset class counts

- crypto: 6
- energy: 15
- environmental_power: 13
- equity_index: 35
- fx: 25
- grains_oilseeds: 12
- livestock: 3
- metals: 15
- rates: 20
- real_estate: 1
- softs: 5
- volatility: 4

## Venue counts

- CBOT: 15
- CFE: 2
- CME: 36
- COMEX: 6
- EUREX: 14
- ICEEU: 4
- ICEUS: 10
- NASDAQ: 5
- NYMEX: 9
- OSE: 31
- SGX: 13
- TOCOM: 9

## Capital scenario result

| Capital JPY | Tradable-original | Tradable-modern-only | Pending-evidence | Research-only | Status |
|---:|---:|---:|---:|---:|---|
| 500,000 | 0 | 0 | 149 | 5 | not calculable |
| 750,000 | 0 | 0 | 149 | 5 | not calculable |
| 1,000,000 | 0 | 0 | 149 | 5 | not calculable |

## Required enrichment before a meaningful P06 rerun

- Contract multiplier and tick value for every candidate or at least for a narrowed priority subset.
- Current price with as-of timestamp.
- 20-day ATR/N in native currency and JPY converted value.
- Initial and maintenance margin in JPY or native currency plus FX conversion.
- Minimum order quantity.
- Round-trip commission, average spread, and estimated slippage.
- Product-level Japan resident eligibility and trading permission evidence.
- Realtime and historical data availability/cost.

## Sample blocking unknowns

- CAN-EXP-EQ-US-SP500-FUTURE-STANDARD-CME-ES-IBSJ: N/ATR_20_JPY_or_native;current_price_as_of_date;contract_multiplier;tick_size;minimum_quantity;initial_margin_jpy;maintenance_margin_jpy;commission_roundtrip_jpy;spread_estimate;historical_data_availability;realtime_data_entitlement_cost;symbol_level_japan_resident_eligibility
- CAN-EXP-EQ-US-SP500-FUTURE-MICRO-CME-MES-IBSJ: N/ATR_20_JPY_or_native;current_price_as_of_date;contract_multiplier;tick_size;minimum_quantity;initial_margin_jpy;maintenance_margin_jpy;commission_roundtrip_jpy;spread_estimate;historical_data_availability;realtime_data_entitlement_cost;symbol_level_japan_resident_eligibility
- CAN-EXP-EQ-US-NASDAQ100-FUTURE-STANDARD-CME-NQ-IBSJ: N/ATR_20_JPY_or_native;current_price_as_of_date;contract_multiplier;tick_size;minimum_quantity;initial_margin_jpy;maintenance_margin_jpy;commission_roundtrip_jpy;spread_estimate;historical_data_availability;realtime_data_entitlement_cost;symbol_level_japan_resident_eligibility
- CAN-EXP-EQ-US-NASDAQ100-FUTURE-MICRO-CME-MNQ-IBSJ: N/ATR_20_JPY_or_native;current_price_as_of_date;contract_multiplier;tick_size;minimum_quantity;initial_margin_jpy;maintenance_margin_jpy;commission_roundtrip_jpy;spread_estimate;historical_data_availability;realtime_data_entitlement_cost;symbol_level_japan_resident_eligibility
- CAN-EXP-EQ-US-RUSSELL2000-FUTURE-STANDARD-CME-RTY-IBSJ: N/ATR_20_JPY_or_native;current_price_as_of_date;contract_multiplier;tick_size;minimum_quantity;initial_margin_jpy;maintenance_margin_jpy;commission_roundtrip_jpy;spread_estimate;historical_data_availability;realtime_data_entitlement_cost;symbol_level_japan_resident_eligibility
- CAN-EXP-EQ-US-RUSSELL2000-FUTURE-MICRO-CME-M2K-IBSJ: N/ATR_20_JPY_or_native;current_price_as_of_date;contract_multiplier;tick_size;minimum_quantity;initial_margin_jpy;maintenance_margin_jpy;commission_roundtrip_jpy;spread_estimate;historical_data_availability;realtime_data_entitlement_cost;symbol_level_japan_resident_eligibility
- CAN-EXP-EQ-US-DOW-FUTURE-STANDARD-CME-YM-IBSJ: N/ATR_20_JPY_or_native;current_price_as_of_date;contract_multiplier;tick_size;minimum_quantity;initial_margin_jpy;maintenance_margin_jpy;commission_roundtrip_jpy;spread_estimate;historical_data_availability;realtime_data_entitlement_cost;symbol_level_japan_resident_eligibility
- CAN-EXP-EQ-US-DOW-FUTURE-MICRO-CME-MYM-IBSJ: N/ATR_20_JPY_or_native;current_price_as_of_date;contract_multiplier;tick_size;minimum_quantity;initial_margin_jpy;maintenance_margin_jpy;commission_roundtrip_jpy;spread_estimate;historical_data_availability;realtime_data_entitlement_cost;symbol_level_japan_resident_eligibility
- CAN-EXP-EQ-US-MIDCAP400-FUTURE-STANDARD-CME-EMD-IBSJ: N/ATR_20_JPY_or_native;current_price_as_of_date;contract_multiplier;tick_size;minimum_quantity;initial_margin_jpy;maintenance_margin_jpy;commission_roundtrip_jpy;spread_estimate;historical_data_availability;realtime_data_entitlement_cost;symbol_level_japan_resident_eligibility
- CAN-EXP-EQ-JP-NIKKEI225-USD-FUTURE-STANDARD-CME-NIY-IBSJ: N/ATR_20_JPY_or_native;current_price_as_of_date;contract_multiplier;tick_size;minimum_quantity;initial_margin_jpy;maintenance_margin_jpy;commission_roundtrip_jpy;spread_estimate;historical_data_availability;realtime_data_entitlement_cost;symbol_level_japan_resident_eligibility
- CAN-EXP-RATES-US-2Y-FUTURE-STANDARD-CBOT-ZT-IBSJ: N/ATR_20_JPY_or_native;current_price_as_of_date;contract_multiplier;tick_size;minimum_quantity;initial_margin_jpy;maintenance_margin_jpy;commission_roundtrip_jpy;spread_estimate;historical_data_availability;realtime_data_entitlement_cost;symbol_level_japan_resident_eligibility
- CAN-EXP-RATES-US-5Y-FUTURE-STANDARD-CBOT-ZF-IBSJ: N/ATR_20_JPY_or_native;current_price_as_of_date;contract_multiplier;tick_size;minimum_quantity;initial_margin_jpy;maintenance_margin_jpy;commission_roundtrip_jpy;spread_estimate;historical_data_availability;realtime_data_entitlement_cost;symbol_level_japan_resident_eligibility
- CAN-EXP-RATES-US-10Y-FUTURE-STANDARD-CBOT-ZN-IBSJ: N/ATR_20_JPY_or_native;current_price_as_of_date;contract_multiplier;tick_size;minimum_quantity;initial_margin_jpy;maintenance_margin_jpy;commission_roundtrip_jpy;spread_estimate;historical_data_availability;realtime_data_entitlement_cost;symbol_level_japan_resident_eligibility
- CAN-EXP-RATES-US-30Y-FUTURE-STANDARD-CBOT-ZB-IBSJ: N/ATR_20_JPY_or_native;current_price_as_of_date;contract_multiplier;tick_size;minimum_quantity;initial_margin_jpy;maintenance_margin_jpy;commission_roundtrip_jpy;spread_estimate;historical_data_availability;realtime_data_entitlement_cost;symbol_level_japan_resident_eligibility
- CAN-EXP-RATES-US-ULTRABOND-FUTURE-STANDARD-CBOT-UB-IBSJ: N/ATR_20_JPY_or_native;current_price_as_of_date;contract_multiplier;tick_size;minimum_quantity;initial_margin_jpy;maintenance_margin_jpy;commission_roundtrip_jpy;spread_estimate;historical_data_availability;realtime_data_entitlement_cost;symbol_level_japan_resident_eligibility
- CAN-EXP-RATES-US-SOFR3M-FUTURE-STANDARD-CME-SR3-IBSJ: N/ATR_20_JPY_or_native;current_price_as_of_date;contract_multiplier;tick_size;minimum_quantity;initial_margin_jpy;maintenance_margin_jpy;commission_roundtrip_jpy;spread_estimate;historical_data_availability;realtime_data_entitlement_cost;symbol_level_japan_resident_eligibility
- CAN-EXP-RATES-US-FEDFUND-FUTURE-STANDARD-CBOT-ZQ-IBSJ: N/ATR_20_JPY_or_native;current_price_as_of_date;contract_multiplier;tick_size;minimum_quantity;initial_margin_jpy;maintenance_margin_jpy;commission_roundtrip_jpy;spread_estimate;historical_data_availability;realtime_data_entitlement_cost;symbol_level_japan_resident_eligibility
- CAN-EXP-RATES-US-10Y-MICRO-FUTURE-MICRO-CME-10Y-IBSJ: N/ATR_20_JPY_or_native;current_price_as_of_date;contract_multiplier;tick_size;minimum_quantity;initial_margin_jpy;maintenance_margin_jpy;commission_roundtrip_jpy;spread_estimate;historical_data_availability;realtime_data_entitlement_cost;symbol_level_japan_resident_eligibility
- CAN-EXP-RATES-US-2Y-MICRO-FUTURE-MICRO-CME-2YY-IBSJ: N/ATR_20_JPY_or_native;current_price_as_of_date;contract_multiplier;tick_size;minimum_quantity;initial_margin_jpy;maintenance_margin_jpy;commission_roundtrip_jpy;spread_estimate;historical_data_availability;realtime_data_entitlement_cost;symbol_level_japan_resident_eligibility
- CAN-EXP-RATES-US-30Y-MICRO-FUTURE-MICRO-CME-30Y-IBSJ: N/ATR_20_JPY_or_native;current_price_as_of_date;contract_multiplier;tick_size;minimum_quantity;initial_margin_jpy;maintenance_margin_jpy;commission_roundtrip_jpy;spread_estimate;historical_data_availability;realtime_data_entitlement_cost;symbol_level_japan_resident_eligibility

## H2 approval request

H2で承認してほしい内容は次です。

- P06 v0.1では、計算に必要なCritical dataが不足しているため、Tradable候補を0件とする。
- 149件をPending-evidence、5件をResearch-onlyとしてP07またはP06再実行前のデータ補完対象にする。
- P07へ進む場合は、全154件ではなく、P05のproxy groupと小口運用可能性を考慮して優先Subsetを作ってData Vendor/費用調査を行う。
- P06を再実行する場合は、先に契約仕様・証拠金・価格・ATR/Nを公式/信頼ソースから補完する。

```text
H2 Decision:
- decision: approved_with_conditions
- approver: owner
- decision_at: 2026-08-02
- approved_scope:
  - research/asset_selection/06_hard_gate/06_hard_gate_results_v0.1_2026-08-02.csv
  - research/asset_selection/06_hard_gate/06_capital_scenarios_v0.1_2026-08-02.csv
  - research/asset_selection/06_hard_gate/06_exclusions_pending_v0.1_2026-08-02.md
- conditions:
  - Unknown margin, N, multiplier, or minimum quantity remains non-passable
  - P07 should prioritize data/cost feasibility and may recommend a narrowed enrichment subset
- rejected_reasons:
- next_allowed_step: P07
- notes:
```

