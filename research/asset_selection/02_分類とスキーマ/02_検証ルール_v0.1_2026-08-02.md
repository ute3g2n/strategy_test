# Phase 0 Validation Rules

- 文書状態: draft
- 作成日: 2026-08-02
- Step ID: P02

## 1. 共通Validation

- Required列は空欄不可。
- ID列は一度発行したら再利用しない。
- `Unknown`を`pass`扱いにしない。
- Candidateを削除せず、除外時は`selection_status=excluded`または`hard_gate_status=fail`にする。
- 日付または時刻はISO 8601形式を推奨する。
- 複数IDはセミコロン区切りにする。

## 2. Candidate Validation

| Rule ID | Rule | Severity |
|---|---|---|
| CV-001 | `candidate_id`、`exposure_id`、`vehicle_id`は必須 | critical |
| CV-002 | `asset_class`はtaxonomy定義値のみ | critical |
| CV-003 | `vehicle_type`はtaxonomy定義値のみ | critical |
| CV-004 | `japan_resident_eligible=unknown`のCandidateはG1 pass不可 | critical |
| CV-005 | `api_order_available=unknown`のCandidateはG2 pass不可 | critical |
| CV-006 | `api_account_available=unknown`のCandidateはG2 pass不可 | critical |
| CV-007 | `contract_multiplier`、`minimum_quantity`がunknownならG5またはG6 pass不可 | critical |
| CV-008 | `physical_delivery_risk=high`はG9で条件または除外理由を要求 | high |
| CV-009 | `evidence_confidence=Unknown`は採点不可 | critical |
| CV-010 | `selection_status=selected_primary`はP11以前に使用しない | high |

## 3. Evidence Validation

| Rule ID | Rule | Severity |
|---|---|---|
| EV-001 | `source_url`、`source_title`、`publisher`は必須 | critical |
| EV-002 | Critical fact_typeは原則`primary_or_secondary=primary`を要求 | high |
| EV-003 | `confidence=Unknown`はGate根拠に使用不可 | critical |
| EV-004 | `conflict_status=major_conflict`または`unresolved`はCritical Gate pass不可 | critical |
| EV-005 | `stale` evidenceはCritical判定に使用不可 | critical |
| EV-006 | Broker/API/Japan eligibilityは調査日を必ず記録 | critical |
| EV-007 | Fee、margin、market data costは再確認期限を必ず記録 | high |

## 4. Gate Validation

- G1～G10のCritical項目に`Unknown`がある場合は`pass`不可。
- `conditional`の場合は条件を明記する。
- `research_only`は最終Live候補30～50件に含めない。
- `fail`または`pending_evidence`には理由を必ず記録する。

## 5. Score Validation

- Hard Gate通過候補だけ採点する。
- P08ではTrend頑健性15点を採点しない。
- P08では85点部分を100点へ再換算した`structural_score_pretest`を使う。
- P10以前にBacktest結果をScorecard weightへ反映しない。
- Evidence factorとOperational penaltyの理由を記録する。

## 6. Bias Control Validation

- P03 Longlistでは過去収益で候補を除外しない。
- Candidate別にLookback、Stop、Roll ruleを最適化しない。
- Backtest ProtocolはP09で事前登録し、H3承認後にP10へ進む。
- Red Team findingは元Scoreを直接上書きせず、修正要求として記録する。

## 7. P03開始条件

P03へ進むには次が必要。

- `02_taxonomy_v0.1_2026-08-02.md`
- `02_candidate_schema_v0.1_2026-08-02.csv`
- `02_evidence_schema_v0.1_2026-08-02.csv`
- `02_validation_rules_v0.1_2026-08-02.md`

P03ではWeb検索が始まるため、P02成果物の分類名と必須列を変更する場合はP03開始前に行う。
