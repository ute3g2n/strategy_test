# P5R2-21 security／code review

## Findings first

- Critical: 0
- High: 0
- Medium: 0
- Low: 0

## 確認内容

- 呼出元指定の絶対path、相対path、`..`、symlink／reparse、別ID、TOCTOU差し替えを拒否する。
- ServiceはbrowserのRun状態を信用せず、server-owned `_Run.status`と固定runtime rootを注入する。
- Serviceが管理するRunを解決できない要求は`RUN_NOT_FOUND`で拒否し、物理I/Oへ到達しない。
- `RESULT`以外、active／recovery Run、確認未実施、DELETE-G1未承認、物理I/O未許可を拒否する。
- 削除対象は`results/<run_id>/`だけで、CSV、Historical Data、Run catalog、Audit、Evidenceをcascadeしない。
- lock下でsnapshotと削除直前のsignatureを再検査し、失敗時は`DELETE_FAILED`で停止する。
- operation tokenの再送と削除済みtombstone再送を冪等に処理し、restore APIは提供しない。
- UIは1回目の押下で確認Dialogを表示し、確定中は対象ボタンを無効化する。request bodyはlogical IDだけを使う。
- audit／tombstoneには結果Artifactの状態と物理I/O実施有無を保存する。管理用hashは生成しない。

## 判定

P5R2-DELETE-G1の承認範囲に対して、Critical／Highは0。既存利用者Dataの削除、外部接続、Secret、費用、P6開始は行っていない。A95 static policyは新規P5R2-21成果物について`ALLOW`とした。
