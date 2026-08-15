# P5-09 Quality / Calendar / Cost / Gap / 期間分割 / Holdout 実行ログ

- Step: `P5-09`
- Phase: `PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12`
- Run: `RUN-P5-09-BINANCE-001`
- 実行日: 2026-08-15 (Asia/Tokyo)
- Orchestrator: `AutoTradeProject_ImplementationQuality_Orchestrator_v0_1`
- 判定: `QUALITY_EVIDENCE_COMPLETE_WITH_OPEN_UNKNOWN`

## 1. 実行範囲

P5-08の展開済みBinance Data Vision Spot Kline 1m CSVだけを入力にした。対象は`BTCUSDT`／`ETHUSDT`、期間は`2025-02-24T00:00:00Z`以上`2026-08-01T00:00:00Z`未満、保存・集計Calendarは`CRYPTO_24_7_UTC`である。

P5-09自身は外部通信、環境変数読取、API key／Secret読取、Broker／Paper／Live／Core／P4 DB変更を行っていない。P5-08のProvider条件`UNKNOWN`と外部取得Runのhost isolation`NOT_VERIFIED`は事実として引き継ぎ、P5-09のローカル品質PASSへ変換していない。

## 2. Runtime dispatch

rootは`multi_agent_v1__spawn_agent`／`multi_agent_v1__wait_agent`の可用性を確認し、指定Orchestratorを固定JSON path・`gpt-5.6-terra`で実起動してwaitした。Coordinatorのagent_idは`01a004cb-44c2-74a3-a9d5-6b46fbc94c3a`である（root receiptを正本とする）。

Coordinatorからchild spawn/wait不可の報告を受け、A110／A130／A140／A150／A160／A90／A95は全員未起動と記録した。代替Agent・代替modelは使用せず、独立実行・独立レビュー済みとは扱わない。root/child receipt:

- [root receipt](../../../tests/evidence/phase5/RUN-P5-09-BINANCE-001/dispatch/P5-09-root-runtime-receipt-20260815.json)
- [child receipt](../../../tests/evidence/phase5/RUN-P5-09-BINANCE-001/dispatch/P5-09-child-runtime-receipt-20260815.json)

## 3. TDD・実行・検証

最初に`tests/phase5_external_data/test_binance_quality.py`を作成し、実装未存在によるREDを確認した。その後、標準ライブラリだけで動く`run_binance_quality.py`を実装し、固定fixtureをGREEN化した。

実行コマンド:

```text
py -3.11 scripts/phase5_external_data/run_binance_quality.py
py -3.11 -m pytest -q tests/phase5_external_data
.venv\Scripts\ruff.exe check scripts/phase5_external_data/run_binance_quality.py tests/phase5_external_data/test_binance_quality.py
py -3.11 scripts/ai_foundation/protected_hash_policy_guard.py <P5-09対象ファイル>
```

結果:

| 検査 | 結果 |
|---|---|
| P5-08入力 | 36/36 source checksum verified、対象範囲一致 |
| BTCUSDT / ETHUSDT 1m | 各753,120本、最初2025-02-24 00:00 UTC、最後2026-07-31 23:59 UTC |
| timestamp / UTC / 1分間隔 | PASS |
| 重複・逆行 / OHLCV不整合 | 各0件 |
| gap / zero-fill / imputation | 各0件 / 0件 / 0件 |
| D1 / H4 / H1 / M30 / M15 | 各523 / 3,138 / 12,552 / 25,104 / 50,208本/銘柄 |
| train / validation / holdout | 各447,840 / 129,600 / 175,680本/銘柄、境界重複なし |
| pytest | 9 passed |
| ruff / py_compile / diff check | PASS |
| protected policy guard | 全対象ALLOW |

別の読み取り検査で、Normalizedの月次gzip CSVの連続timestamp、Derived全ファイルの行数・UTC境界・入力本数を再確認し、PASSとなった。

## 4. Cost / Gap / Holdout

- Provider公開Data費用はP5-08記録の`0 USD`を参照した。P5-09の内部使用量は入力展開CSV`244,225,713 bytes`、出力約`99,938,675 bytes`、ローカル処理時間`92.047秒`として測定し、内部金額は未測定のまま記録した。
- Spot fee／slippageは注文・約定がないため未測定。0や実測値へ置換していない。
- Gapは`CRYPTO_24_7_UTC`上で観測0。欠損が発生した場合は市場欠損／配布欠落を推測せず、ゼロ埋め・補間なしで停止する。
- Holdoutは`2026-04-01T00:00:00Z`から`2026-08-01T00:00:00Z`。この品質処理ではチューニングへ再利用していない。Walk-forwardは境界定義のみで、戦略実行・収益性判定は対象外。

## 5. Unknown / Stop / 次Step

| ID | 状態 | 内容 | 再開条件 |
|---|---|---|---|
| `UNK-P5-BINANCE-TERMS-INHERITED` | `OPEN_NOT_PASS` | Providerの利用・保持・再配布条件はP5-08からUNKNOWN | Human/provider terms decision |
| `UNK-P5-DISPATCH-CHILD-001` | `OPEN_NOT_PASS` | 指定child Agent 7体は未起動。self-review fallbackのみ | child dispatchと全receipt完了 |

今回の機械検査にCritical/Highはない。ただしUnknownは残っているため、P5-09をP5全体PASS、P5-H2承認、再配布許可、Broker／Paper／Live適合へ一般化しない。次はP5-10の統合品質レビューである。

## 6. 成果物

- [P5-09正式HTML](../../../doc/phase5/05_実証/10_P5-09_Binance品質・Calendar・Cost_Gap・Holdout.html)
- [Run README](../../../tests/evidence/phase5/RUN-P5-09-BINANCE-001/README.md)
- [execution finish](../../../tests/evidence/phase5/RUN-P5-09-BINANCE-001/execution-finish-20260815.json)
- [manifest](../../../tests/evidence/phase5/RUN-P5-09-BINANCE-001/manifest.json)
- [quality report](../../../tests/evidence/phase5/RUN-P5-09-BINANCE-001/quality/quality-report.json)
- [calendar application](../../../tests/evidence/phase5/RUN-P5-09-BINANCE-001/quality/calendar-application.json)
- [cost-gap](../../../tests/evidence/phase5/RUN-P5-09-BINANCE-001/quality/cost-gap.json)
- [period split](../../../tests/evidence/phase5/RUN-P5-09-BINANCE-001/quality/period-split.json)
- [evidence index](../../../tests/evidence/phase5/RUN-P5-09-BINANCE-001/evidence-index.json)
- [stop decision](../../../tests/evidence/phase5/RUN-P5-09-BINANCE-001/stop-decision.json)
- [regeneration procedure](../../../tests/evidence/phase5/RUN-P5-09-BINANCE-001/regeneration-procedure.md)
