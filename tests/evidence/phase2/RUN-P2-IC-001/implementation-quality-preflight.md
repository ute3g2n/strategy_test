# ImplementationQuality preflight

`AutoTradeProject_ImplementationQuality_Orchestrator_v0_1` と既存の `scripts/quality_gate/runner.py` を照合した。

改訂前の結果: `BLOCKED`。Runner は S2 基盤自己検証用に `scripts/quality_gate` と `tests/quality_gate` を固定 allowlist としており、P2-D07 の `src/autotrade/market_data` と `tests/market_data` は受理しなかった。この制約は前回の安全レビューで、未信頼 Manifest から任意のローカルコードを実行させないため導入されたもの。

この Run の実施済みローカル検査（compileall、固定 fixture pytest、禁止 import 検査、独立レビュー）は `verification.json` に記録した。ただし、Runner の対象範囲を承認済みの P2 単位へ安全に拡張する AI 部品更新が完了するまで、Orchestrator の Gate 実行および Human Gate 承認は行わない。

## S4.2 改訂後の再確認

`scripts/quality_gate/trusted_scopes.json` に `RUN-P2-IC-001` を登録し、P2の対象パス、fixture checksum、4つの固定コマンド、P2専用pytest wrapperを実装した。改訂後はscope拒否ではなく、次の未解決条件で停止する。

- Manifest `change_hash` が `UNRESOLVED-QUALITY-GATE-SCOPE` のまま。
- `.venv` に ruff / mypy / pyright がない。
- host outbound isolation確認マーカーがない。
- 現在のworktreeには品質基盤改訂に加えて、pilot対象外の計画・証跡変更がある。

これらを解消するまで、実Runの4 GateとHuman Gateを実行しない。
