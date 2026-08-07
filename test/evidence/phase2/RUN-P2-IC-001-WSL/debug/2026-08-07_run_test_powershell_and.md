# run_test.ps1 PowerShell `-and` エラーのデバッグ記録

## 失敗

Windows PowerShell で `run_test.ps1` を実行すると、`A parameter cannot be found that matches parameter name 'and'` で停止した。

## 原因分類

実装の問題。`Test-Path` の戻り値を括弧で囲まずに `-and` を続けていたため、PowerShell が `-and` を `Test-Path` のパラメーターとして解釈していた。

## 修正

`$preflightIsRecent` を `(Test-Path -LiteralPath $preflightPath) -and (...)` の形へ変更した。処理の意味、対象scope、固定Run ID、固定command、隔離条件は変更していない。

## 再確認

- `tests/quality_gate/test_wsl_quality_gate_contract.py`: GREEN
- PowerShell parser: `run_test.ps1`、`run_isolated_p2.ps1`、`select_automation_evidence.ps1` が成功
- Bash syntax: `run_isolated_p2.sh` が成功
- `git diff --check`: 成功
- 外部ネットワーク、Databento、Broker、Secret、実データ、実取引: 使用なし
