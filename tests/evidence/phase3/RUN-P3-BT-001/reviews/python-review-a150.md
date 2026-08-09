# A150 Python Code Review — RUN-P3-BT-001 (P3-07)

## 判定（Findings first）

- **受入不可**
- Critical: **1**
- High: **8**
- Medium: **6**

## Findings

### [C-001] 実Replay・Snapshot・Commit・Result永続化が未実装

`replay_order.normalize_replay`、`replay_is_idempotent`、`simulator.run_full_replay` は入力のフラグだけで順序付き結果hash一致を返す。`snapshot.snapshot_aggregator` は常に復元一致、`snapshot.replay_after_restore` は常に重複0を返す。Result Storeにもappend-only/atomic publish/commit marker/recovery offsetの処理がない。入力改竄でもPASSになるため、決定的再生・重複注文防止・復旧証跡を保証できない。

修正案: canonical event列を実際に正規化・実行してresult/state hashを再計算し、`result → snapshot → commit-marker` を一回だけ原子的に確定する。復旧時はmarkerのoffset/watermark/hash/bindingを照合し、未確定行を再公開しない。

### [H-001] 必須値・未知値のfail-closedが不足

`apply_data_gate` は未知flagを許可し、Calendar/Manifest/Engine/Replay/partial/cohortの各guardは入力欠落や型違いを十分検証せずPASSする。

修正案: 必須フィールド、型、許可値を検証し、欠落・未知・比較不能は理由付きSTOPPEDに統一する。

### [H-002] M30入力とCalendar境界の検証不足

M30はopen時刻の連続性以外にBAR_1M、close時刻、OHLC関係、非負整数volume、event_id一意性、quality/data_version、Calendar/sessionを検証しない。`calendar_rejections` キーの存在だけでDST ACCEPTED等の固定結果を返す。未確認・破損・未来情報を受理可能。

修正案: strict schemaを導入し、各M1のclose=open+1分、OHLCV関係、event ID/Calendar bindingを検証する。Calendar fixtureは内容とhashを照合し、異常はすべて停止する。

### [H-003] Decimal・丸め・費用意味論が未実装

`Decimal(str(value))` はfloat等を受理し、Stop価格は`.2f`（暗黙の丸め）で承認済みside別tick/丸め規則を使わない。Slippageはbase非負のみ、Costはfill非負をcost非負と誤判定し、実際の費用・sideを計算しない。

修正案: 文字列Decimal/有限値/quantumを厳格化し、Manifest固定のtick・side別不利丸め→slippage→cost順を実装する。

### [H-004] 次足約定とLook-ahead防止が未実装

`schedule_next_bar` は時刻が等しくない入力を無条件でfilled=True、`fill_next_bar_only` はeligible_openのtruthyだけで通す。UTC・時系列・next eligible bar・pending fingerprintを検証しない。

修正案: UTC timestampをparseし、directiveとeligible barの順序・Calendarを検証する。欠落・過去・同一barはNO_ELIGIBLE/STOPPEDにする。

### [H-005] Result path/publish安全性不足

公開可否を呼出し側のboolへ委譲し、`resolve().relative_to()` だけでroot自身、未存在先、既存run上書き、symlink/reparse race、append-onlyを防がない。

修正案: 許可root・正規path・既存run禁止・通常ファイル・atomic rename・commit marker順序をpublish境界で検証する。

### [H-006] Performance evidenceを偽装可能

limitsがtruthyなら実測なしで`evidence_required=True`となり、Performance recorderもキー存在だけでPASSを返す。値の型、非負、limit、fixture/result hashを検証しない。

修正案: 実測値と対象fixture/result hashを必須化し、欠落/不正はNOT_EXECUTED、limit超過はFAILとする。

### [H-007] Cohort/Config互換性を入力で検証しない

`build_m30_cohort` はunknown/duplicate/missing timeframeや`input_order`を検証せずsortするだけ。`assert_m30_disabled_compatibility` は入力を無視し固定hashでCOMPATIBLEを返す。

修正案: enabled timeframes、canonical order、closed viewの完全集合、v1 fixture/config/hashを相互照合する。

### [H-008] Canonical hashがstrictでなく非決定になり得る

`_common.canonical` と`contracts.canonical_json` の`default=str`が未対応型・set・任意objectを文字列表現で通す。文字列表現やset順序に依存し、hash再現性と入力境界を破る。

修正案: 許可型だけをcanonical JSON化し、Decimal/UTC/配列順を明示正規化する。未対応型は例外ではなくSTOPPEDへ変換する。

## Medium

- M-001: 公開関数が`dict`/Noneを入口で検証せず、AttributeError等を構造化STOPPEDに変換しない。
- M-002: M30でevent_id欠落時に位置依存fallbackを生成し、再送/衝突識別を弱める。
- M-003: Calendarはcase名だけを検証し、fixture時刻・timezone・versionを検証しない。
- M-004: offline/engine/path_known等のbool guardがtruthiness依存で、`"false"`等を真として扱う。
- M-005: `is_publishable` に存在・通常ファイル・TOCTOU対策と型エラー処理がない。
- M-006: テストがhappy-pathのbool契約中心で、未知値、欠損、改竄hash、OHLCV破損、重複ID、partial commit再起動を網羅しない。

## 再現メモ

`PYTHONPATH=src` で次を確認した（いずれも停止せず許可/証拠扱いになる）。

```text
apply_data_gate({'blocking_flag':'NEW_UNKNOWN'}) -> {'signal_allowed': True}
validate_manifest({}) -> {'status': 'PASS'}
schedule_next_bar({'directive_time':'nonsense'}) -> {'filled': True}
measure_performance({'elapsed_limit_minutes':30,'rss_limit_gib':8}) -> {'evidence_required': True}
run_full_replay({'same_manifest_twice':True}) -> {'ordered_result_hash_equal': True}
```

## 再レビュー（修正後）

2026-08-09の修正後に再確認した。`tests/backtest` は **80 passed** だが、下記が残るため受入不可。

- Critical: **1** — `run_full_replay`、source-only replay、snapshot fallback、recoveryを実行系へ結合しておらず、入力フラグだけで結果一致・重複0を返せる。
- High: **9** — 同一payload重複をdedupeしないReplay、未知Data Gate/Policyの許可、M30 Calendar/ID/Cohort/互換性の固定値・任意hash bypass、float/暗黙丸め・Cost/Slippage未計算、任意文字列の次足約定、性能証跡の不十分なhash検証、Manifest値比較不足、NaN/Infinity canonical化、`AtomicResultStore`のrun_id境界・marker再照合・fsync不足。
- Medium: **5** — 入口型検証、fixture/version binding、missing値のguard、path TOCTOU、敵対的テスト不足。

再現例:

```text
canonical({'x': float('nan')}) -> '{"x":NaN}'
normalize_replay(two identical event_id/payload events) -> PASS with 2 events
apply_data_gate({'blocking_flag':'NEW_UNKNOWN'}) -> {'signal_allowed': True}
run_full_replay({'same_manifest_twice': True}) -> {'ordered_result_hash_equal': True}
measure_performance({'elapsed_limit_minutes':30,'rss_limit_gib':8}) -> {'evidence_required': True}
assert_m30_disabled_compatibility({'v1_config':{'m30_enabled':False},'v1_semantic_hash':'sha256:fake'}) -> COMPATIBLE
```
