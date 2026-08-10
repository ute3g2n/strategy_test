# A40 Entry Review — P3-08R-02

対象: `b9f3c77f4f449808ec27d2c167cbea9435618068`

## Findings first

- Critical: 0
- High: 0
- Medium: 0
- Unknown: 0（P3-08R-03でManifest・Core referenceを作るという後続境界は、未解決Unknownではなく明示的な引渡し条件として記録済み）

## 確認結果

1. `tests/engine_poc/entrypoint.py`は固定fixture、固定digest、固定Manifest path、Local data provider、`network_mode=none`、read-only入力、許可write rootを一つのentry planへ正規化する。
2. `build_lean_config`は決定的なconfig dataを作るが、`launch_allowed=false`であり、LEAN projectを起動しない。
3. `EngineRunRequest`/`EngineRunResult`のCore DTOは`src/autotrade/backtest/contracts.py`の既存契約を利用し、vendor SDK型をCore/Strategyへ追加していない。
4. `validate_lean_output`は順序番号、UTC、hash、failure、禁止vendor fieldを検証する。P3-09実測値や期待値を生成しない。
5. `scripts/quality_gate/local_p3_poc.py --mode run`は明示的に停止し、prepare入口から本PoCへ到達できない。

## 判定

P3-08R-02の専用入口・Adapter境界として受入可。P3-09本Runの実行許可、Core reference、期待出力の確定は行っていないため、次はP3-08R-03へ限定する。
