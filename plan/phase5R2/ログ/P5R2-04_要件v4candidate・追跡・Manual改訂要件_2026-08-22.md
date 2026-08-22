# P5R2-04 実行ログ — 要件v4 candidate・追跡・Manual改訂要件

- phase_id: `P5R2`
- step_id: `P5R2-04`
- document_set_id: `P5R2-DOCSET-04`
- 実行日: `2026-08-22`
- 状態: `P5R2-04_COMPLETE / P5R2-05_READY / P5R2-HREQ_UNAPPROVED / P6_PAUSED`

## 1. 実行範囲

HREQ前の v4 candidate、候補Requirement、Acceptance、REQ→AC→UI→API→Persistence→Test→Evidence→Manual追跡、Manual改訂要件だけを作成した。P5R旧完了とManual v0.5は履歴として保持し、本文を変更していない。

作成物:

1. `plan/phase5R2/requirements/drafts/01_自動トレードシステム要件定義書_v4_candidate.md`
2. `doc/phase5R2/02_要件候補/03_P5R2候補Requirement・Acceptance・追跡表.html`
3. `doc/phase5R2/02_要件候補/04_バックテスト手順書改訂要件.html`

## 2. runtime dispatch

Coordinator `AutoTradeProject_DesignDocSet_Orchestrator_v0_1` は `multi_agent_v1` で起動・完了した。Coordinator配下の指定Agent dispatchは成立しなかったため、A10/A80/A81/A90/A95を直接read-only fallbackとして個別起動し、全件の結果を受領した。直接fallbackは補助証跡であり、P5R2-05の正式独立レビュー完了・HREQ承認とは扱わない。

- coordinator agent_id: `01a02822-32d0-70a2-98cd-797c1fc00616`
- dispatch: `COORDINATOR_STARTED / NESTED_DISPATCH_FAILED / DIRECT_READ_ONLY_FALLBACK`
- independent: `false`（P5R2-04の指定Coordinator配下の完全実行ではない）
- review_mode: `ADVISORY_FALLBACK / P5R2-05正式レビュー未完了`
- 直接fallback受領: A10 `01a0282f-c187-7221-bf47-5abac43d6815`、A80 `01a0282f-c2cb-77b3-806b-44693c71fc38`、A81 `01a02831-23f0-7122-8a6e-241b5a11cde5`、A90 `01a02831-252d-72b2-bda6-a2e3b358a2fe`、A95 `01a02831-2683-7dd0-ab61-8091d0465ede`

詳細は `runtime-receipt-P5R2-04.md` と同JSONを正本とする。A90のHigh/Medium指摘はP5R2-05の正式レビュー入力として残し、今回の補助点検で反映できるJob責務分離・8件crosswalk・候補パス統一を反映した。

## 3. root統合チェックリスト

- [x] user回答と推奨案を混同せず、Round 1〜4の明示回答だけを候補Requirementへ正規化した。
- [x] 15m/30m/1h/4h/1d、1m source、legacy 1m/M30閲覧専用を分離した。
- [x] Download JobとDataSetのID・状態・usable昇格を分離した。
- [x] 外部取得`HistoricalDownloadJob`とlocal生成`TimeframeGenerationJob`を`job_type`・入力・出力・状態・再試行で分離する候補契約を明示した。
- [x] H0の4領域・8件を正式Candidate IDとしてcrosswalkし、詳細Requirementと個別追跡行を追加した。
- [x] identity、immutable version、dedupe、値競合停止、warning/UNUSABLEを要件化した。
- [x] Run取消、terminalの状態不変受付、結果表示非表示・再表示、実削除の分離を要件化した。
- [x] Manual本体を変更せず、機能・失敗・復旧・画像・Evidence・改訂履歴の改訂要件を作った。
- [x] HREQ/H1/DATA-G1/DELETE-G1/H2、P6停止、`P5R2-UNK-HD-004`、生成可能全期間の`P5R2-UNK-TF-006`を残した。
- [x] 公開公式文書のread-only確認だけを行い、login、契約、API call、Data downloadを行っていない。
- [x] 管理用hash、manifest、receipt hash、stale、fingerprint、hash retryを追加しない。

## 4. A95静的判定

対象3文書と本ログは、管理用hashを追加していない。A95 direct fallbackは`NEEDS_HUMAN_GATE`と判定した。`P5R2-UNK-HD-004`は保護対象hashの用途・直接因果・失敗時停止範囲が不明なため、引き続き `NEEDS_HUMAN_GATE` とする。判定JSONはruntime receiptに保存するが、hash値・manifest・receipt hashは作らない。

## 5. 次の状態

P5R2-04は候補文書作成として完了し、次は `P5R2-05_READY` である。P5R2-05は候補文書のFindings first正式レビューであり、今回のdirect fallback advisoryとは別に扱う。A90/A81が指摘した完全状態・監査・Manual fidelity・Provider境界はP5R2-05で正式に閉じる。独立レビューが成立しなければ、HREQ packet完成へ進まず `REVIEW_RUNTIME_BLOCKED` として停止する。

未承認のまま: 正式v4、実装、Test subprocess、Playwright、外部Data、Secret、費用、実削除、P6。
