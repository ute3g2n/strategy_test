# Phase 0: Step 0前の実行基盤準備

- 文書状態: 初版ドラフト
- 基準日: 2026-08-02
- 上位計画: `plan/Phase0_現代に適した取引アセット調査計画書.md`
- 要件定義: `plan/自動トレードシステム_要件定義書.md`
- 目的: Step 0以降のアセット調査を、再現可能かつ監査可能な形で進めるための実行基盤を定義する

> 本文書は調査運用の準備文書であり、投資助言ではない。ここでは候補アセットの良し悪しを判断せず、判断に使う器だけを固定する。

---

## 1. この工程の位置づけ

Phase 0計画書のStep 0～12は調査工程である。各StepのPromptは、その工程を実行するAIへの作業指示であり、単純に上から順番に投入するだけでは不十分である。

Step 0へ入る前に、次を固定する。

1. 成果物の保存先。
2. ファイル命名規則。
3. Candidate、Exposure、Vehicle、Evidence、Score、Gate、Run logのschema。
4. `Unknown`、`Pending`、`Conflict`の扱い。
5. Human Gateの承認条件。
6. Prompt実行ログと再実行条件。
7. 役割分担と独立性ルール。

この準備が終わるまで、候補アセットのWeb調査、採点、バックテスト、データ購入は開始しない。

---

## 2. 推奨ディレクトリ構成

Phase 0の成果物は、`research/asset_selection` 配下へ保存する。

```text
research/asset_selection/
  00_foundation/
  01_charter/
  02_taxonomy_schema/
  03_longlist/
  04_evidence_verification/
  05_exposure_vehicle_map/
  06_hard_gate/
  07_data_vendor/
  08_structural_score/
  09_backtest_protocol/
  10_robustness_backtest/
  11_portfolio_selection/
  12_red_team/
  13_final_selection/
  logs/
  sources/
  archive/
```

### 2.1 ディレクトリの役割

| ディレクトリ | 役割 |
|---|---|
| `00_foundation` | 本工程で固定したschema、ルール、実行台帳 |
| `01_charter` | Step 0のResearch Charter |
| `02_taxonomy_schema` | Step 1の分類体系とschema |
| `03_longlist` | Step 2のLonglist |
| `04_evidence_verification` | Step 3の公式情報検証 |
| `05_exposure_vehicle_map` | Step 4のExposureとVehicle統合 |
| `06_hard_gate` | Step 5の除外・保留・資金Scenario |
| `07_data_vendor` | Step 6のデータ源・費用・品質調査 |
| `08_structural_score` | Step 7の構造指標・暫定採点 |
| `09_backtest_protocol` | Step 8のBacktest Protocol事前登録 |
| `10_robustness_backtest` | Step 9の頑健性評価結果 |
| `11_portfolio_selection` | Step 10の30～50件選定 |
| `12_red_team` | Step 11の独立監査 |
| `13_final_selection` | Step 12の最終選定 |
| `logs` | Prompt実行ログ、承認ログ、再実行ログ |
| `sources` | Evidence snapshot、参照URL一覧、PDFメモ |
| `archive` | 旧版成果物、差し戻し版、凍結済み版 |

---

## 3. ファイル命名規則

ファイル名は、`step番号_内容_版_日付`を基本とする。

```text
00_foundation_schema_v0.1_2026-08-02.md
00_prompt_run_log_v0.1_2026-08-02.csv
01_research_charter_v0.1_2026-08-02.md
03_longlist_futures_v0.1_2026-08-02.csv
04_evidence_registry_v0.1_2026-08-02.csv
06_hard_gate_results_v0.1_2026-08-02.csv
```

### 3.1 版管理ルール

| 状態 | ルール |
|---|---|
| Draft | 作業中。後続Stepの正式入力にしない |
| Review | Human Gateまたは監査待ち |
| Approved | 後続Stepの正式入力にできる |
| Superseded | 新版に置き換え済み |
| Frozen | Backtest Protocolや最終選定など、以後変更禁止の版 |

### 3.2 上書き禁止

次のファイルは原則として上書きしない。

- Evidence registry。
- Prompt run log。
- Human approval log。
- Backtest protocol。
- Experiment registry。
- 最終選定ファイル。

修正する場合は新版を作り、旧版を`archive`へ移す。

---

## 4. 共通ID規則

### 4.1 ID Prefix

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

### 4.2 IDの原則

- IDは一度発行したら再利用しない。
- 名称変更があってもIDは維持する。
- ExposureとVehicleは分ける。
- Candidateは`Exposure × Vehicle × Broker/Venue`の組合せで作る。
- 同じExposureに複数Vehicleがある場合は、Candidateを分けて管理する。

---

## 5. Schema定義

### 5.1 Exposure Schema

```text
exposure_id
exposure_name_ja
exposure_name_en
asset_class
risk_cluster
economic_driver
region
base_currency
tradable_thesis
proxy_allowed
notes
created_at
updated_at
status
```

