# CTX-09 統合品質・独立レビュー Findings

## 判定（Findings first）

`CTXMAP-H1` は不適格。Highが3件未解決であり、固定Agent 4件の独立spawn/wait受領も成立していない。CTX-08の初回active document 425件に加え、今回のFindings文書を含む現在のactive document 426件について、A07固定モデル `gpt-5.1` の意味確認は未成立である。今回のレビューは、固定Orchestrator起動後に子Agent起動不能となったため、独立レビューではなく、明示された責任チェックリストとローカル読み取り監査によるフォールバックである。

## Findings

### CTX09-F-001 — High — Gate入力Pathのrepository confinement不足

- 状態: `OPEN`、H1阻止。
- 根拠: `scripts/context_index/check_context_gate.py:217-229` の `changed_list` 読み取り、`285-298` のA07 response読み取り、`252-254` のbaseline snapshot読み取り。
- 問題: `run_gate()` は `report`、manifest、state、graph、H1 receiptには `_inside_root()` を通す一方、`--changed-list`、`--a07-responses`、`--baseline-snapshot` は読み取り前にrepository内へ拘束していない。絶対Path、UNC、repo外相対Pathが指定されると、Gateがrepo外のファイルを入力として読む経路が残る。
- 影響: repository confinementというCTX-09の明示要件を満たさず、外部ファイルの内容が変更判定またはA07入力へ混入する。A07 responseを外部から注入されると、Gateの判断材料も汚染される。
- 必須修正: すべての入力Pathを読み取り前にrepository rootへ解決し、絶対Path、UNC、traversal、symlink/reparse、存在しないPathを共通のfail-closed関数で拒否する。入力Pathの種別ごとに外部Pathを許可する例外を設けない。
- 再試験: repo外のchanged-list、A07 response、baseline snapshotをそれぞれ指定し、外部ファイルを読まず `BLOCKED` になること、既存manifest・index・worktreeが変化しないことを確認する。

### CTX09-F-002 — High — Gate PASS後のallowlistにhash固定がなくTOCTOUが残る

- 状態: `OPEN`、H1阻止。
- 根拠: `scripts/context_index/check_context_gate.py:573-580`、`auto-commit.sh:135-146`、`auto-commit.sh:160-162`。
- 問題: GateのPASS reportは `allowed_paths` のPathだけを返し、Gateが検証した内容のhashを固定しない。`auto-commit.sh` はreportを再読してPathを正規化するだけで、`git add` 直前の内容がGate検証時と同一かを確認しない。report自体が差し替えられた場合のreport integrityも固定されていない。
- 影響: Gate PASS後からstage/commitまでの間に許可済みファイルまたはreportが差し替えられると、未検証の内容をstage、commit、場合によってはpushできる。既存の未追跡変更をstageしない設計意図も、競合時には保証できない。
- 必須修正: PASS reportにPathごとのsource hashとreport hashを保存し、stage直前に対象ファイル、生成manifest、A07 receipt、report自身を再ハッシュする。差分があればindexを変更せず `BLOCKED` とする。stage後もindex blob hashを照合し、push前に再確認する。
- 再試験: Gate完了後・`git add`前に対象ファイルをSecret様文字列へ差し替えるfixture、reportを別allowlistへ差し替えるfixtureを実行し、stage/commit/pushが起きず、indexが不変であることを確認する。

### CTX09-F-003 — High — A07 semantic confirmation未成立

- 状態: `OPEN`、H1阻止。
- 根拠: `plan/context_index/CTX-08_初回全量化レポート.md`、`plan/context_index/CTX-08_不確実レコード一覧.md`、`plan/context_index/CTX-08_dispatch_receipt_index.json`。
- 問題: CTX-08の初回active document 425件と、今回追加したFindings文書を含む現在のactive document 426件は、決定的なPath、hash、見出し、link等の抽出までは完了しているが、固定 `AutoTrade_A07_ContextManifestMaintainer_v0_1` / `gpt-5.1` のstrict receiptによる意味要約、purpose、trigger、relation確認が0件である。runtimeが `Unknown model` を返したため、代替モデルによる完了扱いはしていない。
- 影響: manifest metadataを意味的に信頼できず、routerの検索・関連資料提示の品質を受入済みとできない。CTX-09のcoverage 100%とH1前提を満たさない。
- 必須修正: 固定 `gpt-5.1` runtimeが利用可能になった後、1文書ごとにsafe input、source hash、strict JSON receipt、validator PASS、receipt永続化を成立させる。固定モデルを代替しない。起動不能、timeout、schema不正、Secret疑いはBLOCKEDのまま残す。
- 再試験: 現在の426件のreceipt索引、source hash、document validator、relation graph、routing fixture 10件を再生成し、成功件数・BLOCKED件数・未登録件数を突合する。

