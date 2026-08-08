# P2-08承認後Runの品質Gate

| Gate | 結果 |
|---|---|
| formatter | PASS |
| lint | PASS |
| mypy | PASS（8 source files） |
| pytest | PASS（44 passed） |
| coverage | PASS（80.05%） |
| bounded external request | PASS（HTTP 200 / DBN 22,760 bytes） |

外部取得はH2-2承認後の固定1回だけ実行した。API keyの値は標準出力、ログ、HTML、JSONへ出力していない。WSL固定4 Gateは外部I/Oを再実行せず、同じ対象scopeの静的品質確認として別途実施する。
