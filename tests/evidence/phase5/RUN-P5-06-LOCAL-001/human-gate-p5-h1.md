# P5-H1 Human Gate承認記録

- Phase: `PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12`
- Plan: `P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md`
- Gate: `P5-H1`
- Status: `APPROVED`
- Received: `2026-08-12`（Asia/Tokyo）
- User declaration: 「P5-H1を承認します。」
- Approval linkage: P5-05のレビュー済み設計、Critical/High=0、固定local dummy、RED→GREEN、Run Manifest、品質Gateの開始範囲を承認対象として固定する。P5-DATA-G1、外部Data、Provider、Secret、費用、Broker、Paper、Live、実資金、実Risk、Cloudは承認対象外。

## 承認対象Runと範囲

- Run ID: `RUN-P5-06-LOCAL-001`
- `scope_mode`: `target_only`
- Baseline HEAD: `f911013220884fdde6a8aa94b914cb7a4c563a1f`
- Change hash at approval/scope registration: `sha256:c91854d705c489adc9894214b2f86c86940304aab4ce23d420524031f27206c6`（baselineからtarget-only範囲を計算。P5-06の実装差分発生後はRun Manifestのchange hashを再計算する）
- `target_paths`:
  - `src/autotrade/market_data`
  - `scripts/quality_gate`
  - `tests/market_data`
  - `tests/fixtures/market_data`（既存固定fixtureはread-only）
  - `tests/evidence/phase5/RUN-P5-06-LOCAL-001`
- `excluded_paths`:
  - `src/autotrade/application`
  - `src/autotrade/backtest`
  - `src/autotrade/strategy`
  - `doc`
  - `plan`
  - `.env`
  - `research`
  - `third_party/everything-claude-code`
  - `tests/evidence/phase5`（上記RunのEvidence rootを除く）
- Fixed local fixture: `tests/fixtures/market_data/data_quality_replay_fixture.json`
- Fixture version: `p2-dqr-fixture-v1`
- Fixture SHA-256: `sha256:c19d1c165f0214c2f64218208684e01c1f6b08b838d2821a2b6f172750637a99`
- Trusted scope registry: `scripts/quality_gate/trusted_scopes.json`
- Host outbound isolation: required; verification evidence is a P5-06 precondition. Unconfirmed isolation remains `UNKNOWN` and must fail closed.

## 承認後に許可すること

P5-06の直接実行プロンプトに従い、TEST-P5-DATA-IDの固定local dummy RED、承認範囲内の最小実装、local verification、上限付きdebug、Python/security review、Evidence保存を行う。外部通信、Provider、Secret、実Data、P4 DB/Core、Broker/Paper/Live、Cloud、依存追加は開始しない。

## 明示的な除外と停止条件

- 既存fixtureの改変、fixture hash不一致、target外変更、test skip／削除、Secret、外部通信、Provider、実Data、未登録Runを停止する。
- host outbound isolationが確認できない場合は品質Gateを`BLOCKED`とし、UnknownをPassへ変換しない。
- Critical／High、receipt欠落、Evidence不整合、P5-DATA-G1の未承認をP5-H1で代用する行為があれば停止する。

## 証拠

- P5-05レビュー: `doc/phase5/04_レビュー/05_Phase5詳細設計レビュー・改訂記録.html`
- P5-06ログ／Evidence root: `tests/evidence/phase5/RUN-P5-06-LOCAL-001/`
- Registry: `scripts/quality_gate/trusted_scopes.json`
