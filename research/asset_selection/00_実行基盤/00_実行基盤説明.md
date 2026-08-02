# Phase 0 Foundation README

- 作成日: 2026-08-02
- 対象工程: Phase 0 Step 0前の実行基盤準備
- 参照計画: `plan/Phase0_Step0前_実行基盤準備.md`

## 目的

このディレクトリは、現代に適した取引アセット調査を再現可能に進めるための共通ルールを置く場所である。

ここでは候補アセットの調査、採点、バックテストは行わない。Step 0以降の成果物が同じschema、同じEvidence規則、同じ承認Gateで作られるようにする。

## 含まれるファイル

| ファイル | 内容 |
|---|---|
| `00_schema_dictionary.md` | 共通schemaとstatus値 |
| `00_prompt_run_log_template.csv` | Prompt実行ログのテンプレート |
| `00_human_approval_log_template.csv` | Human Gate承認ログのテンプレート |
| `00_evidence_registry_template.csv` | Evidence registryのテンプレート |
| `00_execution_checklist.md` | Step 0開始前チェックリスト |

## 運用ルール

- Evidence、承認ログ、Prompt実行ログは追記専用とする。
- 旧版を消さず、新版を作る。
- `Unknown`を`pass`扱いにしない。
- Candidateごとの最適化を行わない。
- Human Gateを通過するまで、次工程で禁止された作業を開始しない。

