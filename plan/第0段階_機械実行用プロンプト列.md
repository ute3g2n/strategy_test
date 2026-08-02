# Phase 0: 機械実行用プロンプト列

- 文書状態: 初版ドラフト
- 基準日: 2026-08-02
- 上位計画: `plan/Phase0_現代に適した取引アセット調査計画書.md`
- 実行基盤: `plan/Phase0_Step0前_実行基盤準備.md`
- 目的: この文書のPromptを上から順番に実行することで、現代に適した取引アセット調査・採点・最終候補30～50件選定まで完了できるようにする

> 本文書はAIエージェントへ順番に投入するための実行用Prompt列である。投資助言ではなく、研究・システム設計のための調査手順である。

---

## 0. 実行方法

この文書のPromptを、`P00`から`P13`まで順番に実行する。

原則:

- 1つのPromptが完了してから次のPromptへ進む。
- 各Promptは、必要な入力ファイル、出力ファイル、品質Gate、停止条件を自分で確認する。
- Human Gateが必要な箇所では、AIは承認依頼文を出して停止する。
- ユーザーが承認した後、次のPromptへ進む。
- Web調査が必要なPromptでは、公式一次情報を優先してWeb検索を行う。
- Data購入、外部サービス契約、Live設定反映は、明示承認があるまで行わない。

このPrompt列は、既存計画書内のRole別Promptより優先して使う。

---

## 1. 共通実行Header

各Promptの先頭には、以下の共通Headerを含める。

```text
You are executing Phase 0 asset selection research for a Japanese resident automated Turtle-style trend-following system.

Primary objective:
Select 30 to 50 modern tradable exposures and 3 to 5 initial implementation exposures for a Turtle-style trend-following automated trading system.

User constraints:
- User is a Japan resident.
- Interactive Brokers Japan is the first broker candidate.
- Live starting capital is under 1,000,000 JPY.
- Initial monthly total operating budget target is under 10,000 JPY.
- Long and short must both be evaluated.
- Original Turtle strategy and modernized variants must be compared.
- Initial implementation target is 3 to 5 markets.
- Final research target is 30 to 50 exposures.
- Do not provide investment advice.

Required reference documents:
- plan/Phase0_現代に適した取引アセット調査計画書.md
- plan/Phase0_Step0前_実行基盤準備.md
- plan/自動トレードシステム_要件定義書.md
- research/タートルズ・トレンドフォロー戦略.md

Global rules:
- Execute only the current prompt's step.
- Do not skip required prior outputs. If missing, stop and report the missing files.
- Do not invent facts, URLs, fees, margin, eligibility, or API capabilities.
- Use official primary sources for critical facts whenever possible.
- Record source URL, publisher, accessed_at, effective_date or published_date, confidence, and conflict_status.
- Do not treat Unknown as Pass.
- Do not optimize candidate-specific strategy parameters.
- Do not use backtest performance to build the initial longlist.
- Preserve all assumptions, conflicts, and unresolved items.
- Write outputs only to the specified step directory.
- Append a Prompt Run Log entry.
- At Human Gate checkpoints, stop and ask the user for approval before the next gated step.
```

---

## P00: Foundation確認・不足補完

```text
[共通実行Headerを適用]

Step ID: P00
Role: Foundation Orchestrator

Task:
Phase 0を機械的に実行できる状態か確認し、不足している実行基盤ファイルがあれば作成・補完してください。

Inputs:
- plan/Phase0_現代に適した取引アセット調査計画書.md
- plan/Phase0_Step0前_実行基盤準備.md
- plan/Phase0_機械実行用プロンプト列.md
- plan/自動トレードシステム_要件定義書.md

Required checks:
1. research/asset_selection配下にStep別ディレクトリがあること。
2. 00_foundation配下にschema辞書、Evidence template、Prompt run log template、Human approval log templateがあること。
3. Candidate、Evidence、Gate、Score、Prompt Run、Human Approvalのschemaが存在すること。
4. Unknown、Pending、Conflictの扱いが定義されていること。
5. Human Gate H0～H5の承認条件が定義されていること。

If missing:
- Create the missing directory or template.
- Do not start asset research.

Outputs:
- research/asset_selection/00_foundation/00_foundation_status_v0.1_2026-08-02.md
- research/asset_selection/logs/00_prompt_run_log_v0.1_2026-08-02.csv

Completion condition:
- P01 can start without missing foundation files.
```

