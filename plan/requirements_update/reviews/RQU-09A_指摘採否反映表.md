# RQU-09A 指摘採否反映表

- ステップ: `RQU-09A`
- 実施日: 2026-08-10
- 入力: `RQU-08A_専門安全レビュー.md`、`RQU-08B_実装詳細接続レビュー.md`、`RQU-08C_可読性描画HTMLレビュー.md`
- 改訂対象: `drafts/RQU-07_自動トレードシステム要件定義書_candidate.md`、`drafts/01_自動トレードシステム要件定義書_candidate.html`
- 改訂版: `candidate-0.3`
- 判定: `COMPLETED_FOR_RQU-09B`
- Critical: `0`
- High: `0`

## 1. 採否一覧

| 指摘ID | 出典 | 重要度 | 採否 | 反映内容 | 反映先 |
|---|---|---:|---|---|---|
| `RQU-08A-001` | 専門安全レビュー | Medium | 採用 | HTMLのQ1〜Q30を1行ずつに分け、OD-01〜OD-08も独立した行単位表にした | 候補HTML 7章 |
| `RQU-08A-002` | 専門安全レビュー | Low | 採用 | Strategy、Backtest、P3-D14、RQU-03、RQU-04、統合台帳への相対リンクを追加した | 候補Markdown文書情報後、候補HTMLヘッダー・末尾 |
| `RQU-08A-003` | 専門安全レビュー | Low | 採用 | PaperシーケンスとOrderIntent状態図の前に「将来・未承認・外部注文ではない」を再掲した | 候補Markdown Level 2/4、候補HTML Level 4・正式化条件 |
| `RQU-08A-004` | 専門安全レビュー | Low | 採用 | `REQ-DATA-005/006`を候補内で勝手に細分類せず、RQU-03を追跡先とする注記を追加した | 候補Markdown末尾、候補HTML 7章 |
| `RQU-08B-001` | 実装詳細接続レビュー | Medium | 採用 | 既存詳細設計、P3-D14、RQU-03、統合台帳への直接リンクを追加した | 候補Markdown・HTML |
| `RQU-08B-002` | 実装詳細接続レビュー | Low | 採用 | Markdownに加えHTMLでもQ/ODを1行ずつ追跡できるようにした | 候補HTML 7章 |
| `RQU-08B-003` | 実装詳細接続レビュー | Low | 採用 | `REQ-DATA-005/006`の意味を候補で再定義せず、RQU-03を正しい追跡先として明記した | 候補Markdown・HTML |
| `RQU-08C-001` | 可読性描画HTMLレビュー | Medium | 採用 | `ClosedBar`、`SignalEvent`、`TargetPosition`、`Paper`、`OMS`、`provenance`、M1/M30を初出で短く説明した | 候補Markdown・HTML Level 2/3 |
| `RQU-08C-002` | 可読性描画HTMLレビュー | Low | 採用 | 状態図の箱・矢印の読み方、Paperの将来境界、承認境界を図の前に補足した | 候補Markdown・HTML Level 4 |
| `RQU-08C-003` | 可読性描画HTMLレビュー | Low | 採用 | 追跡表をHTMLにも行単位で配置した | 候補HTML 7章 |
| `RQU-08C-004` | 可読性描画HTMLレビュー | Info | 保留 | アプリ内Browserの`file://`表示制限は回避せず、`RQU-UNK-01`として未PASSのまま残した | 候補Markdown・HTML Unknown、RQU-09B |

## 2. 改訂内容の確認

### 2.1 追跡性

- 候補Markdownと候補HTMLの要求ID集合を同じ48件に維持する。
- Q1〜Q30とOD-01〜OD-08を候補Markdown・候補HTMLで同じ順番に保つ。
- `REQ-DATA-005/006`の細かい意味を新しく作らず、RQU-03へのリンクにより採否・根拠をたどれるようにする。
- P3-D04、P3-D05、P3-D14、統合台帳への相対リンクを候補HTMLに追加する。

### 2.2 安全境界

- Backtestの固定範囲で確認できた事実と、Paper・Live・Cloud・Secret・Brokerの将来候補を分離する。
- `TargetPosition`は目標状態、`OrderIntent`はRisk/OMS/Human Gate後の将来候補であり、現在の外部注文ではない。
- Unknownは解消済みへ変更しない。`UNK-P3-01/05/07`は`APPROVED_DEFERRED_UNKNOWN`、`RQU-UNK-01`は部分解消・未PASSのまま維持する。
- 利益保証、投資助言、本番運用許可を示す表現は追加しない。

### 2.3 可読性

- 各Levelの目的を建物・部屋・専門スタッフ・マニュアルのたとえで先に説明する。
- 専門用語を削除せず、初出の短い説明と用語集を併用する。
- 数式を追加しない。`1N`、DD15%、M1/M30などの意味を壊さず、比較基準または時間足として説明する。
- 色だけに頼らず、図中のラベル、破線、STOPPED、未承認・将来の文言、要求IDを残す。

## 3. RQU-09Aの検証予定と引き渡し

RQU-09Bで次を再実行する。

1. 候補HTMLのMermaid 9ブロックのparse/render。
2. 候補HTMLのUTF-8、DOM、目次、内部アンカー、相対リンク、ローカル資産、responsive/print CSS。
3. 候補Markdown/HTMLの要求ID差分。
4. `git diff --check`。
5. RQU-08A/BのCritical/High 0、RQU-08Cの各Level 85点以上、Unknownの状態維持。

RQU-09A完了後も正式な`plan/自動トレードシステム_要件定義書.md`、`doc/requirements/01_自動トレードシステム要件定義書.html`、`doc/index.html`はまだ差し替えない。RQU-H3承認後のRQU-10で初めて正式化する。
