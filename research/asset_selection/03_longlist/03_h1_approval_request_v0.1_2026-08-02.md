# H1 Approval Request - P03 Longlist v0.1

- Step ID: P03
- Status: Approved with conditions on 2026-08-02
- Created at: 2026-08-02T13:36:30+09:00

## 承認対象

- `research/asset_selection/03_longlist/03_longlist_candidates_v0.1_2026-08-02.csv`
- `research/asset_selection/03_longlist/03_longlist_coverage_report_v0.1_2026-08-02.md`
- `research/asset_selection/sources/03_source_index_v0.1_2026-08-02.csv`

## H1判断項目

以下を確認し、P04へ進んでよいか判断する。

1. Longlistの母集団として、154 Candidate/Vehicle rows、129 Unique exposureを採用してよい。
2. P03 v0.1は先物中心のLonglistとし、ETF/CFD/Spot FX/Crypto spotは必要に応じて後続または別Trackで追加検討する。
3. P04では、各候補の日本居住者アクセス、Broker/API対応、デモ口座可否、ショート可否、最小取引単位、データ取得方法を検証する。
4. この段階では、Backtest結果・過去収益・個別パラメータ最適化による絞り込みを行っていないことを承認する。

## 推奨Decision

`approved_with_conditions`

理由:

- P03 v0.1は先物Trend Following向けの母集団として十分な広さを持つ。
- ただし、ETF/CFD/Spot FX/Crypto spotを同一母集団に混ぜると、税務・API・取引コスト・ショート可否・データ品質の評価軸が大きく変わるため、P04以降では先物Trackを主Trackとして進め、必要に応じて別Trackで追加するのが安全。

## 返信テンプレート

P04へ進む場合は、次の形式で回答する。

```text
H1 Decision:
- decision: approved_with_conditions
- approver: owner
- decision_at: 2026-08-02
- approved_scope:
  - research/asset_selection/03_longlist/03_longlist_candidates_v0.1_2026-08-02.csv
  - research/asset_selection/03_longlist/03_longlist_coverage_report_v0.1_2026-08-02.md
  - research/asset_selection/sources/03_source_index_v0.1_2026-08-02.csv
- conditions:
  - P04は先物Trackを主Trackとして進める
  - ETF/CFD/Spot FX/Crypto spotは必要時に別Trackで追加調査する
- rejected_reasons:
- next_allowed_step: P04
- notes:
```

## Actual Decision

```text
H1 Decision:
- decision: approved_with_conditions
- approver: owner
- decision_at: 2026-08-02
- approved_scope:
  - research/asset_selection/03_longlist/03_longlist_candidates_v0.1_2026-08-02.csv
  - research/asset_selection/03_longlist/03_longlist_coverage_report_v0.1_2026-08-02.md
  - research/asset_selection/sources/03_source_index_v0.1_2026-08-02.csv
- conditions:
  - P04は先物Trackを主Trackとして進める
  - ETF/CFD/Spot FX/Crypto spotは必要時に別Trackで追加調査する
- rejected_reasons:
- next_allowed_step: P04
- notes:
```