---

## P01: Step 0 Research Charter作成

```text
[共通実行Headerを適用]

Step ID: P01
Role: Research Charter Designer

Task:
Phase 0のResearch Charterを作成し、調査Scope、Hard Gate、Scorecard、Bias対策、Human Gate H0の承認項目を凍結候補としてまとめてください。

Inputs:
- plan/Phase0_現代に適した取引アセット調査計画書.md
- plan/Phase0_Step0前_実行基盤準備.md
- research/asset_selection/00_foundation/00_foundation_status_v0.1_2026-08-02.md

Required contents:
- 調査目的。
- 対象資産クラス。
- 対象外資産クラス。
- ExposureとVehicleの評価単位。
- 最終30～50件の定義。
- 初期3～5件の定義。
- Hard Gate G1～G10の正式定義。
- Scorecard 100点配分。
- Evidence confidence定義。
- 情報鮮度基準。
- 過剰適合、Selection bias、Survivorship bias対策。
- Human Gate H0承認Checklist。

Rules:
- Backtest結果や過去収益を使って候補を絞らない。
- Candidate別Parameter最適化を許可しない。
- UnknownをPassにしない。

Outputs:
- research/asset_selection/01_charter/01_research_charter_v0.1_2026-08-02.md
- research/asset_selection/01_charter/01_h0_approval_checklist_v0.1_2026-08-02.md
- research/asset_selection/logs/01_prompt_run_log_v0.1_2026-08-02.csv

Human Gate:
- H0承認が必要。
- 出力後、H0承認依頼文を作成して停止してください。
```

---

## P02: Step 1 Taxonomy・Schema設計

```text
[共通実行Headerを適用]

Step ID: P02
Role: Taxonomy and Schema Architect

Task:
H0承認済みResearch Charterに基づいて、資産分類、Exposure分類、Vehicle分類、Risk cluster、出力schemaを確定してください。

Inputs:
- research/asset_selection/01_charter/01_research_charter_v0.1_2026-08-02.md
- research/asset_selection/01_charter/01_h0_approval_checklist_v0.1_2026-08-02.md
- research/asset_selection/00_foundation/00_schema_dictionary.md

Required contents:
- Asset class taxonomy。
- Exposure taxonomy。
- Vehicle taxonomy。
- Risk cluster分類。
- Candidate ID生成ルール。
- Exposure ID生成ルール。
- Vehicle ID生成ルール。
- Evidence fact_type一覧。
- CSV schemaと必須列。
- Validation rule。

Outputs:
- research/asset_selection/02_taxonomy_schema/02_taxonomy_v0.1_2026-08-02.md
- research/asset_selection/02_taxonomy_schema/02_candidate_schema_v0.1_2026-08-02.csv
- research/asset_selection/02_taxonomy_schema/02_evidence_schema_v0.1_2026-08-02.csv
- research/asset_selection/02_taxonomy_schema/02_validation_rules_v0.1_2026-08-02.md
- research/asset_selection/logs/02_prompt_run_log_v0.1_2026-08-02.csv

Completion condition:
- P03のLonglist作成で使える分類とschemaが揃っている。
```

---

## P03: Step 2 Web Longlist作成

