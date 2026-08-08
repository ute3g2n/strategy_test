# P2-07 WSL同期ブロッカー

- 実行Run: `RUN-P2-DQR-001`
- 対象: `/home/oue/strategy_test`
- Windows側trusted scope: 登録済み
- WSL側確認コミット: `0ba78f9`
- WSL側結果: `Run ID is not the fixed WSL scope`、exit code 20
- 原因: WSLクローンが、任意のtrusted scopeを読む現行wrapperとP2-07成果物をまだ取得していない。
- 対応: WSLへ書込み・コピーを行わず、ユーザーによる `git pull --ff-only` 後に同一コマンドを再実行する。
