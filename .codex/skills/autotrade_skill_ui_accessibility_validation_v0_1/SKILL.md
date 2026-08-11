---
name: autotrade_skill_ui_accessibility_validation_v0_1
description: UIモックの名前、役割、キーボード操作、focus、コントラストをaxeと実ブラウザで検証する。
---

# autotrade_skill_ui_accessibility_validation_v0_1

## 目的

画面を色だけに頼らず読めて、キーボードでも操作でき、Dialog・Form・Tableの名前と役割が伝わることを機械検査と実ブラウザ操作で確認する。axeの結果は重要な入力と結合し、運用者が安全状態を理解できるかを別途確認する。

## 入力

- `phase_id`、`step_id`、`evidence_root`、`human_gate_policy`
- 画面ID、UI状態ID、テストID、重要操作、警告・停止・復旧の文言
- Storybook、Vitest、`@storybook/addon-a11y`、`axe-core`の設定
- PC・スマートフォンviewport、キーボード操作表、期待されるfocus順
- ダミーデータのSeed、基準日時、locale、timezone

## 出力

- axeおよびStorybook a11yの結果、対象画面・対象状態・違反ルール
- Tab/Shift+Tab、Enter、Space、Escape、Dialog閉じる操作の証跡
- focus表示、見出し、label、role、表の見出し、エラーメッセージのFindings first一覧
- jsdomと実Chromiumの差分、再現手順、重大度、修正または後続Gateへの引き継ぎ

## 実施規約

1. 通常、未入力、未承認、警告、停止、失敗、復旧待ち、データなしの代表状態を対象にする。
2. UI要素の名前と役割を、色・アイコンだけでなく日本語の文字でも表す。
3. Dialogは開く、focusを受ける、Escapeまたは取消で閉じる、元の位置へ戻る流れを確認する。
4. Formはlabelとエラーの関係を確認し、Tableは列見出しと行の意味を確認する。
5. axeで検出されない操作不能、意味不明な状態、見切れは手動・Playwrightで別に記録する。

## 禁止事項・境界

- 実口座、実注文、Secret、個人情報、外部サービスに接続しない。
- jsdomの警告を勝手に無視してPassにしない。実Chromiumでの確認が必要な項目はUnknownとして残す。
- 色コントラストが通ったことだけでHuman Gate、安全停止、Live自動承認をPassにしない。

## 品質チェック

- axeのCritical/Serious（またはプロジェクト重大度でCritical/High）違反が0件。
- 主要操作がキーボードだけで到達・実行・取消でき、focusが視認できる。
- `aria`属性やroleを追加した場合、実際の画面名・役割・状態と一致している。
- 実Chromiumの証跡があり、jsdomのみの成功を正式合否にしない。
- 未確認viewport・未確認状態・警告をUnknownに残し、決定時期・開始条件・停止条件・証拠先を付ける。

## Phase依存パラメータ

- `phase_id`
- `step_id`
- `evidence_root`
- `run_id`
- `human_gate_policy`
- `viewport_policy`
- `keyboard_policy`
- `unknown_policy`

## 参照成果物

- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`
- `doc/ai_foundation/07_AI部品作成ルール.html`
- `ui/mock/src/App.test.tsx`
- `ui/mock/.storybook/preview.ts`