```text
[共通実行Headerを適用]

Step ID: P03
Role: Multi-Asset Longlist Scout

Task:
Web検索を使い、公式情報を中心に、資産クラス横断のLonglistを作成してください。候補発見が目的であり、採点や除外はまだ行わないでください。

Inputs:
- research/asset_selection/01_charter/01_research_charter_v0.1_2026-08-02.md
- research/asset_selection/02_taxonomy_schema/02_taxonomy_v0.1_2026-08-02.md
- research/asset_selection/02_taxonomy_schema/02_candidate_schema_v0.1_2026-08-02.csv

Web research scope:
- Futures and micro futures.
- FX and currency futures.
- Equity index futures and ETFs.
- Rates futures and ETFs.
- Energy futures.
- Metals futures.
- Agricultural futures.
- Volatility products.
- Crypto spot, futures, and perpetuals where Japan resident access might be possible.
- CFDs only as candidate discovery, with official broker verification deferred to P04.

Required sources:
- Exchange official product lists.
- Broker product pages.
- Regulator or official restriction pages where relevant.
- Data vendor coverage pages where useful for discovery.

Required output fields:
- exposure_id
- exposure_name_ja
- exposure_name_en
- asset_class
- risk_cluster
- vehicle_type
- symbol
- exchange_or_venue
- broker_or_possible_broker
- source_url
- source_title
- publisher
- accessed_at
- discovery_notes

Targets:
- 100 to 200 exposures if possible.
- 150 to 300 candidate vehicles if possible.

Rules:
- Do not exclude based on historical performance.
- Do not mark eligibility as confirmed unless official source supports it.
- Use `pending_evidence` for unresolved eligibility or API questions.

Outputs:
- research/asset_selection/03_longlist/03_longlist_candidates_v0.1_2026-08-02.csv
- research/asset_selection/03_longlist/03_longlist_coverage_report_v0.1_2026-08-02.md
- research/asset_selection/sources/03_source_index_v0.1_2026-08-02.csv
- research/asset_selection/logs/03_prompt_run_log_v0.1_2026-08-02.csv

Human Gate:
- H1承認が必要。
- 出力後、Longlist coverage、重複、Source方針の承認依頼文を作成して停止してください。
```

---

## P04: Step 3 公式Evidence検証

```text
[共通実行Headerを適用]

Step ID: P04
Role: Evidence, Broker, and Eligibility Verifier

Task:
H1承認済みLonglistについて、公式一次情報を使い、日本居住者利用可否、Broker取扱、API、Long/Short、契約仕様、取引時間、主要制約を検証してください。

Inputs:
- research/asset_selection/03_longlist/03_longlist_candidates_v0.1_2026-08-02.csv
- research/asset_selection/03_longlist/03_longlist_coverage_report_v0.1_2026-08-02.md
- research/asset_selection/02_taxonomy_schema/02_evidence_schema_v0.1_2026-08-02.csv

Web research requirements:
- Open official source pages, not only snippets.
- Prefer broker, exchange, regulator, and data vendor official pages.
- For IBKR, verify Japan entity or Japan-resident relevance where possible.
- For API, verify order, account, position, and market data capabilities separately.
- For futures, verify tick size, multiplier, trading hours, first notice, last trade, and delivery risk where applicable.
- For ETFs and stocks, verify short availability mechanism and delisting/survivorship risks.
- For FX/CFD/Crypto, verify Japan resident access, counterparty, funding, custody, and API constraints.

Outputs:
- research/asset_selection/04_evidence_verification/04_verified_universe_v0.1_2026-08-02.csv
- research/asset_selection/04_evidence_verification/04_evidence_registry_v0.1_2026-08-02.csv
- research/asset_selection/04_evidence_verification/04_pending_conflicts_v0.1_2026-08-02.md
- research/asset_selection/logs/04_prompt_run_log_v0.1_2026-08-02.csv

Rules:
- Critical eligibility/API/margin/contract facts without official evidence must remain `Unknown` or `pending_evidence`.
- Do not remove a candidate silently. If evidence is insufficient, mark it.

Completion condition:
- Each candidate has evidence status and unresolved items are explicit.
```

---

## P05: Step 4 ExposureとVehicleの統合

```text
[共通実行Headerを適用]

Step ID: P05
Role: Exposure-Vehicle Mapper

Task:
Verified universeをExposure単位へ整理し、同一経済Exposure、Proxy、Vehicle重複を統合してください。

Inputs:
- research/asset_selection/04_evidence_verification/04_verified_universe_v0.1_2026-08-02.csv
- research/asset_selection/04_evidence_verification/04_evidence_registry_v0.1_2026-08-02.csv
- research/asset_selection/02_taxonomy_schema/02_taxonomy_v0.1_2026-08-02.md

Required actions:
- 同一Underlying/Index/Commodity/Currency riskを持つCandidateをCluster化。
- Direct exposureとProxy exposureを区別。
- Vehicle差分を記録: contract size, tracking error, funding, roll, borrow, counterparty。
- Primary/Fallbackはまだ最終決定しない。
- Exposure ID変更が必要な場合はmigration mapを作る。

Outputs:
- research/asset_selection/05_exposure_vehicle_map/05_exposure_vehicle_map_v0.1_2026-08-02.csv
- research/asset_selection/05_exposure_vehicle_map/05_duplicate_proxy_report_v0.1_2026-08-02.md
- research/asset_selection/05_exposure_vehicle_map/05_id_migration_map_v0.1_2026-08-02.csv
- research/asset_selection/logs/05_prompt_run_log_v0.1_2026-08-02.csv

Completion condition:
- P06でGate判定できるよう、CandidateとExposureの対応が一意に追跡できる。
```

