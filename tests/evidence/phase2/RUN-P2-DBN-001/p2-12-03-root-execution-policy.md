# P2-12-03 root実行方針（2026-08-09）

プロジェクトコードはroot権限で実行してよい。本番運用ではroot実行を想定する。

- `run_isolated_p2.ps1 -RunAsRoot`: WSL内のdecoderと品質Gateをrootで実行する。
- `-RunAsRoot`なし: WSLの既定ユーザーで実行する。
- root実行を理由にRunを停止したり、証跡を不採用にしたりしない。

次の確認は、どちらの実行ユーザーでも必須である。

- 保護入力の場所・所有者・権限・読込前後SHA-256
- trusted scopeとtarget_only
- networkingMode=none、外部接続禁止
- 固定4 Gate、Data Gateのfail-closed、Secret非出力

やさしい説明: 強い権限でも普通の権限でも翻訳機を動かせます。どちらで動かしたかを記録し、読む箱と確認テストは固定します。
