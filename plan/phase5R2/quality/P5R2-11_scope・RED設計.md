# P5R2-11 Quality Scope・RED設計

## 判定

`P5R2-11_SCOPE_REGISTERED_EVIDENCE_NOT_GENERATED`

P5R2-H1の承認範囲に従い、Quality入口のnamespace互換修正と
`RUN-P5R2-11-LOCAL-001`のscope登録を行った。固定4 Gate、RED分類、Evidence rootは
設計・登録済みであるが、P5R2-11ではtest subprocess、pytest、Playwright、npm、WSLを
起動していない。P5R2-11登録時点ではP5R2-UNK-QG-001/002を確認待ちとして保持し、後続P5R2-12 preflightで解消条件を確認した。

## H1承認の参照

| 種別 | 参照先 | 状態 |
|---|---|---|
| H1 packet | `doc/phase5R2/05_H1/06_P5R2-H1承認packet.html` | `APPROVED_BY_DELEGATED_AUTHORITY` |
| H1判断ログ | `plan/phase5R2/ログ/P5R2-H1_承認判断_2026-08-22.md` | 記録済み |
| 統合台帳 | `doc/00_全Phase残課題Blocked統合台帳.html` | H1、QG-001、QG-002を現在状態へ反映 |
| 設計レビュー | `plan/phase5R2/ログ/P5R2-10_詳細設計レビュー・改訂・再レビュー_2026-08-22.md` | Critical=0 / High=0の入力履歴 |

## 1. Namespace互換確認と最小変更

### 確認結果

変更前の `run_test.ps1`、`run_isolated_p2.ps1`、`run_isolated_p2.sh` は
`phase[0-9]+`だけを受け付け、`phase5R2`を拒否していた。また、PowerShell wrapperは
受け取ったEvidence phaseを小文字化していたため、既存scopeの大文字 `phase5R`と
Evidence pathの大文字小文字を一致させられなかった。

### 適用した変更

| ファイル | 変更 | 既存互換性 |
|---|---|---|
| `scripts/wsl_quality_gate/run_test.ps1` | `phase[0-9]+`を、数字の後に任意の`R`と改訂番号を許す検査へ変更 | `phase2`、`phase3`、`phase5`、`phase5R`を維持 |
| `scripts/wsl_quality_gate/run_isolated_p2.ps1` | 同じnamespace検査へ変更し、Evidence phaseを小文字化せずtrimだけに変更 | 既存の`phase5R` pathを保持 |
| `scripts/wsl_quality_gate/run_isolated_p2.sh` | 既存shell runnerのnamespace検査だけを同じ境界へ変更 | `run_isolated_p2.sh`を継続使用 |

許可する形は `phase` + 数字 + 任意の `R` + 任意の改訂数字である。任意文字列や
絶対pathを許可する変更は行っていない。P5R2-11では実行による互換性確認を行わず、
静的な変更確認だけを行う。

## 2. Trusted scope

| 項目 | 登録値 |
|---|---|
| Run ID | `RUN-P5R2-11-LOCAL-001` |
| phase / step | `phase5R2` / `P5R2-11` |
| scope mode | `target_only` |
| Evidence root | `tests/evidence/phase5R2/RUN-P5R2-11-LOCAL-001/` |
| 実行状態 | P5R2-11はscope登録のみ。後続P5R2-12でpreflight、RED、固定4 Gateを実行し、RED_CONFIRMED |
| network | host outbound isolation必須。未確認ならBLOCKED |
| external I/O | 禁止 |
| Secret / Broker / Live | 禁止 |
| physical delete | 禁止 |

### target_paths

```text
src/autotrade/application
src/autotrade/backtest
src/autotrade/market_data
src/autotrade/strategy
ui/mock/src
tests/application
tests/backtest
tests/phase5R
tests/market_data
ui/mock/tests
scripts/quality_gate
scripts/wsl_quality_gate
```

### excluded_paths

```text
.env
.env.*
doc
plan
research
third_party
broker
cloud
secrets
tests/evidence/phase5
tests/evidence/phase5R
tests/evidence/phase5R2
```

`tests/evidence/phase5R2/RUN-P5R2-11-LOCAL-001/`は、scopeのコード変更対象ではなく、
後続runnerが書き込むEvidence rootとして扱う。既存 `tests/evidence/phase5` は
protected fixtureの保存場所を含むため、入力はread-only参照であり、scope変更対象ではない。

P5R2-12のpreflight後、host isolationと既存protected fixture identityの一致をEvidenceで確認した。固定入口のformatter／lint／typeはPASSし、testは期待REDとなった。詳細はP5R2-12 RED Evidenceへ分離して記録する。
P5R2専用固定pytest入口は`local_p5r2_pytest`とし、既存P5Rの入口へ対象範囲を混在させない。

