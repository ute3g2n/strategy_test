# P3-09 取引エンジンPoC — BLOCKED

実行要求は受領したが、P3-09の発火制御により実engineの起動前に停止した。

## 停止理由

- `RUN-P3-LEAN-PREP-001` はPASSであり、LEANの固定digest、artifact hash、LICENSE、network none/read-only preflight、WSL固定4 Gateは確認済み。
- しかし、`RUN-P3-POC-001` のtrusted scopeは `execution_allowed=false` で、P3-09専用のUnknownが残っている。
- `tests/engine_poc/`、P3-09専用Run Manifest、LEAN実測結果とCoreのparity期待値を結ぶ機械証跡が存在しない。
- そのため、固定入力と期待出力が確定していない状態でLEANを起動すると、結果を後付けで合格扱いする余地が生じる。

## 実行安全性

- LEAN、NautilusTrader、Broker、Paper、Live、Cloud、Secretは起動・使用していない。
- 既存のfixture、期待値、Calendar、性能合格値は変更していない。
- 詳細は `precondition-audit.json` と `verification.json` を正本とする。

## 再開条件

実行計画は `plan/phase3/P3-08R_実行計画書_2026-08-10.md` に固定した。

1. `tests/engine_poc/` にP3-09専用の実行入口を作成し、レビューする。
2. `RUN-P3-POC-001` Run Manifestへdigest、fixture hash、Calendar/timeframe/Adapter版、code revision、出力schemaを固定する。
3. LEAN/Core parityの期待出力を機械検証可能な証跡として固定する。
4. trusted scopeのUnknownを解消し、`execution_allowed=true`に更新したうえで、再度P3-09を実行する。
