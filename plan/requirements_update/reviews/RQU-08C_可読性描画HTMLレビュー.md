# RQU-08C 可読性・描画・HTMLレビュー

- ステップ: `RQU-08C`
- 実施日: 2026-08-10
- 対象: `plan/requirements_update/drafts/RQU-07_自動トレードシステム要件定義書_candidate.md` / `plan/requirements_update/drafts/01_自動トレードシステム要件定義書_candidate.html`
- 使用Skill: `student-reviewer`
- 役割: 中学生向け可読性・表示品質レビュー責任者
- source fidelityの最終判断: RQU-08A/RQU-08Bへ委譲
- 判定: `COMPLETED_WITH_VISUAL_LIMITATION`
- 最終判定: `PASS_FOR_RQU-09A`

## 1. 目的と境界

このレビューでは、ITを知らない中学生が候補文書を読み進められるか、専門語に説明が付いているか、例え話が役に立つか、数式や投資をすすめる表現が残っていないかを確認した。

同時に、候補HTMLのMermaid構文、空図、要求ID、目次、相対リンク、ローカル資産、スマートフォン幅・印刷向けCSSを確認した。実ブラウザのスクリーンショットによる文字の重なり・切れの最終目視は、アプリ内Browserのローカル`file://`表示がURLポリシーでブロックされたため実施できない。この未確認事項は`RQU-UNK-01`としてPASSへ繰り上げず、RQU-09Bでも引き継ぐ。

## 2. student-reviewer評価

### 2.1 Level別スコア

| C4 Level | score | pass | 良い点 | 指摘・修正候補 |
|---|---:|---|---|---|
| Level 1 Context | 94 | true | 最初に「街の中の建物」と目的を示し、人・システム・外部境界を図で確認できる。未承認境界も明示される。 | `provenance`、`hash`、`Human Gate`は初見では難しいため、最初の表でも短い日本語を添えるとさらによい。 |
| Level 2 Container | 92 | true | 「部屋」のたとえと、入力・出力・停止条件の表が対応している。Backtestの流れが順番で読める。 | `ClosedBar`、`SignalEvent`、`TargetPosition`、`Paper`、`OMS`が連続して出るため、初出箇所で一言説明する。表はスマートフォンでは横スクロールになる。 |
| Level 3 Component | 88 | true | データ担当、ルール担当、再生担当、安全停止担当の分担が図と文章でつながっている。M30を「実M1連続30本から作る」と明記している。 | `Donchian`、`N`、`provenance`、`Snapshot`、`Fill`は専門語である。既存用語集を保ち、初出に「何をするものか」を短く補う。 |
| Level 4 Code / Detail | 86 | true | 実装クラスの細部へ行き過ぎず、データ関係と状態変化に絞っている。`TargetPosition`は注文ではないこと、未承認なら停止することが明確。 | 状態名が英語中心で負荷が高い。図の直前に「箱は状態、矢印は状態の変化」と書き、`OrderIntent`と`APPROVED_FOR_PAPER`の将来境界を再強調する。 |

全Levelが合格基準の85点以上である。難語は見つかったが、要求ID・型名・安全警告を削る必要はない。RQU-09Aでは上表の低リスクな読みやすさ改善と、RQU-08A/RQU-08Bの追跡表・リンク指摘をまとめて反映する。

### 2.2 中学生向けレビューのYAML要約

```yaml
level_1:
  score: 94
  pass: true
  good_points:
    - 最初に建物のたとえと目的が示されている
    - 人、システム、未承認境界が図で分かる
  required_fixes: []
  suggested_revisions:
    - provenanceを「データがどこから来たか」と初出で補足する
level_2:
  score: 92
  pass: true
  good_points:
    - 部屋ごとの入力、出力、停止条件が表になっている
    - Backtestの順番をシーケンス図で追える
  required_fixes: []
  suggested_revisions:
    - ClosedBar、TargetPosition、Paperを初出で短く説明する
level_3:
  score: 88
  pass: true
  good_points:
    - 専門スタッフの役割分担が図と文章で一致する
    - 不足時にSTOPPEDへ進む安全境界が見える
  required_fixes: []
  suggested_revisions:
    - M30を「30分のまとまり」と併記する
level_4:
  score: 86
  pass: true
  good_points:
    - データと状態の関係に絞っている
    - TargetPositionとOrderIntentを区別している
  required_fixes: []
  suggested_revisions:
    - 状態図の読み方と将来Paper境界を図の前に補足する
```

## 3. 必須品質確認

| 確認項目 | 結果 | 証拠 |
|---|---|---|
| Mermaid構文・描画 | `PASS`。9ブロックすべてparse/render成功 | `evidence/mermaid/RQU-08C_candidate_render_result.txt` |
| 空図 | `PASS`。9ブロックすべて本文あり | 同上 |
| 色以外の識別 | `PASS`。図中ラベル、`[未承認]`、`[将来計画]`、STOPPED、破線を併用 | 候補HTML各図 |
| 切れ・重なり | `PARTIAL`。JSDOM SVG生成は成功。実ブラウザ目視は`RQU-UNK-01` | 同上、統合台帳 |
| UTF-8 | `PASS`。置換文字なし | `evidence/RQU-08C_candidate_html_check_result.txt` |
| 目次・内部アンカー | `PASS`。8リンク、欠落0 | 同上 |
| ローカル相対リンク | `PASS`。外部リンク0、切れ0 | 同上 |
| スマートフォン幅 | `PASS`（静的確認）。viewport、700px media query、表の横スクロールあり | 同上 |
| 印刷 | `PASS`（静的確認）。print media query、図の改ページ抑制あり | 同上 |
| Mermaid資産 | `PASS`。ローカル`doc/assets`の2スクリプトが存在 | 同上 |
| 要求ID同期 | `PASS`。Markdown 48、HTML 48、片側のみ0 | `evidence/RQU-08C_requirement_id_sync_result.txt` |
| 数式 | `PASS`。数式記法・数式ブロックなし。`1N`等のドメイン記号は削除せず、比較基準として説明 | 候補Markdown/HTML |
| 投資助言・利益保証 | `PASS`。固定範囲の証拠と将来未承認を分離し、利益保証を否定 | 候補文書6章・Unknown章 |

## 4. 採否

| 指摘ID | 重要度 | 判定 | 次工程での扱い |
|---|---|---|---|
| RQU-08C-001 | Medium | 採用 | Level 1〜4の初出専門語に短い日本語説明を加える。要求ID、型名、安全警告は維持する。 |
| RQU-08C-002 | Low | 採用 | 状態図の読み方と、Paperは将来・未承認であることを図の直前に再掲する。 |
| RQU-08C-003 | Low | 採用 | `Q1〜Q30`と`OD-01〜OD-08`をHTMLでも行単位に追跡できるようにする。これはRQU-08A/Bの指摘と統合する。 |
| RQU-08C-004 | Info | 保留 | 実ブラウザの文字配置は`RQU-UNK-01`として再レビューで状態を引き継ぐ。スクリーンショットを取得できる環境で再確認する。 |

## 5. RQU-08C完了判定

- 各C4 Levelは85点以上: `PASS`
- Mermaid構文エラー: `0`
- 静的に確認できるリンク切れ: `0`
- Markdown/HTML要求ID差分: `0`
- Critical/Highの新規指摘: `0`
- 実ブラウザ目視: `RQU-UNK-01`として未PASS
- RQU-09Aへの引き渡し: `PASS`

RQU-09Aでは、RQU-08A/RQU-08B/RQU-08Cの採用指摘を候補Markdown・候補HTMLへ反映し、RQU-09Bで全検証を再実行する。
