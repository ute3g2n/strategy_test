# P4-10 run manifest

| 項目 | 値 |
|---|---|
| Step | `P4-10` |
| Phase | `PHASE4_PRODUCT_APPLICATION_BACKTEST_2026_08_11` |
| Run ID | `RUN-P4-04D-001`（既存P4-H1承認Runの参照。新規実行Runではない） |
| Scope mode | `target_only`（P4-06〜08の固定local結果を参照） |
| P4-H2 | `APPROVED`、2026-08-12 |
| P4-10 side effects | 文書・計画・台帳・index・Evidence記録だけ |
| Core | source 36 files、P4-09再照合diff `0` |
| Fixture | SHA-256 `aeb03df1eef3ea836d176a8b0443c45b6bc7f6d01e455fd6026cabf16c536fa4` |
| Application quality | formatter／lint／mypy PASS、pytest `17 passed`（P4-09入力） |
| UI | 21/21、13×10×2＝260 operations、6 expected／0 unexpected／0 skipped、42 screenshots、axe Critical／Serious 0 |
| External browser request | `0`（browser boundary。host isolation証明ではない） |
| DB／migration execution | `NOT_EXECUTED` |
| P5 implementation | `NOT_STARTED` |
| External I/O／Secret／Broker／Paper／Live | `0／NOT_STARTED` |

## Target contract

- P4-04A〜D、P4-06〜09の正式HTML／ログ／Evidenceをread-onlyで入力にする。
- `src/autotrade/backtest`、`src/autotrade/market_data`、`src/autotrade/strategy`は変更しない。
- `UNK-P3-01/05/07`、`Q-243`、`RQV2-BLK-001`、`UNK-P4-04B-001〜005`、`UNK-P4-04D-004`、`UNK-P4-UI-002`をPASSにしない。
- DB作成、migration、repository、fixture、Application／UI source、依存、WSL、外部Data、Secret、外部I/Oは発火しない。
- 完了HTML、P4-10ログ、Phase5入力、dispatch／verification／self-review、doc/index、統合台帳を相互リンクする。