### 5.2 Vehicle Schema

```text
vehicle_id
vehicle_type
symbol
exchange_or_venue
broker
broker_contract_id
currency
contract_multiplier
tick_size
minimum_quantity
trading_hours
settlement_type
first_notice_rule
last_trade_rule
physical_delivery_risk
margin_model
short_mechanism
funding_borrow_roll_method
notes
created_at
updated_at
status
```

### 5.3 Candidate Schema

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

### 5.4 Evidence Schema

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

### 5.5 Gate Result Schema

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

### 5.6 Score Schema

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

### 5.7 Prompt Run Log Schema

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

### 5.8 Human Approval Log Schema

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

---

## 6. Status値

### 6.1 Evidence confidence

| 値 | 意味 |
|---|---|
| `A` | Critical項目が公式一次情報で確認済み |
| `B` | 主要項目は公式確認、一部が信頼できる二次情報 |
| `C` | 重要な不確実性が残る |
| `Unknown` | 採点・Gate通過に使えない |

### 6.2 Conflict status

| 値 | 意味 |
|---|---|
| `none` | 矛盾なし |
| `minor_conflict` | 表現や日付の差異はあるが判断に重大影響なし |
| `major_conflict` | 判断結果が変わる可能性がある |
| `unresolved` | 未解決。Critical項目ならGate通過不可 |

### 6.3 Gate status

| 値 | 意味 |
|---|---|
| `pass` | Gate通過 |
| `fail` | 除外 |
| `conditional` | 条件付き通過。条件を明記 |
| `pending_evidence` | 証拠不足 |
| `research_only` | 研究対象にはできるがLive候補にしない |

### 6.4 Selection status

| 値 | 意味 |
|---|---|
| `selected_primary` | 最終候補のPrimary Vehicle |
| `selected_fallback` | Fallback Vehicle |
| `reserve` | 補欠 |
| `research_only` | 研究対象のみ |
| `excluded` | 除外 |
| `pending` | 判断保留 |

---

## 7. Unknown、Pending、Conflictの扱い

### 7.1 Unknown

- Critical項目の`Unknown`はGate通過不可。
- 非Critical項目の`Unknown`は採点時に減点または保留にする。
- `Unknown`を平均値や推測値で埋めない。
- 推定を置く場合は`assumption`として明記し、Evidenceとは分ける。

### 7.2 Pending

- 追加調査で解消可能な不明点を`pending_evidence`とする。
- Pending項目には担当Role、期限、必要なSource種別を付ける。
- Pendingのまま後続Stepへ進む場合はHuman Gateで明示承認する。

### 7.3 Conflict

- Source間で矛盾がある場合は、片方を黙って捨てない。
- 公式一次情報同士の矛盾は`major_conflict`以上とする。
- Broker公式と取引所公式が矛盾する場合は、Candidate単位で保留する。
- 最新日付だけで勝敗を決めず、適用対象、地域、口座種別、商品種別を確認する。

---

## 8. Role運用ルール

### 8.1 論理Role

| Role | 主責務 |
|---|---|
| Orchestrator | 進行管理、入出力整合、Human Gate準備 |
| Asset Scout | Longlist作成 |
| Evidence Verifier | Source確認とEvidence登録 |
| Broker/Legal Verifier | 日本居住者、Broker、API、口座条件の確認 |
| Data Specialist | データ取得性、費用、品質の確認 |
| Quant Evaluator | 構造指標とBacktest評価 |
| Portfolio Selector | 分散制約付き候補選定 |
| Red Team Reviewer | 独立監査 |
| Final Integrator | 最終報告と凍結 |

### 8.2 独立性ルール

- Asset Scoutは最終採点を行わない。
- Evidence Verifierは過去収益で候補を落とさない。
- Quant EvaluatorはCandidateごとに最良Parameterを選ばない。
- Portfolio SelectorはScore順だけで選ばない。
- Red Team Reviewerは元Scoreを直接編集しない。
- Final Integratorは未解決Critical findingを確定扱いしない。

### 8.3 サブエージェント化の判断

最初は論理Roleとして運用する。次の条件に該当する場合だけ、専用サブエージェントやSkill化を検討する。

- 同じRoleの作業を3回以上反復する。
- 出力schemaの検査を自動化した方が明らかにミスを減らせる。
- Web調査件数が多く、資産クラス別に並列化する価値が高い。
- Red Teamを担当作業から明確に分離する必要がある。

---

## 9. Human Gate運用

| Gate | 位置 | 承認対象 | 未承認時に禁止する作業 |
|---|---|---|---|
| H0 | Step 0後 | Scope、Hard Gate、Scorecard、Bias対策 | Web Longlist調査 |
| H1 | Step 2後 | Longlist coverage、重複、Source方針 | 詳細Evidence検証 |
| H2 | Step 5後 | 除外理由、資金Scenario、Data予算 | Data購入、詳細Data取得 |
| H3 | Step 8後 | Backtest Protocol、Holdout、試行回数 | 頑健性Backtest |
| H4 | Step 11後 | 30～50件、監査Finding、例外 | 最終選定凍結 |
| H5 | Step 12後 | 初期3～5件、費用、未解決事項 | 実装・Paper準備 |

