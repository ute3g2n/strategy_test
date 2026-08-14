# Step 08 非hash運用パイロット記録

実施日: 2026-08-15

## パイロット結果

| ケース | 実施 | 結果 | 判定方法 |
|---|---|---|---|
| 新規Markdown | in-memory候補 | ALLOW | path、schema、stateのみ。管理hashの計算・保存・比較なし |
| 新規HTMLとindex link | `doc/index.html`の既存導線を確認 | PASS | HTMLParser、相対リンク文字列、path境界を確認 |
| HTML大幅変更 | AI foundation HTML候補 | ALLOW | HTML構造、見出し、非hashポリシーを確認 |
| source変更 | application source候補 | ALLOW | Python構造とA95静的候補判定を確認 |
| Phase/Step受入変更 | path、schema、link、protected目的、stateの候補 | ALLOW | 管理hash一致を要求しないことを確認 |
| protected hash失敗 | raw/DBN/replay/application markerの既存fail-closedテスト | PASS | 不一致を無視せず、保護境界で停止するテストを実行 |
| 用途不明hash | `checksum for convenience` | NEEDS_HUMAN_GATE | A95の自動許可なし |

## 機械検証

- `pytest tests/ai_foundation/test_protected_hash_policy_guard.py tests/ai_foundation/test_nonhash_pilot_scenarios.py tests/market_data/test_raw_normalized_store_contract.py tests/market_data/test_p2_12_dbn_replay_contract.py tests/application/test_p4_07_execution.py -q`: `55 passed`。
- 実測経過時間: `1932 ms`（同一ローカル実行）。
- A95候補判定: management候補 `BLOCKED`、protected data/repro候補は目的付き`ALLOW`、用途不明候補は`NEEDS_HUMAN_GATE`。
- HTML構造、doc/index link、JSON schema、相対path、Secret文字列の持込みなし、状態出力を確認した。
- パイロットスクリプト・テストではhash値を取得・保存・比較せず、management hash retryは0回だった。
- token消費量はこの実行環境から取得できないため、推測値を記録しない。今後は必要ならruntime側の利用量計測を別途設計する。
- runtime dispatchはthread limitで起動不能だった。未起動を独立レビュー済みとは扱わず、Step 08 receiptへfallbackを記録した。

## 保護境界

raw payload、DBN、fixture、replay、application markerのprotected不一致は、管理hash不一致として再試行せず、それぞれの既存fail-closedテストで拒否されることを確認した。protected hashを削除・弱体化する変更はパイロット完了とはしない。

## 権限適用

文章管理基盤と廃止対象の管理用hashチェックを強制スキップして完了する。安全・データ・再現性に直結する保護対象hashは維持する。外部I/O、Secret、WSL、Broker、Live、Git writeは実施していない。
