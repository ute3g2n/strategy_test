# CTX-08 初回全量マニフェスト化レポート

## 1. 実行概要

CTX-00でmanaged対象としたMarkdown、HTML、ソースコード、設定を、ローカル決定的抽出で一回走査した。本文を外部へ送信せず、文書本文をrouter入力へ渡さず、生成物とruntime状態は索引対象の境界から分離した。

このレポート自身と「不確実レコード一覧」を追加した後の最終マニフェストを正本とする。CTX-08の全量化は一回限りのバッチであり、CTXMAP-H1前の常駐watcherや保存時自動A07は起動していない。

## 2. 対象範囲と境界

| 区分 | 対象 | 抽出方式 | 境界 |
|---|---|---|---|
| 文書 | `README.md`、`AGENTS.md`、`doc/`、`plan/`、`research/`、`settings/`、`.codex/`の`.md`／`.html` | UTF-8、安全path、見出し、title、trace ID、local link、hash | `node_modules`、`.venv`、`third_party`、raw／build／dist、Secret疑いpathを除外 |
| ソース | `.codex`、`context`、`scripts`、`settings`、`src`、`tests`、`plan`と、rootの明示config／auto-commit入口 | Python AST、各言語の保守的regex、設定metadata | 本文を保存せず、構文解析不能・保守的抽出はPARTIAL |
| 生成物 | `context/*_manifest.json`、`context/relation_graph.json`、`plan/context_index/runtime/` | 境界として扱う | 自分自身の変更で再発火させない |
| 外部／第三者 | `third_party/`、外部MCP、外部vector DB、Cloud、Broker、Secret | 対象外 | 本文取得・送信・認証は実施しない |

## 3. coverageと品質結果

最終数値は `context/artifact_manifest.json`、`context/code_manifest.json`、`context/relation_graph.json` の検証結果と一致させる。

- 文書: 425件（active）、未登録0、重複ID／path 0、stale hash 0。
- ソース／設定: 254件、COMPLETE 217件、PARTIAL 37件、BLOCKED 0件、未登録0。
- 関係グラフ: 文書link、REQ／DEC／UNK／ART trace、AI部品、importを証拠ラベル付きで格納する。未解決local referenceは推測で補完せずPARTIALにする。
- routing fixture: 10件すべてで期待primary許容集合を確認する。主資料は最大3件、補助資料は最大6件に制限する。
- MCP: local stdioだけを使用し、repo外path、traversal、Secret、prompt injection、巨大範囲、invalid UTF-8、未知IDを拒否する。

## 4. A07 runtime状態

CTX-08で固定された `AutoTrade_A07_ContextManifestMaintainer_v0_1` のモデル `gpt-5.1` はruntimeから `Unknown model` として拒否された。したがって、各文書の意味要約・purpose・relation判定をA07が完了したとは扱わない。決定的抽出で作ったmanifestは、構文・hash・coverageのローカル基盤としてだけ受け入れ、semantic A07承認は未成立として残す。

`plan/context_index/CTX-08_dispatch_receipt_index.json` はこの状態を全managed documentへ適用する索引であり、起動不能文書を成功扱いしない。A07が利用可能になった場合の再開条件は、対象1文書のsafe input、strict JSON receipt、source hash一致、validator PASS、receipt保存である。

## 5. 再現コマンドと証拠

```text
python -m scripts.context_index.build_context_index --root . --policy context/context_policy.json --output context/artifact_manifest.json --state-output context/manifest_state.json
python -m scripts.context_index.build_code_manifest --root . --policy context/context_policy.json --output context/code_manifest.json --existing-manifest context/code_manifest.json
python -m scripts.context_index.build_relation_graph --code-manifest context/code_manifest.json --document-manifest context/artifact_manifest.json --output context/relation_graph.json
python -m pytest tests/context_index -q --cov=scripts/context_index --cov-report=term
```

実際の出力・hash・runtime制限は `plan/context_index/CTX-08_dispatch_receipt_index.json` とCTX-08のreceiptへ固定する。Trusted scope未登録のためWSL固定4 Gateは実行していない。
