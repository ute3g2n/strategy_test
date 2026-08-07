# WSL clone への execution ID 引継ぎ失敗

## 失敗結果

Windows側の `run_test.ps1` は `FAILED / wrapper_exit_code=1` で終了した。`run-test-summary.json` と `host-runner.json` に、WSL runnerが `WSL_HOST_WRAPPER_EXECUTION_ID` を受け取れず停止した記録がある。

## 原因分類

実装と同期手順の問題。Windows PowerShellで設定した任意の環境変数は、`wsl.exe` 内のLinuxプロセスへ自動で引き継がれない。さらに今回の `/home/oue/strategy_test` はWindows側の未コミット修正より古いWSL cloneだった。

## 修正方針

host wrapperから execution ID をLinux runnerの第3引数として明示的に渡し、Linux runnerは環境変数がなくても第3引数を使う。Windows側とWSL側を同じ修正コミットへ同期してから再実行する。

## 安全な停止

今回の実行は固定4 Gate開始前に停止した。`restore.json` は `RESTORED` で、外部ネットワーク、Databento、Broker、Secret、実データ、実取引は使用していない。4 Gate成功やBLK-RUN-003解消の証拠には使わない。
