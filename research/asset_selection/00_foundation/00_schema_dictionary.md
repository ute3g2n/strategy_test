# Phase 0 Schema Dictionary

- 作成日: 2026-08-02
- 準拠文書: `plan/Phase0_Step0前_実行基盤準備.md`

## ID Prefix

| 対象 | Prefix | 例 |
|---|---|---|
| Exposure | `EXP` | `EXP-EQ-US-SP500` |
| Vehicle | `VEH` | `VEH-FUT-CME-MES` |
| Candidate | `CAN` | `CAN-EXP-EQ-US-SP500-VEH-FUT-CME-MES-IBKR` |
| Evidence | `EVD` | `EVD-20260802-0001` |
| Source | `SRC` | `SRC-CME-0001` |
| Score run | `SCR` | `SCR-20260802-0001` |
| Gate run | `GTE` | `GTE-20260802-0001` |
| Prompt run | `RUN` | `RUN-20260802-0001` |
| Human approval | `APR` | `APR-H0-20260802-0001` |

## Candidate Schema

```text
candidate_id
exposure_id
vehicle_id
exposure_name_ja
asset_class
risk_cluster
vehicle_type
symbol
exchange_or_venue
broker
broker_contract_id
currency
long_available
short_available
api_order_available
api_account_available
japan_resident_eligible
trading_hours
tick_size
contract_multiplier
minimum_quantity
last_trade_rule
first_notice_rule
physical_delivery_risk
margin_initial_jpy
margin_maintenance_jpy
median_daily_volume
median_open_interest
median_spread
history_start
minute_data_available
realtime_data_available
estimated_monthly_data_cost_jpy
commission_roundtrip_jpy
funding_borrow_roll_method
evidence_confidence
evidence_ids
hard_gate_status
hard_gate_reasons
structural_score
robustness_score
final_score
rank_stability
selection_status
review_notes
created_at
updated_at
```

## Evidence Schema

```text
evidence_id
source_id
candidate_id
exposure_id
vehicle_id
fact_type
fact_claim_ja
source_url
source_title
publisher
source_type
primary_or_secondary
accessed_at
published_date
effective_date
expiry_date
quoted_or_summarized_point_ja
confidence
conflict_status
conflict_with_evidence_ids
verified_by_role
verification_notes
```

## Gate Status

| 値 | 意味 |
|---|---|
| `pass` | Gate通過 |
| `fail` | 除外 |
| `conditional` | 条件付き通過 |
| `pending_evidence` | 証拠不足 |
| `research_only` | 研究対象のみ |

## Evidence Confidence

| 値 | 意味 |
|---|---|
| `A` | Critical項目が公式一次情報で確認済み |
| `B` | 主要項目は公式確認、一部が信頼できる二次情報 |
| `C` | 重要な不確実性が残る |
| `Unknown` | 採点・Gate通過に使えない |

## Conflict Status

| 値 | 意味 |
|---|---|
| `none` | 矛盾なし |
| `minor_conflict` | 判断に重大影響なし |
| `major_conflict` | 判断結果が変わる可能性あり |
| `unresolved` | 未解決 |

## Selection Status

| 値 | 意味 |
|---|---|
| `selected_primary` | 最終候補のPrimary Vehicle |
| `selected_fallback` | Fallback Vehicle |
| `reserve` | 補欠 |
| `research_only` | 研究対象のみ |
| `excluded` | 除外 |
| `pending` | 判断保留 |

