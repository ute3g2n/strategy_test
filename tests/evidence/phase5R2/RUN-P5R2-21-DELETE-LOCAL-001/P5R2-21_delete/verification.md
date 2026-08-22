# P5R2-21 物理削除受入検証

- Step: `P5R2-21`
- Run: `RUN-P5R2-21-DELETE-LOCAL-001`
- 判定: `LOCAL_GREEN`
- 実行日: `2026-08-23`

## 対象

P5R2-DELETE-G1で承認された範囲だけを検証した。物理操作の対象は、この検証中に作成した一時ResultArtifactであり、既存のHistorical Data、既存Run、既存CSV、既存Audit、既存Evidenceは対象にしていない。

## Backend受入

`tests/phase5R/test_p5r2_result_artifact_physical_delete.py` を実行し、5件がPASSした。

- terminal `RESULT`だけを、サーバーが解決したruntime root内から削除する。
- logical Artifact ID以外の任意pathを受け付けない。
- 削除前にRun状態、Artifact種別、確認、許可root、symlink／reparse／TOCTOUを検査する。
- CSV、Historical Data、Run本体、Audit、Evidenceは削除せず、対象外のunknown Runも物理操作しない。
- 同じoperation tokenの再送と、新しいtokenでの削除済み再送を冪等に返す。
- 削除完了後は`RESULT_DELETED` Audit／tombstoneを残し、Runの`result_deleted`を保存する。
- 再起動後、結果ファイルがないことを理由に`RECOVERY_REQUIRED`へ遷移しない。
- restore APIは追加していない。

対象Python回帰は `40 passed`、ruff、mypy、compileallもPASSした。

## Web Product受入

実Application APIへloopback接続する専用Playwrightを実行し、desktop `1280x900` と mobile `390x844` の2件がPASSした。

- 完了済みRunカードから削除操作を開始できる。
- 1回目の押下ではAPIを呼ばず、確認Dialogを表示する。
- 確定後だけ`/api/p5r2/result-artifacts/delete`へlogical ID、`RESULT`、確認済みを送る。
- request bodyに`path`、`absolute_path`を含めない。
- 削除後は「削除済み（復元不可）」を表示し、同じボタンを無効化する。
- 外部requestは0件、axeのcritical／serious violationは0件だった。

captureは次の2ファイルに保存した。

- `ui/chromium-desktop/p5r2-delete-ui-capture.json`
- `ui/chromium-mobile/p5r2-delete-ui-capture.json`

## 境界

外部Provider、login、API call、Data download、Secret、費用、既存利用者Dataの削除、P6開始は行っていない。P5R2-H2は未承認のまま保持する。