### CTX09-F-004 — Medium — stdio JSONL入力上限とprompt-injection境界が不十分

- 状態: `OPEN`、H1前の修正または採否が必要。
- 根拠: `scripts/context_index/context_mcp_server.py:27-31`、`497-511`、`tests/context_index/test_context_router_mcp.py:192`。
- 問題: `serve_stdio()` は1行全体を `json.loads()` する前のbyte/character上限を持たない。レスポンス上限はあるが、入力行の上限がない。またprompt-injection検出は本文取得時の英語句中心の正規表現で、検索時に返すmanifest metadataには同じ境界が適用されない。
- 影響: 巨大な1行入力によるメモリ・処理時間圧迫、または日本語・言い換え・metadata経由の指示上書き文が、router/MCP利用側へ未分類データとして渡る可能性がある。
- 必須修正: JSON decode前にraw line byte上限を適用し、超過時は安全なエラーで処理を打ち切る。metadataと本文をuntrusted dataとして明示し、prompt-injection疑いを拒否または明確に隔離する多言語fixtureを追加する。
- 再試験: 上限超過JSONL、日本語の指示上書き文、混在文字列、metadataだけに含まれる攻撃文を負例として、本文・Secret・外部Pathを返さず拒否することを確認する。

### CTX09-F-005 — Medium — PARTIALと入口文書の状態同期不足

- 状態: `OPEN`、受入前に採否・期限・ownerが必要。
- 根拠: `context/code_manifest.json`、`plan/context_index/CTX-08_不確実レコード一覧.md`、`doc/index.html:74`。
- 問題: code manifest 254件のうち37件が `PARTIAL` であり、parserの限界と再確認条件はあるが、H1受入におけるowner・期限・採否が一元化されていない。また `doc/index.html` は計画を「CTX-02実行中」と表示し、実際のCTX-08完了・CTX-09レビュー中の状態と同期していない。
- 影響: 利用者が入口から現在状態を誤認し、PARTIALをCOMPLETEと誤って参照する、またはレビュー完了と誤解する可能性がある。
- 必須修正: PARTIALごとの受入可否、owner、期限、再確認条件を統合台帳へ登録し、doc/index、README、計画、receiptの状態表記を同一の正本から同期する。PARTIALは推測でCOMPLETEへ昇格しない。
- 再試験: PARTIAL一覧、統合台帳、doc/index、計画、receiptを横断し、状態・件数・リンクが一致することを確認する。

### CTX09-F-006 — Medium — watcherがGate/commit失敗をプロセス終了状態へ伝播しない

- 状態: `OPEN`、運用有効化前に修正または明示的採否が必要。
- 根拠: `scripts/context_index/context_watch.py:169-183`。
- 問題: `watch_loop()` は `process_event()` の戻り値を捨て、失敗時にもループを継続し、最終的に0を返す。pendingは `BLOCKED` へ更新されるが、外部監視や起動ラッパーからは正常終了・稼働継続に見える。
- 影響: A07未起動、validator失敗、auto-commit失敗が監視側へ明確に伝わらず、手動復旧が遅れる。CTX-09の監視・復旧受入条件を満たさない。
- 必須修正: 失敗を集約して非0終了または明示的な停止状態へ遷移させ、pending・event log・終了理由をrunbookで追跡可能にする。再試行は無制限にせず、手動再実行を要求する。
- 再試験: Gate失敗、A07未起動、auto-commit失敗の各fixtureで、pendingがBLOCKEDになり、watcherとラッパーが失敗を返し、未承認commit/pushが発生しないことを確認する。

### CTX09-F-007 — Medium — 強制停止後のstale lock復旧が未定義

- 状態: `OPEN`、運用有効化前に復旧手順が必要。
- 根拠: `scripts/context_index/context_watch.py:54-62`、`181-182`、`scripts/watch-stop.js:10-13`。
- 問題: lockはfinallyで削除されるが、`watch-stop.js` はプロセスを強制停止するためfinallyが実行されない場合がある。stale lockのPID生存確認、作成時刻、再取得条件、退避の手順がない。
- 影響: 異常終了後にwatcherを再起動できず、pending eventが処理されない。運用者が手動でlockを削除する場合も、別watcher稼働中の二重起動を誤って招く可能性がある。
- 必須修正: lockにPID・開始時刻・root fingerprintを保存し、生存確認と同一root確認を行う。stale判定と人間確認を含む復旧手順を追加し、無条件削除は行わない。
- 再試験: 通常停止、強制停止、PID再利用、別rootのlockをfixture化し、二重watcherを許さず、安全な復旧だけを通すことを確認する。

