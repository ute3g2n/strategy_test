# P4-H1 Human Gate承認記録

- Phase: `PHASE4_PRODUCT_APPLICATION_BACKTEST_2026_08_11`
- Plan: `P4-PLAN-001 / plan/Phase4_実行計画書_v0.1_2026-08-11.md`
- Gate: `P4-H1`
- Status: `APPROVED`
- Received: `2026-08-12`（Asia/Tokyo）
- User declaration: 「P4-H1を承認します。P4-06以降のプロンプトを順番に実行して下さい」
- Approval linkage: P4-05が提出した対象Run・scope・fixtureの候補を承認対象として固定する。

## 承認対象Runと範囲

- Run ID: `RUN-P4-04D-001`
- `scope_mode`: `target_only`
- `target_paths`:
  - `src/autotrade/application`
  - `tests/application`
  - `tests/phase4`
  - `tests/fixtures/phase4`
- `excluded_paths`:
  - `src/autotrade/backtest`
  - `src/autotrade/market_data`
  - `src/autotrade/strategy`
  - `ui/mock`
  - `doc`
  - `plan`
  - `.env`
  - `research`
  - `third_party`
  - `tests/evidence`（Evidenceの追加保存先としては例外）
- Read-only fixture: `tests/fixtures/phase3/run_p3_backtest_fixture_manifest_v1.json`
- Fixture SHA-256: `sha256:aeb03df1eef3ea836d176a8b0443c45b6bc7f6d01e455fd6026cabf16c536fa4`
- Trusted scope registry: `scripts/quality_gate/trusted_scopes.json`
- Baseline: `2ce571e`

## 承認後に許可すること

P4-06、P4-07、P4-08、P4-09を、計画書の直接実行プロンプトの順序で実行する。許可範囲は、固定local fixtureを使うProduct/Application、Persistence、Backtest/Sweep/Result/Evidence、P4対象UI、対象scopeのテストと証跡である。実Agent起動は第一選択とし、起動不能時は計画書どおり`DISPATCH_MODE=LOCAL_FALLBACK_NO_SUBAGENTS`へ切り替え、未起動を独立レビュー済みとは扱わない。

## 明示的な除外と停止条件

- Core（`src/autotrade/backtest`、`src/autotrade/market_data`、`src/autotrade/strategy`）を変更しない。
- 実市場Data、Broker、Paper、Live、実資金、Account／Order／実Risk値、Secret、Cloud、外部I/O、未承認HTTP transport、依存追加を開始しない。
- P4-03正式file treeを正本とし、Application実装は`src/autotrade/application`へ置く。P4-04D RED sentinelに旧`autotrade.product_application`参照がある場合は、設計不一致を記録したうえで承認target内の契約テストへ修正してからRED→GREENを行う。
- `UNK-P4-04D-004`（host outbound isolation）は未解消であり、Passへ変換しない。WSL品質Gateは`run_test.ps1`だけを使用し、host outbound isolationが確認できない場合はBLOCKEDとする。
- `UNK-P4-04D-005`（viewport／browser／axe runtime）はP4-08までUnknownとして保持し、未実行をPassへ変換しない。
- Critical／High、scope逸脱、Core差分、Secret／外部I/O、fixture hash不一致、Evidence不整合、必須テスト欠落があればそのStepで停止する。
- P4-10はP4-H2承認前のため、この承認には含めない。

## 証拠

- P4-05レビュー: `doc/phase4/04_レビュー/05_Phase4詳細設計レビュー・改訂記録.html`
- P4-04D品質設計: `doc/phase4/03_品質設計/04_Phase4テスト戦略・RunManifest設計.html`
- Plan: `plan/Phase4_実行計画書_v0.1_2026-08-11.md`
- Registry: `scripts/quality_gate/trusted_scopes.json`
