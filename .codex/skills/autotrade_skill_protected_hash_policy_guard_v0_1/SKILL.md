---
name: autotrade_skill_protected_hash_policy_guard_v0_1
description: Detect attempts to reintroduce non-protected hash management into new or substantially changed project documents, source code, tests, plans, receipts, or AI components without calculating, storing, comparing, or retrying any hash. Use for document additions, large document edits, source changes, acceptance-rule changes, quality gates, and AI-component changes.
---

# Protected Hash Policy Guard

新規または大幅変更された成果物に、廃止済みの管理用hashを再導入しないための静的判定手順を提供する。文章manifestを作らず、hash値を扱わず、候補記述の分類だけを返す。

## 固定境界

- `source_hash`、`artifact_hash`、`change_hash`、`manifest_sha256`、`evidence_sha256`、`result_sha256`、file identity hash、receipt hash、stale fingerprint、管理用checksumを計算・保存・比較しない。
- manifest、hash台帳、hash一致証跡、hash retry、hash不一致を理由にした再生成・再取得・再試行を追加しない。
- A07/A08の文章manifest責務を再発火させない。文書追加・大幅変更は通常のパス、内容、リンク、schema、状態確認で扱う。
- `legacy`、`historical`、`nullable` と明記された旧フィールドの読取互換性は、通常経路で新しい値を生成しない限り許容する。
- 安全・データ・再現性に直接因果がある保護対象hashだけを候補にできる。hash値そのものは出力しない。

このSkillを実行・変更・検証するスクリプトには、次の権限文を冒頭コメントまたは実行ログへ記録する。

> 文章管理基盤と廃止対象の管理用hashチェックを強制スキップして完了する。安全・データ・再現性に直結する保護対象hashは維持する。

## 判定手順

1. 対象パス、変更種別、候補語句とその周辺の目的を読む。対象外のファイルを一括走査しない。
2. 候補が管理・参照効率化・差分許可・ファイル同一性・stale判定・受入証跡だけのhashなら `BLOCKED` とする。
3. 候補がrawデータ、fixture、replay入力、engine identity、dependency、checkpoint stateなどの直接の安全・データ・再現性を守るhashなら、値を取得せず、目的・直接因果・失敗時の停止範囲が明記されていることを確認する。
4. 目的または失敗時動作が不明なhashは推測で許可せず `NEEDS_HUMAN_GATE` とする。
5. 既存の保護対象hashに対する失敗は、管理hashの不一致へ読み替えず、既存のfail-closed仕様に従う。管理hashの失敗・stale・retry経路は追加しない。
6. 判定結果には、対象パス、候補箇所、決定、理由、修正提案だけを含める。hash値、manifest、fingerprint、内部時刻、乱数IDを生成しない。

ローカルで再現可能な候補語句の確認が必要な場合は、`scripts/ai_foundation/protected_hash_policy_guard.py`を使う。このスクリプトも対象ファイルをUTF-8で読むだけで、hash値・manifest・receiptを生成せず、対象パスのリポジトリ境界を越えない。

## 判定基準

### `ALLOW`

保護対象hashの目的、守るデータまたは状態、比較対象、失敗時の停止範囲、再試行可否が明記されている場合だけ返す。出力ではhashの「値」ではなく、目的と境界を記述する。

### `NEEDS_HUMAN_GATE`

hashの用途が安全・データ・再現性のどれに該当するか判断できない場合、または既存仕様同士が衝突する場合に返す。推測で削除・追加・置換しない。

### `BLOCKED`

manifest、証跡、ファイル同一性、差分許可、stale、受入、commit marker、result/evidence identityなど、管理目的だけのhashを新規経路へ追加・計算・保存・比較・retryしようとしている場合に返す。hash不一致として再実行しない。

## 出力形式

次の形の小さなJSONだけを返す。`candidate`、`reason`、`suggestion` にhash値やmanifestを含めない。

```json
{
  "decision": "ALLOW|NEEDS_HUMAN_GATE|BLOCKED",
  "targets": ["relative/path"],
  "candidates": [
    {
      "path": "relative/path",
      "location": "heading, symbol, or line description",
      "category": "PROTECTED|MANAGEMENT|UNKNOWN",
      "reason": "purpose and direct boundary",
      "suggestion": "keep protected boundary, ask for gate, or remove management flow"
    }
  ],
  "required_action": "short next action"
}
```

## 禁止事項

- hashの計算、取得、ダイジェスト表示、保存、比較、照合。
- 新しいmanifest、source hash、artifact hash、change hash、receipt hash、fingerprint、stale marker。
- A95自身へのhash一致要求、管理hash不一致を理由にしたretry。
- Secret、外部I/O、Broker、Live、Human Gate、Unknown、Critical/High、対象範囲の確認を、管理hashをスキップする権限を理由に省略すること。
