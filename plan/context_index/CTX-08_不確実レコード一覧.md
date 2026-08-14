# CTX-08 不確実レコード一覧

## 判定

CTX-08のA07固定runtimeが利用できなかったため、active document全件について、意味要約・目的・発火条件・relationsのA07確認状態は `UNCONFIRMED_A07_RUNTIME_UNAVAILABLE` とする。これは本文の欠落や捏造を意味せず、決定的抽出された見出し、hash、path、local linkをsemantic approvalと混同しないための状態である。

## 集計

| レコード群 | 件数 | 状態 | 再開条件 |
|---|---:|---|---|
| active managed document | 425 | `UNCONFIRMED_A07_RUNTIME_UNAVAILABLE` | A07 strict receipt、source hash一致、validator PASS |
| code extraction COMPLETE | 217 | deterministic complete | source hash再検証、構造変更時の再抽出 |
| code extraction PARTIAL | 37 | `PARTIAL` | parser拡張または人間確認。ただし推測でCOMPLETEへ昇格しない |
| code extraction BLOCKED | 0 | none observed | 新規BLOCKEDは原因と再開条件をreceiptへ保存 |
| unregistered managed document/source | 0 | PASS | 新規追加時にGateとA07へ渡す |

## PARTIALの扱い

PARTIALの個別ID、path、diagnosticsは `context/code_manifest.json` を正本とする。構文解析不能、保守的regex、未解決import、rename ambiguityを、存在しない関係や意味で補完してはいけない。

## A07再開手順

1. A07 runtimeの固定model・agent_id・独立性を確認する。
2. 1文書ずつ、`relative_path`、source hash、構造差分、既存record、安全excerptだけを渡す。
3. strict JSONの`record_add`／`record_update`／`metadata_unchanged`を検証する。失敗、timeout、Secret、path違反はBLOCKEDのままにする。
4. receipt、manifest、state、relation graphを更新し、全validatorとrouting fixtureを再実行する。

本文全量、Secret、外部送信、未承認watcherは再開条件に含めない。
