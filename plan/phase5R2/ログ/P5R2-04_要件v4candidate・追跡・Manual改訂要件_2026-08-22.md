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

指定された `multi_agent_v1__spawn_agent` と `multi_agent_v1__wait_agent` は、この実行環境の利用可能Toolに存在しなかった。そのためCoordinator/指定5 Agentの実spawn・waitはできない。

- dispatch: `RUNTIME_DISPATCH_FALLBACK_REQUIRED / LOCAL_FALLBACK_NO_SUBAGENTS`
- independent: `false`
- review_mode: `SELF_REVIEW_FALLBACK`
- 未起動: A10, A80, A81, A90, A95（すべて `agent_id=N/A`）
- 理由: `AGENT_RUNTIME_TOOL_UNAVAILABLE: multi_agent_v1__spawn_agent and multi_agent_v1__wait_agent are not exposed in this runtime`

詳細は `runtime-receipt-P5R2-04.md` と同JSONを正本とする。未起動Agentを独立実行済み・独立レビュー済みとは扱わない。

## 3. root統合チェックリスト

- [x] user回答と推奨案を混同せず、Round 1〜4の明示回答だけを候補Requirementへ正規化した。
- [x] 15m/30m/1h/4h/1d、1m source、legacy 1m/M30閲覧専用を分離した。
- [x] Download JobとDataSetのID・状態・usable昇格を分離した。
- [x] identity、immutable version、dedupe、値競合停止、warning/UNUSABLEを要件化した。
- [x] Run取消、terminalの状態不変受付、結果表示非表示・再表示、実削除の分離を要件化した。
- [x] Manual本体を変更せず、機能・失敗・復旧・画像・Evidence・改訂履歴の改訂要件を作った。
- [x] HREQ/H1/DATA-G1/DELETE-G1/H2、P6停止、`P5R2-UNK-HD-004`を残した。
- [x] 公開公式文書のread-only確認だけを行い、login、契約、API call、Data downloadを行っていない。
- [x] 管理用hash、manifest、receipt hash、stale、fingerprint、hash retryを追加しない。

## 4. A95相当の静的判定

対象3文書と本ログは、管理用hashを追加していない。`P5R2-UNK-HD-004`は保護対象hashの用途・直接因果・失敗時停止範囲が不明なため、引き続き `NEEDS_HUMAN_GATE` とする。判定JSONはruntime receiptに保存するが、hash値・manifest・receipt hashは作らない。

## 5. 次の状態

P5R2-04は候補文書作成として完了し、次は `P5R2-05_READY` である。P5R2-05は候補文書のFindings firstレビューであり、実runtimeを再試行する。指定Agentの実出力が得られない場合、独立レビュー完了・HREQ packet完成を主張せず `REVIEW_RUNTIME_BLOCKED` として停止する。

未承認のまま: 正式v4、実装、Test subprocess、Playwright、外部Data、Secret、費用、実削除、P6。