---

## P06: Step 5 Hard Gate・小口資金実行可能性

```text
[共通実行Headerを適用]

Step ID: P06
Role: Feasibility and Capital Gate Analyst

Task:
各CandidateについてHard Gateと小口資金実行可能性を判定し、Tradable-original、Tradable-modern-only、Research-only、Exclude、Pending-evidenceへ分類してください。

Inputs:
- research/asset_selection/05_exposure_vehicle_map/05_exposure_vehicle_map_v0.1_2026-08-02.csv
- research/asset_selection/04_evidence_verification/04_evidence_registry_v0.1_2026-08-02.csv
- research/asset_selection/01_charter/01_research_charter_v0.1_2026-08-02.md
- research/タートルズ・トレンドフォロー戦略.md

Required calculations:
- Minimum quantity 1N JPY risk.
- 2N stop loss.
- Gap stress loss.
- 4 Unit theoretical stop loss.
- Initial and maintenance margin ratio.
- 3-market and 5-market concurrent holding scenario.
- Commission, spread, funding, and roll cost as ratio to N.
- FX conversion sensitivity with a 10% adverse currency move.

Capital scenarios:
- 500,000 JPY.
- 750,000 JPY.
- 1,000,000 JPY upper-bound scenario.

Rules:
- Unknown margin, N, multiplier, or minimum quantity cannot pass.
- Current-price-dependent numbers must include as-of date.
- Boundary candidates require sensitivity, not rounding-based pass/fail.

Outputs:
- research/asset_selection/06_hard_gate/06_hard_gate_results_v0.1_2026-08-02.csv
- research/asset_selection/06_hard_gate/06_capital_scenarios_v0.1_2026-08-02.csv
- research/asset_selection/06_hard_gate/06_exclusions_pending_v0.1_2026-08-02.md
- research/asset_selection/logs/06_prompt_run_log_v0.1_2026-08-02.csv

Human Gate:
- H2承認が必要。
- 出力後、Hard Gate除外、Capital threshold、Data予算の承認依頼文を作成して停止してください。
```

---

## P07: Step 6 Data Vendor・費用・品質調査

```text
[共通実行Headerを適用]

Step ID: P07
Role: Market Data Vendor Researcher

Task:
H2承認済みのGate通過候補について、BacktestとLiveに必要なデータ取得方法、品質、費用をWeb検索で調査してください。

Inputs:
- research/asset_selection/06_hard_gate/06_hard_gate_results_v0.1_2026-08-02.csv
- research/asset_selection/06_hard_gate/06_capital_scenarios_v0.1_2026-08-02.csv
- research/asset_selection/04_evidence_verification/04_evidence_registry_v0.1_2026-08-02.csv

Web research requirements:
- Use official data vendor, exchange, and broker pages.
- Check historical start, 1-minute bars, tick/BidAsk, volume, open interest.
- Check expired futures, delisted assets, corporate actions, contract definitions.
- Check API limits, download format, correction policy, license, non-display rules.
- Estimate historical one-time cost and realtime monthly cost.
- Separate total monthly operating budget from market_data_budget_jpy.

Budget scenarios:
- Initial 3 to 5 candidates.
- 30 candidates.
- 50 candidates.

Outputs:
- research/asset_selection/07_data_vendor/07_data_vendor_matrix_v0.1_2026-08-02.csv
- research/asset_selection/07_data_vendor/07_data_quality_cost_report_v0.1_2026-08-02.md
- research/asset_selection/07_data_vendor/07_budget_scenarios_v0.1_2026-08-02.csv
- research/asset_selection/logs/07_prompt_run_log_v0.1_2026-08-02.csv

Rules:
- Do not purchase data.
- Do not assume broker historical data is sufficient for long-term research unless limitations are documented.
```

---

## P08: Step 7 構造指標・暫定採点

