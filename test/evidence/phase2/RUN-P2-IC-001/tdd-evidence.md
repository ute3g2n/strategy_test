# RUN-P2-IC-001 TDD 証跡

対象は P2-D07 の `CatalogResolver.resolve`（REQ-Q02 / REQ-Q19 / REQ-Q20 / REQ-Q23）。固定 JSON fixture のみを使用する。

| 段階 | 実行 | 結果 |
|---|---|---|
| RED | `.venv\Scripts\python.exe -m pytest tests\market_data\test_catalog_resolver.py -q` | `ModuleNotFoundError: No module named 'autotrade'`。未実装の想定どおり失敗。 |
| GREEN | `.venv\Scripts\python.exe -m pytest tests\market_data\test_catalog_resolver.py -q --cov=autotrade.market_data.catalog_resolver --cov-report=term-missing` | 9 passed、coverage 91%。 |
| 静的検査 | `.venv\Scripts\python.exe -m compileall -q src\autotrade\market_data` | 成功。 |
| 安全ソース検査 | `rg` で socket / HTTP client / subprocess / Databento / Broker / env 読取りを検索 | 該当なし。 |

保証する振る舞い: 一意かつ active で tick size を持つ有効期間内の mapping だけが、in-memory監査の成功後に `resolved` となる。0件、複数、pending・属性不足、naive UTC、非UTC・不正 fixture、監査失敗は、推測せず停止する。
