# Human Gate ユーザー承認意思表示

- Run ID: `RUN-P2-IC-001-WSL`
- ユーザー意思表示: 承認します
- USER_APPROVAL_DECLARED=1
- 記録日: 2026-08-07
- HEAD commit: `0ba78f9ab22b46794eab8f5b2da98b732ea2fd81`
- fixture SHA-256: `sha256:94022229698e972353b8ec9537f455af5cb29d47253f5f2a1ed5d33b08b50169`
- 実差分 SHA-256: `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

## 状態

このプロジェクトでは、ユーザーが明示的に「承認します」と伝えた時点でHuman Gateを承認済みとする。Runnerはこの宣言とRun IDを照合し、機械Gate、レビュー、hash、fixture、scopeの条件が通っていれば `PASS` にする。秘密鍵による署名やworktree外の承認JSONは要求しない。