```text
[共通実行Headerを適用]

Step ID: P08
Role: Structural Market Quality Analyst

Task:
Backtest収益を使わず、Hard Gate通過候補について構造指標と暫定Scoreを計算してください。

Inputs:
- research/asset_selection/06_hard_gate/06_hard_gate_results_v0.1_2026-08-02.csv
- research/asset_selection/07_data_vendor/07_data_vendor_matrix_v0.1_2026-08-02.csv
- research/asset_selection/07_data_vendor/07_data_quality_cost_report_v0.1_2026-08-02.md
- research/asset_selection/04_evidence_verification/04_evidence_registry_v0.1_2026-08-02.csv

Required metrics:
- Spread in bps and as ratio to N.
- Estimated slippage.
- ADV participation.
- Open interest ratio.
- Minimum 1N, 2N, and 4Unit risk.
- Margin ratio by capital scenario.
- Data history length.
- 1-minute availability.
- Missing and correction policy.
- Funding, borrow, roll observability and cost.
- Return correlation and crisis correlation where data is available.
- Exposure uniqueness.
- Evidence confidence.
- Operational penalty.

Scoring:
- Use only the 85 points excluding Trend robustness.
- Re-scale the 85-point score to 100 as `structural_score_pretest`.
- Do not score historical performance.

Outputs:
- research/asset_selection/08_structural_score/08_structural_metrics_v0.1_2026-08-02.csv
- research/asset_selection/08_structural_score/08_structural_scores_v0.1_2026-08-02.csv
- research/asset_selection/08_structural_score/08_data_quality_exceptions_v0.1_2026-08-02.md
- research/asset_selection/logs/08_prompt_run_log_v0.1_2026-08-02.csv

Completion condition:
- P09 can freeze a Backtest Protocol without using candidate-specific optimized parameters.
```

---

## P09: Step 8 Backtest Protocol事前登録

```text
[共通実行Headerを適用]

Step ID: P09
Role: Independent Backtest Protocol Designer

Task:
アセット選定用Backtest Protocolを事前登録し、結果を見る前に固定してください。

Inputs:
- research/asset_selection/08_structural_score/08_structural_scores_v0.1_2026-08-02.csv
- research/asset_selection/07_data_vendor/07_data_vendor_matrix_v0.1_2026-08-02.csv
- research/asset_selection/06_hard_gate/06_hard_gate_results_v0.1_2026-08-02.csv
- research/タートルズ・トレンドフォロー戦略.md

Protocol requirements:
- Entry/Exit: 20/10, 55/20, 100/50, 200/100.
- Long and short.
- Wilder N20.
- Entry-day channel lookahead prevention.
- Low, Base, Stress cost scenarios.
- Predefined futures roll rules.
- Conservative handling of unknown intraday order.
- Development, OOS, and Holdout periods.
- Minimum history and trade count rules.
- Trial registry.
- DSR/PBO or equivalent multiple-testing adjustment plan where feasible.
- Failure and missing-data handling.

Forbidden:
- Candidate-specific best lookback.
- Candidate-specific best stop.
- Changing the protocol after seeing results under the same version.

Outputs:
- research/asset_selection/09_backtest_protocol/09_backtest_protocol_v0.1_2026-08-02.md
- research/asset_selection/09_backtest_protocol/09_parameter_registry_v0.1_2026-08-02.yaml
- research/asset_selection/09_backtest_protocol/09_protocol_approval_checklist_v0.1_2026-08-02.md
- research/asset_selection/logs/09_prompt_run_log_v0.1_2026-08-02.csv

Human Gate:
- H3承認が必要。
- 出力後、Backtest Protocol、Holdout、試行回数の承認依頼文を作成して停止してください。
```

---

## P10: Step 9 固定ルールBacktest・頑健性採点

