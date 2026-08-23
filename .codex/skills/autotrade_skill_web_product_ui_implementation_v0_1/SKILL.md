# autotrade_skill_web_product_ui_implementation_v0_1

このSkillは `settings/ai_component_rules.md#共通PRODUCT_ONLY部品契約` を継承する。ユーザーに部品名を要求せず、UI品質に必要な関連テストを自動選択できる。Run Manifest、Evidence、capture registry、独立レビューは依頼または製品品質上必要な場合だけ作成・実施する。

## 目的

型付きのローカルApplication APIへ接続するWeb製品UIを、既存のUIモック構造から安全に移行するための汎用Skill。Backtest計算、結果の捏造、外部接続をUIへ持ち込まない。

## 入力

- 承認済みの実装詳細設計、UI契約、Application API契約。Run Manifestは再現可能な検証を依頼された場合だけ使う。
- 既存UIのコンポーネント、Playwright設定、アクセシビリティ契約
- 固定されたローカルfixture。Evidence rootは再現可能な検証を依頼された場合だけ使う。

## 手順

1. UIモックと実Application APIの差分を調べ、既存の画面構造・可視名・キーボード順を壊さない移行単位を決める。
2. API入力を型付きの境界で組み立て、入力検査・実行・進捗・結果・失敗理由をUI状態へ写像する。UI内で計算しない。
3. `@playwright/test`でrole/label/testidを使う操作を用意し、ネットワーク要求、Secret/PII表示、状態遷移、PC/mobile、keyboard/focusを検査する。
4. assertが通った同一画面のPNG保存やcapture registry連携は、UI品質の確認または再現可能な検証に必要な場合だけ行う。画像の手作業加工は禁止する。
5. visual/a11yの確認は変更リスクに応じて自動選択し、Unknown、Critical、High、未確認viewportをPassにしない。

## 必須の停止条件

- Application APIの結果が未接続、型不一致、またはUIが計算結果を生成している。
- 固定ダミーを実結果と表示する、外部通信、Broker、Secret、認証/権限、実注文、実口座、実資金、Cloudが見つかる。
- response待ちを伴わない任意sleep、曖昧なCSS依存、未確認のa11y/viewportを合格にする。
- Playwrightのassert前に撮影する、またはcaptureのsource run/fixture/AC追跡が欠落する。

## 出力

- UI実装差分、型付きAPI接続、状態表示、Playwright journey/Page Object、capture registry連携
- 失敗時の停止理由と、必要な場合のEvidenceへの参照

## 禁止事項

このSkillはPython Backtest Coreを変更しない。UIにData取得・指標計算・投資判断を実装しない。管理用hash、manifest fingerprint、stale判定、hash retryを追加しない。protected hashを使う場合も、直接のData identity/再現性と失敗時停止範囲を別途明記する。
