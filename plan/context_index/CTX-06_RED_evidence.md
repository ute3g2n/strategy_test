# CTX-06 RED検証証跡

- 計画: `CTXMAP-PLAN-001 v0.1`
- Step: `CTX-06`
- 実行日: `2026-08-14`
- 対象: manifest先行ルーター、ローカルstdio MCP、bounded JIT取得、router fixture

## RED条件

CTX-06の受入条件を先にテストへ固定した。

- Routerは検証済みmanifest以外を受け付けず、primary 1〜3件、supporting 0〜6件、JIT範囲、理由、snapshot hash、request ID、receiptを返す。
- MCPの`search_context`はmanifest metadataだけを返し、`get_artifact`／`get_code_slice`は登録済みIDと狭い範囲だけを読む。
- `get_related`はrelation graphだけを読む。
- `max_chars<=12000`、search limit<=20、related depth<=1を fail-closed で強制する。
- repo外path、`..`、Windows絶対path、Secret path/content、prompt injection文書、stale hash、invalid UTF-8、未知ID／symbolを拒否する。
- stdio以外のHTTP／TCP listenerを作らず、JSONLのエラーに本文・Secret・tracebackを出さない。

## RED実行結果

実装前に次を実行した。

```powershell
& .\\.venv\\Scripts\\python.exe -m pytest tests/context_index/test_context_router_mcp.py -q
```

結果:

```text
ModuleNotFoundError: No module named 'scripts.context_index.context_mcp_server'
```

テストcollectionが、未実装の`context_mcp_server.py` importで停止した。これはCTX-06実装不足による意図したREDであり、無関係な構文エラーや依存取得失敗ではない。

## REDからGREENへの対応表

| REDテスト対象 | 実装入口 | GREENで保証すること |
|---|---|---|
| Router strict output・snapshot | `scripts/context_index/context_router.py` | manifestだけで決定的にIDを選び、本文を読まない |
| Search metadata・limit | `scripts/context_index/context_mcp_server.py` | metadataのみ、20件以下、query上限 |
| Document JIT | `ContextMcpServer.get_artifact()` | allowlist、ID、hash、UTF-8、Secret、prompt injection、rangeを検証してから読む |
| Code JIT | `ContextMcpServer.get_code_slice()` | 登録symbol／line範囲だけ、hashとSecretを検証して読む |
| Relation JIT | `ContextMcpServer.get_related()` | graphの1-hopだけ、本文を読まない |
| stdio境界 | `ContextMcpServer.serve_stdio()` | JSONLだけ、未知toolと壊れたrequestをredactして拒否 |
| 回帰fixture | `context/routing_fixtures.json` | 10件以上の依頼で期待primary集合を固定 |

実装後のGREEN証跡は`CTX-06_GREEN_evidence.md`へ分離して保存する。