```text
[共通実行Headerを適用]

Step ID: P10
Role: Quantitative Robustness Evaluator

Task:
H3承認済みBacktest Protocolに従い、候補を固定ルール群で評価し、Trend robustness scoreを作成してください。

Inputs:
- research/asset_selection/09_backtest_protocol/09_backtest_protocol_v0.1_2026-08-02.md
- research/asset_selection/09_backtest_protocol/09_parameter_registry_v0.1_2026-08-02.yaml
- research/asset_selection/08_structural_score/08_structural_scores_v0.1_2026-08-02.csv
- research/asset_selection/07_data_vendor/07_data_vendor_matrix_v0.1_2026-08-02.csv

Execution requirements:
- Use the approved protocol without modification.
- Save protocol hash and data version.
- Save every parameter candidate and cost scenario result.
- Use median, consistency, worst acceptable case, OOS, and cost stress, not each candidate's best run.
- Record failed and missing runs; do not silently exclude them.
- Preserve trial count for multiple-testing review.

Outputs:
- research/asset_selection/10_robustness_backtest/10_robustness_metrics_v0.1_2026-08-02.csv
- research/asset_selection/10_robustness_backtest/10_full_scores_v0.1_2026-08-02.csv
- research/asset_selection/10_robustness_backtest/10_experiment_registry_v0.1_2026-08-02.csv
- research/asset_selection/10_robustness_backtest/10_failed_runs_report_v0.1_2026-08-02.md
- research/asset_selection/logs/10_prompt_run_log_v0.1_2026-08-02.csv

Completion condition:
- P11 can select candidates from full scores, evidence, and correlation constraints.
```

---

## P11: Step 10 分散制約付き30～50件選定

```text
[共通実行Headerを適用]

Step ID: P11
Role: Diversified Candidate Portfolio Selector

Task:
Full score、Evidence、Exposure重複、Correlation cluster、運用集中を考慮して、最終30～50 Exposureと初期3～5 Exposureを選定してください。

Inputs:
- research/asset_selection/10_robustness_backtest/10_full_scores_v0.1_2026-08-02.csv
- research/asset_selection/10_robustness_backtest/10_robustness_metrics_v0.1_2026-08-02.csv
- research/asset_selection/05_exposure_vehicle_map/05_exposure_vehicle_map_v0.1_2026-08-02.csv
- research/asset_selection/06_hard_gate/06_hard_gate_results_v0.1_2026-08-02.csv
- research/asset_selection/04_evidence_verification/04_evidence_registry_v0.1_2026-08-02.csv

Selection rules:
- Select 30 to 50 distinct exposures, not just vehicles.
- Assign one Primary Vehicle per selected exposure.
- Record Fallback Vehicle where useful.
- Do not include Research-only in Live candidate 30 to 50.
- Do not mechanically take top 50 scores.
- Avoid concentration in one asset class, risk factor, broker, venue, currency, or funding mechanism.
- Use normal and crisis correlation clusters.
- Apply weight sensitivity, cost stress sensitivity, and correlation window sensitivity.
- Initial 3 to 5 should prioritize implementation coverage, evidence confidence, capital fit, and operational simplicity, not only expected return.

Outputs:
- research/asset_selection/11_portfolio_selection/11_selection_30_50_v0.1_2026-08-02.csv
- research/asset_selection/11_portfolio_selection/11_initial_pilot_3_5_v0.1_2026-08-02.md
- research/asset_selection/11_portfolio_selection/11_correlation_clusters_v0.1_2026-08-02.csv
- research/asset_selection/11_portfolio_selection/11_selection_tradeoff_report_v0.1_2026-08-02.md
- research/asset_selection/logs/11_prompt_run_log_v0.1_2026-08-02.csv

Completion condition:
- P12 can independently audit all candidate discovery, evidence, scoring, and selection outputs.
```

---

## P12: Step 11 独立監査・Red Team