### 9.1 承認Decision

| Decision | 意味 |
|---|---|
| `approved` | 次工程へ進める |
| `approved_with_conditions` | 条件付きで次工程へ進める |
| `rejected` | 差し戻し |
| `paused` | 判断保留 |

---

## 10. Prompt実行規約

### 10.1 共通Prompt Header

各StepのPromptには、次を先頭に付ける。

```text
You are executing Phase 0 asset selection research for a Japanese resident automated Turtle-style trend-following system.

Use the approved schema and file naming rules from:
- plan/Phase0_Step0前_実行基盤準備.md
- plan/Phase0_現代に適した取引アセット調査計画書.md

Rules:
- This is research and system design, not investment advice.
- Do not invent facts, URLs, fees, margin, or eligibility.
- Use official primary sources for critical facts whenever possible.
- Record source URL, publisher, accessed_at, effective_date, and confidence.
- Do not treat Unknown as Pass.
- Do not optimize candidate-specific parameters.
- Preserve all assumptions and unresolved conflicts.
- Write outputs only to the step-specific directory.
- Add a Prompt Run Log entry for this task.
```

### 10.2 実行ログ必須項目

各Prompt実行後に、最低限次を記録する。

- 実行したRole。
- 入力ファイル。
- 出力ファイル。
- 使用したSource。
- 未解決事項。
- 次のHuman Gate要否。
- 再実行が必要な条件。

### 10.3 再実行条件

次の場合は、該当Stepを再実行する。

- Critical Sourceが古くなった。
- Broker、取引所、Data Vendorの仕様が変わった。
- Schema変更により旧出力が不整合になった。
- Red TeamがCriticalまたはHigh findingを出した。
- Human Gateで差し戻された。
- 入力候補Universeが大きく変わった。

---

## 11. Step 0前準備Prompt

この工程自体をAIに実行させる場合は、次のPromptを使用する。

```text
Role: Phase 0 Foundation Orchestrator

Task:
Phase 0 asset selection researchを開始する前に、実行基盤を整備してください。

Inputs:
- plan/Phase0_現代に適した取引アセット調査計画書.md
- plan/自動トレードシステム_要件定義書.md
- plan/chat_history/2026-08-02_自動トレードシステム要件ヒアリング.md

Required outputs:
1. research/asset_selection/00_foundation/00_foundation_readme.md
2. research/asset_selection/00_foundation/00_schema_dictionary.md
3. research/asset_selection/00_foundation/00_prompt_run_log_template.csv
4. research/asset_selection/00_foundation/00_human_approval_log_template.csv
5. research/asset_selection/00_foundation/00_evidence_registry_template.csv
6. research/asset_selection/00_foundation/00_execution_checklist.md

Rules:
- Do not start candidate asset research.
- Do not browse the web except to verify whether a referenced official source format is required.
- Do not create final scores.
- Keep schema compatible with the Phase 0 plan.
- Define all required status values and validation rules.
- Record any unresolved design choices separately.

Completion condition:
- Step 0 can start without ambiguity about where outputs go, what fields are required, how evidence is recorded, and when human approval is needed.
```

---

## 12. Step 0開始条件

Step 0へ進んでよい条件は次の通り。

- 成果物保存先が確定している。
- Candidate、Evidence、Score、Gate、Prompt run、Human approvalのschemaがある。
- `Unknown`、`Pending`、`Conflict`の扱いが定義されている。
- Human Gate H0～H5の承認対象が明確である。
- Prompt実行ログの形式が決まっている。
- Red Teamの独立性ルールが明記されている。
- Step 0の出力先が決まっている。

---

## 13. 未確定事項

| ID | 内容 | 推奨対応 |
|---|---|---|
| FD-01 | 実際の作業成果物をCSV中心にするか、Parquetも初期から使うか | Step 1で決定。初期はCSV、定量データはParquet推奨 |
| FD-02 | 承認者名をどう記録するか | 個人名または`owner`で記録 |
| FD-03 | Web調査Sourceのスクリーンショット保存要否 | Step 3で判断。変化しやすい料金・証拠金は保存推奨 |
| FD-04 | サブエージェントを実際に使うタイミング | Step 2の資産クラス別Longlistから検討 |
| FD-05 | 専用Skill化する範囲 | Phase 0を一巡後に判断 |

---

## 14. 次の実行

この文書を承認した後、次は`Step 0: Research Charter作成`へ進む。

Step 0では、以下を凍結する。

- 調査Scope。
- Hard Gate。
- Scorecard weight。
- Source優先順位。
- Bias対策。
- Human Gate H0の承認Checklist。
