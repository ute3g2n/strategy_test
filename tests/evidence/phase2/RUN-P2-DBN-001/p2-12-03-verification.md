# P2-12-03 実DBN Replay・WSL隔離検証の結果

- Run: `RUN-P2-DBN-001`
- 結果: **BLOCKED（安全停止）**
- 直接の理由: `UNK-P2-13` と `UNK-P2-14` が未解消のため、固定4 Gateを始める前に停止した。
- 正本の実行ID: `cfab929d6d12473b9d7633691e4eeb69`。試行履歴は[こちら](./p2-12-03-attempt-history.md)。

## 確認できたこと

- ユーザーが許可したWindows側のDBN一件だけを使用した。
- 入力のSHA-256は実行前後とも `8fd0286a477e073c83e8306c4e1a8ebec3af693141010563edd7e0ec1990b65e` で一致した。
- WSL上の保護入力は `root:autotrade-replay:0440` であり、専用グループの実行アカウントだけが読める。
- WSLはネットワークなしで動かし、外向き通信経路・外向きNICが無いことを確認した。
- プロジェクトのDBNデコーダは、実DBNを `ohlcv-1m` の4レコードとして読取った。
- デコーダは通常の実行アカウントで動かした。管理者権限でプロジェクトコードを動かしていない。

## 作らなかったもの

- `NormalizedBar`、`MarketEvent`、Replayの確定結果は作っていない。
- formatter / lint / 型検査 / pytest の4 Gateは開始していない。Unknownが残る状態で通過扱いにしないためである。

やさしい説明: 本物の箱を安全な部屋で読めるところまでは確認できました。でも「いつ届いた箱か」と「箱の番号が何の商品か」が分からないので、翻訳したデータや売買の合図は一つも作りませんでした。安全のために止まった、正しい停止です。

## 次の条件

既存証跡からRaw受信UTC時刻とCatalog対応を確定できなければ、必要最小限の新規取得についてH2-2を改めて承認してもらう。その後にだけ、正規化・MarketEvent・Replay・固定4 Gateを再実行する。
- 2026-08-08T21:42:34Z UTC（WSL実行ID: `2c62d9e032ff4759bb54a187f8bfc6c9`）に、再取得Raw（SHA-256 `sha256:0483e011f5d406053591d1ac9869cde349634e9e612794eb7e0189657ea1ef2d`）を正式入口から確認した。実行前後hash一致、networkingMode=none、4件のDBN読取りを確認し、`UNK-P2-15`で固定4 Gate開始前にBLOCKEDとなった。受信UTCとCatalog対応は別証跡で確定済みである。正本は `wsl-verification-capture.json` と `automation/run-test-summary.json`。
