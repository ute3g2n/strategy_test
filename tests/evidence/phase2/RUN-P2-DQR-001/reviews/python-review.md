# P2-06 Python品質レビュー（Findings first）

## Findings

### DQR-PY-001 / Medium / Open

- 対象: `tests/market_data/test_data_quality_replay_contract.py`
- 内容: `ReplayGate`の実装がまだ存在しないため、未来の足を追加して過去の公開済みイベントが変わらないことは、現時点ではfixtureの契約値の確認に留まる。
- 判定: P2-06ではRED契約として許容するが、P2-07で`MarketEvent`とReplay実装を追加した後、短い入力と未来足を含む入力を実際に再生して同一履歴を比較するテストへ昇格する。
- 重大度理由: 未実装境界をPass扱いしていないためCritical/Highではない。ただしP2-09の検証結果へこの契約テストのGREENを記録するまで、Phase 3入力へ昇格してはならない。

## 確認済み

- 既存Catalog Resolverテストは9件GREEN。
- P2-06追加テストは、未実装`manifest`境界でcollection REDとなり、skipや期待値の緩和で隠していない。
- 固定fixtureにSecret、Account ID、API key、外部接続設定はない。
- 現在時刻をfixture内容や`data_version`計算の入力にしていない。
- 品質印（欠損、重複競合、時刻逆行、価格・出来高異常、checksum不一致、degraded）は、データ版発行不可・Signal停止として固定した。

## 再レビュー条件

P2-07で次のモジュールが実装された後に再レビューする。

- `store_contracts.py`
- `quality.py`
- `manifest.py`
- `normalized_store.py`
- `replay`境界（未来足と過去履歴の不変性を実行するもの）