## 実行受領とフォールバック境界

- Orchestrator: `AutoTradeProject_ImplementationQuality_Orchestrator_v0_1`、固定model `gpt-5.6-terra`、root agent idは `019ffff6-9a63-7bd3-8def-047b2d0f29f6`。起動とwaitは完了したが、子Agent起動は `RUNTIME_DISPATCH_FALLBACK_REQUIRED` となった。
- A150/A160/A90/A130: 固定modelはいずれも `gpt-5.6-luna`、agent idは全件 `N/A`、spawn/waitは未成立、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK`。
- 作業境界: このStepではソース、manifest、Git index、commit、pushを変更していない。外部I/O、MCP、Broker、Live、Secret取得は行っていない。

## ローカルフォールバック検証

再現可能なローカル検証は次の結果である。ただし、これは独立Reviewerまたはtrusted scopeの証跡を代替しない。

| 検証 | 結果 |
|---|---|
| document validator | PASS、active 426、errors 0 |
| code validator | PASS、254、COMPLETE 217、PARTIAL 37、BLOCKED 0 |
| routing fixture | PASS、10 cases |
| pytest | PASS、73 passed、coverage 80.10%、fail-under 80 |
| ruff | PASS |
| mypy | PASS、15 source files |
| compileall | PASS |
| WSL trusted scope | 未登録のため未実行 |

## H1判断

`CTXMAP-H1` は発行しない。High 3件、固定Reviewer/Verificationの独立受領未成立、A07 semantic confirmation未成立、WSL trusted scope未登録が残っているため、CTX-10のwatcher有効化・保存時A07呼出し・自動commitを開始してはならない。

## 再開条件

1. F-001/F-002を修正し、同一fixtureで外部Path拒否とTOCTOU防止を確認する。
2. 固定A07 runtimeの復旧後、現在の426件のsemantic receiptを成立させる。固定モデルの代替は禁止する。
3. F-004〜F-007を修正または、owner・期限・証拠・Secret境界を弱めない採否記録付きで残留リスク化する。
4. 固定Reviewer 4件を個別spawn/waitし、同一fixtureで再レビューする。起動不能なら独立レビュー済みと記録しない。
5. `CTXMAP-H1を承認します` の明示承認があるまでwatcherを起動しない。

## CTX-09 remediation update (2026-08-14)

This section is the current status after the user-approved remediation pass. The original finding text above is retained as historical evidence.

| Finding | Current status | Evidence / remaining condition |
|---|---|---|
| CTX09-F-001 | RESOLVED | Gate control inputs reject absolute paths and require repository-relative, non-reparse files. |
| CTX09-F-002 | RESOLVED for the local wrapper path | PASS reports contain per-file SHA-256 values and the report SHA-256 is bound from Gate output through allowlist validation and the staged-index check. |
| CTX09-F-003 | OPEN / HIGH | The exact `gpt-5.1` A07 runtime probe was rejected as `Unknown model`; no substitute model is accepted as semantic confirmation. H1 remains ineligible. |
| CTX09-F-004 | RESOLVED | JSONL request lines are byte-bounded and Japanese/English prompt-injection metadata is rejected or omitted. |
| CTX09-F-005 | MITIGATED / MEDIUM | `doc/index.html` now states CTX-10 BLOCKED and H1 pending. PARTIAL code records now carry owner, deadline, and acceptance metadata. |
| CTX09-F-006 | RESOLVED | Watch-loop event failures propagate as nonzero process results and record BLOCKED state. |
| CTX09-F-007 | RESOLVED for stale-lock safety | Lock metadata includes schema, PID, start time, repository fingerprint, and process-start marker; recovery is fail-closed on invalid, active, mismatched, or reused identities. |

The remediation re-review still ran with `RUNTIME_DISPATCH_FALLBACK_REQUIRED`: the requested independent child reviewers were unavailable (`agent_id=N/A`, `independent=false`). This is not counted as independent review completion. CTX-10/CTX-11 must not activate the watcher while F-003 and the independent-review/runtime conditions remain unresolved.
