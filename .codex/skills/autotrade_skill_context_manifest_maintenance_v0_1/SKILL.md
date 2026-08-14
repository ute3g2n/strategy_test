---
name: autotrade_skill_context_manifest_maintenance_v0_1
description: 新規Markdown・HTML文書または大幅変更文書を1ファイル単位で判定し、hashを取得せず、ローカルcontext metadataの追加・更新・blocked判定をstrict JSONで返す。
---

# autotrade_skill_context_manifest_maintenance_v0_1

## 目的

文書を保存したときに、案内図（context metadata）へ載せるべき構造情報を安全に更新する。管理・参照効率化・実行証跡・ファイル同一性確認のためのhashは取得、保存、照合しない。コードの構文解析、Git操作、commit前Gateは本Skillの責務外とし、決定的なローカル処理へ渡す。

## 発火条件

- 新規の管理対象Markdown（`.md`）またはHTML（`.html`）を追加したとき。
- 既存の管理対象文書で、見出し、目的、責務、契約、入出力、関連リンク、保存先などが大幅に変わったとき。
- 大幅変更か不明なとき。本文を推測せず、入力された構造化差分だけで判定する。

## 入力契約

入力は必ず1ファイル分だけとし、次の情報に限定する。

- `relative_path`: リポジトリ内の相対path。絶対path、`..`、repo外pathは禁止。
- `kind`: `managed_document` のみ。ソースコードは決定的コード解析へ渡す。
- hash値を入力しない。安全・データ・再現性に直結するhashはこの文書管理Skillへ渡さず、該当する専用経路で扱う。
- `structural_diff`: 旧新の見出し、title、長さ、リンク、責務語の差分だけを含める。推測や全文ダンプを入れない。
- `existing_record`: 既存のmanifestレコード、または新規なら`null`。
- `safe_excerpt`: 秘密を検査済みの本文抜粋。最大18,000文字。全文保存の代替として使用しない。
+ `request_id`、`schema_version`、`generator_version`、`receipt`。管理用input hashは入力しない。

## 出力契約

追加の説明文やMarkdownを混ぜず、次のキーだけを持つstrict JSONを返す。`additionalProperties`は禁止する。

`artifact_id`、`action`、`summary`、`purpose`、`triggers`、`headings`、`relations`、`confidence`、`reason`、`receipt`

`action` は次のいずれかとする。

- `record_add`: 新規文書。既存レコードがあってはならない。
- `record_update`: 大幅変更により要約、目的、見出し、関係の更新が必要。
+ `metadata_unchanged`: 大幅変更ではなく、意味的レコードは維持して更新時刻・receiptだけを更新。
+ `blocked`: 入力不正、対象外、Secret疑い、path境界違反、excerpt上限超過、判断材料不足、schema不整合。

## 実行手順

1. `relative_path`を正規化し、repo内の1ファイルであることを確認する。
2. `kind`、拡張子、対象policy、excerpt長、入力schemaを検証する。
3. Secretらしい値、認証情報、APIキー、個人情報の疑いを検査する。疑いがあれば本文を要約せず`blocked`にする。
4. 新規なら`record_add`、既存の大幅変更なら`record_update`または`metadata_unchanged`を選ぶ。大幅変更を小変更として扱わない。
5. heading、purpose、relationsは入力された安全な範囲からのみ作り、存在しない事実を補完しない。
6. receiptへgenerator、判定時刻、境界判定、理由を記録する。管理用hashは記録しない。
7. strict JSONを検証し、manifest writer/validatorへ渡す。A07自身はmanifestを直接書き換えない。

## 安全境界

- ネットワーク、外部MCP、外部本文送信、Secret読取、環境変数の秘密値取得を行わない。
- 任意path、repo外path、複数ファイル、Git stage/commit/push、watcher起動を行わない。
- 本文全量、safe excerpt超過分、未検査ログを出力・保存しない。
- `Unknown`、runtime未起動、timeout、validator不合格を`pass`へ変換しない。
- A07の出力だけでは作業完了とせず、validatorのPASS、または理由付きBLOCKEDを上位へ返す。

## 品質チェック

- 新規文書は必ず`record_add`である。
- 既存文書は旧artifact_idを維持し、rename/deleteはmanifest state管理へ渡す。
+ path、artifact_id、receiptが一致する。hash一致はこのSkillの品質条件にしない。
- `headings`、`relations`、`triggers`の上限と型をschemaで検証する。
- A07が処理できない入力は、原因、再開条件、必要な追加情報をreceiptへ残してfail-closedにする。

## 参照成果物

- `plan/context_index/CTX-01_資料コード参照基盤詳細設計候補.md`
- `plan/context_index/CTX-01_マニフェストschema案.json`
- `plan/資料参照効率化施策_全体導入実行計画書_v0.1_2026-08-14.md`
