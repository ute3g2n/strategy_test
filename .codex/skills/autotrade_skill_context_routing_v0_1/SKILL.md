---
name: autotrade_skill_context_routing_v0_1
description: 検証済みのローカルcontext manifestと依頼文だけから、必要な主資料・補助資料・JIT取得範囲を最小選定する。
---

# autotrade_skill_context_routing_v0_1

## 目的

大量の文書・コードを依頼ごとに全文投入せず、manifestの要約、見出し、関係、schema、状態を使って参照候補を絞る。本文を読むAgentではなく、参照計画だけを返す軽量ルーターとして動作する。管理用hashは扱わない。

## 入力契約

- schema、状態、path境界を非hashで確認済みのmanifest snapshot。
- 利用者の依頼文、対象Phase、許可されたpath境界、目的。
- 必要なら候補IDの明示リスト。候補本文、ソースコード本文、Secret、ログ全文は入力しない。

## 出力契約

strict JSONで、次のキーだけを返す。

- `primary_ids`: 主資料のartifact_idまたはcode_idを1〜3件。
- `supporting_ids`: 補助資料を0〜6件。主資料と重複させない。
- `jit_ranges`: 必要になった場合だけ取得する相対path、見出しまたは行範囲、取得理由。
- `rationale_by_id`: 選定理由。manifestに存在する事実だけを使う。
- `missing_information`: manifestにないため判断できない情報。
+ `request_id`、`receipt`。管理用snapshot hashは返さない。

## 実行手順

1. schema version、状態、path境界、対象種別を非hashで検証する。
2. 依頼の目的語、対象ID、関係、見出し、更新日時、confidenceをmanifest上で照合する。
3. 直接の正本を優先してprimaryを最大3件に絞る。
4. 根拠、依存、検証結果など必要最小限だけをsupportingへ最大6件選ぶ。
5. 本文をまだ読まないと判断できない点だけを`jit_ranges`へ相対pathと狭い範囲で記載する。
6. manifestにない情報は補完せず`missing_information`へ記録する。
7. schemaと上限を検証し、不正・Secret疑い・境界不明・状態不明は`blocked`相当のreceiptで返す。

## 安全境界

- 文書本文、コード本文、任意path、repo外pathを直接読まない。
- ネットワーク、外部MCP、Secret、Git操作、依頼外の資料探索を行わない。
- manifestが未検証、欠落、相互矛盾、状態不明の場合は候補を推測せず停止する。
- 候補選定結果を本文の正しさや設計承認と誤認させない。

## 品質チェック

- primaryは1〜3件、supportingは0〜6件である。
- 主資料は依頼に対する直接の正本で、選定理由がある。
- JIT範囲は必要最小限で、pathはmanifestの管理境界内である。
- missing_information、confidence、receiptを省略しない。
- schema、状態、path境界の非hash確認を通過していないmanifestからルーティングしない。

## 参照成果物

- `plan/context_index/CTX-01_資料コード参照基盤詳細設計候補.md`
- `plan/context_index/CTX-01_マニフェストschema案.json`
- `plan/資料参照効率化施策_全体導入実行計画書_v0.1_2026-08-14.md`
