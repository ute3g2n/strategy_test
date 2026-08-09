# RUN-P3-M30-001 ローカル品質確認

- 固定fixture・品質Gate契約: 40 passed
- formatter / lint / mypy: 実行時点でPASS
- M30通常RED: 10 failed。未実装の `autotrade.strategy` / `autotrade.backtest` を明示して失敗しており、skip/xfailは0件。
- H3-1Rが未承認のため、trusted scopeの固定4 GateをPASSとして実行・主張しない。

中学生向け説明: テストの問題と答えが壊れていないことは確認できました。ただし、答えるプログラムそのものはまだ作っていないので、10問はわざと不合格です。これは「できた」とごまかさないための記録です。
