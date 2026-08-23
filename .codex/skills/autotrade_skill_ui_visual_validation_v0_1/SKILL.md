---
name: autotrade_skill_ui_visual_validation_v0_1
description: 固定条件のPC・スマートフォン画面をスクリーンショット比較し、UIモックの見た目と操作意味の差分を検証する。
---

# autotrade_skill_ui_visual_validation_v0_1

このSkillは `settings/ai_component_rules.md#共通PRODUCT_ONLY部品契約` を継承する。視覚差分の製品品質確認は維持するが、run_id、evidence_root、HTMLレポート、Trace、台帳差分は依頼または再現可能な検証に必要な場合だけ使う。

## 目的

固定Seed、固定基準日時、固定viewport、固定ブラウザでUIモックを撮影し、画面の見切れ、重なり、状態表示の欠落、PCとスマートフォンの意味差を検出する。視覚検証は機械的な差分確認であり、運用者の最終承認を代替しない。

## 入力

- 対象画面、固定条件、期待状態。`phase_id`、`step_id`、`evidence_root`、`human_gate_policy`は依頼または安全上必要な場合だけ使う。
- 対象画面ID、ユースケースID、テストID、期待状態、重要操作
- 固定Seed、固定日時、viewport、ブラウザ、フォント、locale、timezone
- ベースライン画像、許容差方針、差分の重大度基準
- `@playwright/test` の正式設定と、必要に応じたStorybookのURL

## 出力

- PC幅・スマートフォン幅のスクリーンショットと比較結果
- 差分画像、Playwright Trace、HTMLレポートへのリンク
- 見切れ、重なり、コントラスト、文字欠落、状態不一致のFindings first一覧
- Critical/High/Medium/Lowの重大度、再現手順、修正要求、Unknown台帳差分

## 実施規約

1. ベースラインの作成条件を先に記録し、同じ条件で再実行する。
2. 21画面・10共通状態のうち対象範囲を明記し、未確認画面をPass扱いしない。
3. PC幅とスマートフォン幅で、主要なラベル・警告・停止・取消・復旧導線の意味が変わらないことを確認する。
4. スクリーンショット差分だけでなく、キーボード操作と画面状態の変化をテストIDへ結び付ける。
5. 失敗時のHTMLレポート、Trace、比較画像は、再現可能な検証を依頼された場合だけ`tests/evidence/{phase_id}/{run_id}/`へ保存する。通常は失敗内容をチャットで報告する。

## 正式確認と探索補助の境界

- 正式な合否は、固定された`@playwright/test`、`toHaveScreenshot`、E2E期待値、受入確認表で判定する。
- AI向け`playwright-cli`は、Human Gateで許可された場合に匿名のローカルモックを探索する補助に限る。探索結果だけでPassにしない。
- MCP、外部AIサービス、共有Storage、ログイン済みブラウザ、実Broker画面は扱わない。

## 禁止事項・境界

- 実市場データ、実口座、実注文、Secret、個人情報、外部送信を行わない。
- ベースラインを黙って更新して差分を隠さない。変更理由と必要な承認状態をチャットまたは依頼された成果物へ記録する。
- 表示が似ていることだけで安全要件、Human Gate、Live自動承認をPassにしない。

## 品質チェック

- viewport、ブラウザ、Seed、基準日時、locale、timezoneが、比較結果または依頼された証跡に記録されている。
- Critical/High差分が0件であること、またはH2/H3へ明示的に引き継がれている。
- PC・スマートフォン双方で主要画面のスクリーンショットが存在する。
- 差分のない画面も対象・条件・結果を報告し、未実行を成功と扱わない。
- TraceとHTMLレポートを作成した場合だけ、ローカルリンクを確認する。

## Phase依存パラメータ

- `phase_id`
- `step_id`
- `evidence_root`
- `run_id`
- `human_gate_policy`
- `viewport_policy`
- `baseline_policy`
- `unknown_policy`

## 参照成果物

- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`
- `doc/ai_foundation/06_AI部品相関図発火制御図.html`
- `plan/requirements_update/RQU-UI_要件UIテスト追跡マトリクス_2026-08-11.md`
- `ui/mock/playwright.config.ts`