```text
[共通実行Headerを適用]

Step ID: P12
Role: Independent Red Team Auditor

Task:
あなたは候補発見、Evidence検証、採点、選定を行っていない独立監査者として、全成果物を批判的に監査してください。

Inputs:
- research/asset_selection/03_longlist/03_longlist_candidates_v0.1_2026-08-02.csv
- research/asset_selection/04_evidence_verification/04_evidence_registry_v0.1_2026-08-02.csv
- research/asset_selection/06_hard_gate/06_hard_gate_results_v0.1_2026-08-02.csv
- research/asset_selection/08_structural_score/08_structural_scores_v0.1_2026-08-02.csv
- research/asset_selection/09_backtest_protocol/09_backtest_protocol_v0.1_2026-08-02.md
- research/asset_selection/10_robustness_backtest/10_full_scores_v0.1_2026-08-02.csv
- research/asset_selection/11_portfolio_selection/11_selection_30_50_v0.1_2026-08-02.csv
- research/asset_selection/11_portfolio_selection/11_initial_pilot_3_5_v0.1_2026-08-02.md

Audit items:
- Look-ahead bias.
- Survivorship bias.
- Selection bias.
- Multiple-testing bias.
- Candidate-specific parameter optimization.
- Unknown incorrectly passed.
- Source conflict or stale source.
- Japan resident eligibility weakness.
- Broker/API misread.
- Unit, multiplier, currency conversion, margin, N calculation errors.
- Futures roll and delivery risk.
- Borrow, funding, counterparty, delisting, corporate action risk.
- Score double counting.
- Correlation cluster and exposure duplication.
- Alignment with under 1,000,000 JPY capital and under 10,000 JPY monthly budget.
- Reproducibility and data lineage.

Outputs:
- research/asset_selection/12_red_team/12_independent_audit_v0.1_2026-08-02.md
- research/asset_selection/12_red_team/12_audit_findings_v0.1_2026-08-02.csv
- research/asset_selection/12_red_team/12_required_reruns_v0.1_2026-08-02.md
- research/asset_selection/logs/12_prompt_run_log_v0.1_2026-08-02.csv

Rules:
- Do not overwrite original scores.
- Do not silently fix findings.
- Classify findings as Critical, High, Medium, or Low.
- For each finding, state evidence, impact, remediation, and required rerun.

Human Gate:
- H4承認が必要。
- 出力後、30～50件選定、監査Finding、例外採用の承認依頼文を作成して停止してください。
```

---

## P13: Step 12 最終情報再検証・選定凍結・報告

```text
[共通実行Headerを適用]

Step ID: P13
Role: Final Research Integrator

Task:
H4承認済みの選定結果と監査結果を反映し、最終候補について変化しやすい公式Web情報を再確認したうえで、最終30～50 Exposure、Primary/Fallback Vehicle、初期3～5 Exposureを凍結してください。

Inputs:
- research/asset_selection/11_portfolio_selection/11_selection_30_50_v0.1_2026-08-02.csv
- research/asset_selection/11_portfolio_selection/11_initial_pilot_3_5_v0.1_2026-08-02.md
- research/asset_selection/12_red_team/12_independent_audit_v0.1_2026-08-02.md
- research/asset_selection/12_red_team/12_audit_findings_v0.1_2026-08-02.csv
- research/asset_selection/04_evidence_verification/04_evidence_registry_v0.1_2026-08-02.csv

Final web revalidation:
- Japan resident eligibility.
- Broker availability and trading permission.
- API order, account, position, and market data capability.
- Margin.
- Commission.
- Market data fee.
- Contract specification.
- First notice and last trade.
- Short, borrow, funding, and broker restrictions.

Rules:
- Use official primary sources for revalidation.
- Do not finalize if unresolved Critical audit findings remain.
- Do not change Scorecard weight or Backtest Protocol at final stage.
- Mark stale or conflicting evidence explicitly.
- Do not reflect final output into Live settings.

Outputs:
- research/asset_selection/13_final_selection/13_final_asset_selection_v0.1_2026-08-02.md
- research/asset_selection/13_final_selection/13_final_selection_30_50_v0.1_2026-08-02.csv
- research/asset_selection/13_final_selection/13_initial_pilot_3_5_v0.1_2026-08-02.md
- research/asset_selection/13_final_selection/13_final_evidence_snapshot_v0.1_2026-08-02.csv
- research/asset_selection/13_final_selection/13_h5_approval_checklist_v0.1_2026-08-02.md
- research/asset_selection/logs/13_prompt_run_log_v0.1_2026-08-02.csv

Human Gate:
- H5承認が必要。
- 出力後、初期3～5件、費用、未解決事項、次の実装準備可否の承認依頼文を作成して停止してください。

Completion condition:
- Phase 0 asset selection research is complete when H5 is approved.
```

---

## 2. 完了判定

P13完了後、次が揃っていればPhase 0完了とする。

- 30～50の異なるExposureが選定済み。
- 各ExposureにPrimary Vehicleがある。
- 必要なFallback Vehicleが記録済み。
- 初期3～5 Exposureが選定済み。
- 全候補にEvidence、Score、Risk、選定理由がある。
- Critical監査Findingが0件。
- H5承認Checklistが作成済み。
- Live設定へはまだ反映していない。

