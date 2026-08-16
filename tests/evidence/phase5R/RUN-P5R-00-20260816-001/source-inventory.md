# P5R-00 ソース確認記録

- Run ID: `RUN-P5R-00-20260816-001`
- 実行日: 2026-08-16（Asia/Tokyo）
- 対象: 要件v3、P5R再構成提案、P5完了判定、統合台帳、既存P5ローカルEvidence、現行Application/Backtest/UI/品質Gate定義
- 実行範囲: 読み取りのみ。外部通信、追加Data取得、Provider変更、Secret読取り、Broker接続、注文、実資金は行っていない。

## 確認した既存の根拠

| 分類 | 根拠 | P5Rでの扱い |
|---|---|---|
| Data | `tests/evidence/phase5/RUN-P5-09-BINANCE-001/quality/quality-report.json`、`period-split.json`、既存normalized/derived | 既存ローカル証跡を読取り専用で使用する。新規取得はしない。 |
| Core | `src/autotrade/backtest/runner.py` と `tests/backtest/` | 既存Coreの契約を壊さず、Application Adapterから呼ぶ。 |
| Application | `src/autotrade/application/` | P4境界をP5Rの実結果契約へ拡張する。UIへCore内部型を漏らさない。 |
| UI | `ui/mock/` | 固定ダミー表示を廃止し、P5R用の実Application API呼出しへ接続する。 |
| 品質Gate | `scripts/quality_gate/trusted_scopes.json` | P5R専用scopeをH1後に登録する。登録前にtest subprocess/Playwrightを実行しない。 |

## P5R-H0へ引き渡す未解決事項

- Provider利用・保持・再配布条件、P5-08のhost isolation、P5時点のchild Agent未起動、execution costの実測は `P5R-UNK-001` としてOPENのままにする。
- fee/slippageは実測市場コストではなく、P5Rで明示する仮定値である。実市場への適合性や利益を保証しない。
- P5RはBacktest製品化のみで、複数運用Unit、Portfolio、実運用Risk、OMS、Forward、Shadow、Paper、Live、Broker、実注文、実資金を含めない。