## 3. Protected fixture境界

P5R2 scopeは次の既存fixtureを参照する。

```text
tests/evidence/phase5/RUN-P5-09-BINANCE-001/normalized/spot/klines/1m/BTCUSDT/2025-02/BTCUSDT-1m-2025-02.csv.gz
```

path、name、version、protected identityの出典は、既存trusted scopeの
`RUN-P5R-03-20260816-001.fixture`である。P5R2 scopeとRun manifestには、既存recordに
登録済みのprotected checksumを再利用して記録した。新しいchecksumやhash値を計算して
いない。P5R2-11ではfixtureを開かず、再計算、変更、Evidence化を行っていない。

この既存protected checksumの参照方式と現行quality runnerの実行時入力契約は、P5R2-12
でread-only入力契約として確認した。実際のfixture読み取りまたはhost isolationに失敗
した場合は `QUALITY_GATE_BLOCKED` とし、hashの再計算・retryは行わない。P5R2-12の
Evidenceではfixture不一致は発生していない。

## 4. 固定4 Gateのscope案

| 順序 | Gate | 登録commandの目的 | P5R2-11の状態 |
|---:|---|---|---|
| 1 | formatter | Python対象pathのformat確認 | 未実行 |
| 2 | lint | Python対象pathの静的検査 | 未実行 |
| 3 | type | application / backtest / market_data / strategyの型検査 | 未実行 |
| 4 | test | 既存のlocal P5R test入口を固定templateとして登録 | 未実行 |

UIのbuild、unit、PlaywrightはH1 packetどおりP5R2-19の別Stepで扱う。P5R2-11の
固定4 GateへnpmやPlaywright commandを混在させない。登録commandの実行、host isolation
Evidenceの生成、scope内テストの実測判定はP5R2-12以降の責務である。

## 5. RED分類

P5R2-12でREDを作るときの分類であり、P5R2-11ではテストファイルを作成・実行しない。

| 分類 | 確認する失敗条件 | fail-closed条件 |
|---|---|---|
| 時間足 | 1mをstrategy足にしない、15m/30m/1h/4h/1d、UTC、closed bar、legacy分離、単一内部欠損の境界 | 条件外のDataをusableまたはRun入力へ昇格しない |
| Data Job / Catalog | Download JobとGeneration Jobの分離、Catalog期間、merge/dedupe/conflict、staging、promotion、quality | Catalog不在・品質未承認・identity不一致なら生成を止める |
| Run cancel | QUEUED/RUNNINGのcancel、二重押下、再送、terminal state不変、OperationGuard、監査 | terminalを変更せず、重複操作を拒否する |
| ResultArtifact delete guard | logical ID、許可root、active Run、CSV/Data/Audit/Evidence保護、実path不受理 | traversal、symlink/reparse、ID不一致、保護対象を拒否する |
| audit | 操作者、理由、target、旧/新state、依存数、request/correlation ID、失敗理由 | 監査欠落・不完全な操作を成功扱いしない |
| restart / recovery | 再起動、partial failure、migration failure、RECOVERY_REQUIRED、orphan、保存先不一致 | 復旧確認前にRunやResultを再利用しない |
| path safety | canonical path、固定root、TOCTOU、OS差異、証跡root分離 | unknown pathや別rootへ進まない |
| UI DTO | 3画面共通DTO、error code、cancel state、artifact表示、dialog/focus | UI表示だけでAPI/Persistenceの成功とみなさない |

## 6. Unknown・停止条件

| ID | P5R2-11現在状態 | 再開条件 |
|---|---|---|
| `P5R2-UNK-QG-001` | P5R2-12 preflightでhost isolation、namespace、固定入口を確認済み | 解消済み。RED実行結果とは別管理 |
| `P5R2-UNK-QG-002` | P5R2-12 preflightで既存protected identityの一致を確認済み | 解消済み。fixtureはread-only、既存record不一致はBLOCKED |

scope登録、H1承認、設計レビューの存在は、固定4 GateのPass、REDのPass、P5R2完了、
DATA-G1、DELETE-G1、H2、P6開始を意味しない。

## 7. 禁止操作と実行回数

- `run_test.ps1`、`run_isolated_p2.ps1`、`run_isolated_p2.sh`を実行していない。
- test subprocess、pytest、Playwright、npm、WSL、外部network、Secret read、Provider login/API/downloadを行っていない。
- 既存fixture、既存Data、既存Run、Audit、Evidence、Export済みCSVを変更・削除していない。
- 管理用hash、manifest hash、fingerprint、stale、receipt hashを作成していない。
