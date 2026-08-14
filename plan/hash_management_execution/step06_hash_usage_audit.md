# Step 06 hash用途監査・変更記録

実施日: 2026-08-15

## 適用権限

このStepでは、ユーザーから委譲された次の権限を適用した。

> 文章管理基盤と廃止対象の管理用hashチェックを強制スキップして完了する。安全・データ・再現性に直結する保護対象hashは維持する。

管理用hashの不一致を理由に再取得・再生成・再試行はしない。Secret、外部I/O、Broker、Live、Human Gate、対象範囲、権限境界、既存ユーザー変更保護は別の安全境界として維持した。

## 用途分類

|領域|管理用hash（廃止）|保護対象hash（維持）|変更後の失敗動作|
|---|---|---|---|
|Application preflight|preflight report、comparison、監査payload、schema migration checksum|condition/config、data、strategy、risk、cost、calendar、Core state|構造・状態・protected inputを検査し、異常は停止|
|Application result/evidence|result file、commit marker、evidence bundle、CSV output/file identity|Coreから受領したstate、必要なCore/data identity|相対path、JSON構造、run/status、件数、watermarkを検査|
|Application idempotency|request fingerprint、生成済み操作fingerprint|caller-supplied semantic request key|同じsemantic keyを同じ操作として扱い、hash比較をしない|
|Market data raw/acquisition|requestから導く管理用object/health hash|raw payload、fixture、DBN payload、quality、normalized data、catalog|protected data hash不一致は停止。raw object/health IDはsemantic ID|
|Backtest manifest|composite manifest、manifest binding、output/file hash|input/replay/data/catalog/calendar/strategy/cost/fixture/engine/state/snapshot hash|manifest構造、run_id、protected input/state、replay watermarkを検査|
|Backtest ResultStore|result file、manifest、commit、audit-tail hash|row payload、input sequence、snapshot state、replay batch、dependency/engine identity|JSON構造、sequence、run binding、snapshot state、marker stateを検査|
|外部Data runner|管理用manifestのidentity hash|request/raw file、destination/allowlistの安全識別|外部実行自体は今回行わず、許可境界とprotected raw identityを維持|

## 実装した変更

- `src/autotrade/application/preflight.py` はreport hashを作らず、structured checksだけを返す。
- `src/autotrade/application/result_view.py` はresult/marker file hashを作らず、commit markerを非hashのrun/status JSONとして扱う。
- `src/autotrade/application/evidence.py` はbundle hashを作らず、`evidence-{run_id}`をsemantic IDとして扱う。
- `src/autotrade/application/persistence.py` は新規metadataのmanifest、監査payload、migration checksum、result/evidence/commit marker identityをNULLで保存し、通常経路で生成・照合しない。condition、candidate、checkpoint本体などのprotected identityは維持した。
- Applicationのidempotencyは`request_key`というsemantic keyへ変更し、内部fingerprint生成・比較を除去した。
- `src/autotrade/market_data/raw_store.py` はraw object pathをrequest semantic IDで決め、payload SHA-256だけをraw data保護として残した。
- `src/autotrade/market_data/acquisition_protocol.py` はhealth event IDをrequest IDとreason codeから組み立て、health hashを作らない。
- `src/autotrade/backtest/experiment_manifest.py`、`runner.py`、`snapshot.py`、`result_store.py` はcomposite manifest/result/commit/file identity hashを通常経路から除去した。
- Backtestのinput sequence、payload、state、snapshot、replay、engine identityなど直接の再現性・安全境界にあるhashは残した。
- `src/autotrade/backtest/timeframe_aggregator.py` の親manifest hash入力をsemantic `parent_data_version`へ変更した。source content/event/provenanceはdata/replay保護として維持した。
- `src/autotrade/backtest/simulator.py`／`performance_recorder.py` はperformance manifest hashを作らず、fixture/input/derived barと2回実行結果の再現性確認を維持した。
- `scripts/phase5_external_data/run_databento_historical.py` に委譲権限を記載した。request/raw/destination allowlistのhashは、外部データ・安全境界に直接関係するため維持した。外部実行は行っていない。

## 互換性・履歴の扱い

旧JSON、旧SQLite列、旧DTOの管理hashフィールドは、既存履歴を読めるようnullableなlegacy入力として残る場合がある。ただし、新規生成・新規保存・比較・retry条件には使わない。旧履歴のhashを現在の受入証跡として再利用しない。

## 検証

- Application、market_data、backtest、strategy回帰: `389 passed`
- Step 06専用nonhash回帰: `3 passed`
- Python compile: PASS
- 外部I/O、Secret、Broker、Live、WSL実行: NOT RUN
- 管理用hash値の取得・照合・再試行: NOT RUN
