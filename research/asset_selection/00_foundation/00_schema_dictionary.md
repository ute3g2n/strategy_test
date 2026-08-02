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

## Gate Result Schema

```text
gate_run_id
candidate_id
gate_id
gate_name
gate_status
gate_reason
required_evidence_ids
blocking_unknowns
capital_scenario_jpy
calculation_version
checked_at
checked_by_role
review_notes
```

## Score Schema

```text
score_run_id
candidate_id
scorecard_version
execution_liquidity_score
capital_fit_score
access_operations_score
data_quality_cost_score
diversification_score
trend_robustness_score
base_score
evidence_factor
operational_penalty
final_score
confidence
score_reason
metric_refs
evidence_ids
scored_at
scored_by_role
```

## Prompt Run Log Schema

```text
run_id
step_id
role
prompt_version
prompt_text_path
input_files
output_files
model_or_agent
started_at
finished_at
status
errors
assumptions
human_gate_required
rerun_reason
parent_run_id
notes
```

## Human Approval Log Schema

```text
approval_id
human_gate_id
gate_name
input_files
decision
decision_at
approver
approved_scope
rejected_reasons
conditions
next_allowed_step
notes
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

## Unknown / Pending / Conflict Rule

| 状態 | 扱い |
|---|---|
| `Unknown` | Critical項目ではGate通過不可。推定でPassにしない |
| `pending_evidence` | 追加調査対象。担当Role、必要Source、期限を記録する |
| `minor_conflict` | 判断影響が軽微な矛盾。理由を記録して条件付きで継続可能 |
| `major_conflict` | 判断結果が変わる可能性がある矛盾。Critical項目なら保留 |
| `unresolved` | 未解決。Critical項目なら後続Gateへ進めない |

## Selection Status

| 値 | 意味 |
|---|---|
| `selected_primary` | 最終候補のPrimary Vehicle |
| `selected_fallback` | Fallback Vehicle |
| `reserve` | 補欠 |
| `research_only` | 研究対象のみ |
| `excluded` | 除外 |
| `pending` | 判断保留 |

## Human Gate

| Gate | 承認対象 | 未承認時に禁止する作業 |
|---|---|---|
| `H0` | Scope、Hard Gate、Scorecard、Bias対策 | Web Longlist調査 |
| `H1` | Longlist coverage、重複、Source方針 | 詳細Evidence検証 |
| `H2` | Hard Gate除外、Capital threshold、Data予算 | Data購入、詳細Data取得 |
| `H3` | Backtest Protocol、Holdout、試行回数 | 頑健性Backtest |
| `H4` | 30～50件、監査Finding、例外 | 最終選定凍結 |
| `H5` | 初期3～5件、費用、未解決事項 | 実装・Paper準備 |
