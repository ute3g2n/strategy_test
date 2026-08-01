---
name: fidelity-reviewer
description: Compare a simplified Japanese explanation against the original research chapter to ensure meaning, risk warnings, and key rules are preserved. Use when simplified text must remain faithful and avoid investment advice.
---

# Fidelity Reviewer

## 1. 目的

原文と中学生向け本文を比較し、意味が変わっていないかを確認する。

## 2. 入力

- 対象章の原文
- 中学生向け本文
- 章の重要点一覧
- 合格ライン

## 3. 出力

```yaml
score: 92
pass: true
preserved_points:
  - 値動きに応じて取引量を変える考え方が残っている
missing_or_weakened_points:
  - ギャップで損失が予定より大きくなる説明が弱い
required_fixes:
  - ストップは損失を保証しない点を追加する
```

## 4. 処理手順

1. 原文の重要点一覧を確認する。
2. 中学生向け本文に各重要点が残っているか確認する。
3. 数式を消した結果、条件や意味が不正確になっていないか確認する。
4. リスク説明が弱くなっていないか確認する。
5. 原文にない断定や約束が追加されていないか確認する。
6. 投資助言のような表現がないか確認する。
7. 100点満点で採点し、90点以上を合格にする。

## 5. 禁止事項

- わかりやすさを理由に、意味の変化を見逃さない。
- リスク説明の弱体化を許可しない。
- 原文にない断定を許可しない。
- 投資助言のような表現を許可しない。
- 数式を復活させる修正案を出さない。

## 6. 品質チェックリスト

- 原文の重要ルールが残っている。
- 注意点とリスクが残っている。
- 簡単にした結果、意味が大きく変わっていない。
- 投資成果を約束していない。
- スコアと合否がある。

## 7. 失敗時の扱い

原文との比較ができない、重要点が大幅に不足している場合は、次を返す。

```yaml
error: true
reason: fidelity_review_failed
message: 原文忠実性レビューを完了できませんでした。
pass: false
required_fixes:
  - 原文の重要点を再確認する
```
