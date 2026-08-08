# P2-09 Data Quality / Replay検証結果

Run ID: `RUN-P2-RPL-001`  
実行日: 2026-08-08

## 判定

Data Quality / Replayの固定fixture検証はPASSした。固定fixtureからは `data_version=dv_ed27a1e51b4a39bef629`、quality report hash `sha256:39de9d12fc61df12cec6c8a4eafb3f1a8cf40772955ae05f94afd3e8f5cccc9b` を再現できる。

一方、P2-08で取得したDatabento DBNはchecksum確認までで、DBN decoderを介したNormalizedBar / MarketEvent変換は未実装である。したがってData Gateは `UNKNOWN`、Signal生成とPhase 3 handoffは許可しない。これは失敗をPassへ変換せず、H2-3の採否対象へ送る判定である。

## 検証項目

| 項目 | 結果 | 根拠 |
|---|---|---|
| 欠損・重複・時刻逆行・異常価格・出来高・checksum・degraded | PASS | `QualityChecker` とP2-06固定fixtureの全ケース |
| 同一data_version / MarketEvent系列 | PASS（fixture限定） | 同一Manifest入力から `dv_ed27a1e51b4a39bef629` と固定2イベントを再現 |
| 条件付き銘柄混入 | PASS | `MZC/MZS/MZW` と本線 `MCL/M6A` が非交差 |
| Databento DBN checksum | PASS | P2-08 raw SHA256 `8fd0286a477e073c83e8306c4e1a8ebec3af693141010563edd7e0ec1990b65e` |
| DBN→NormalizedBar→MarketEvent | UNKNOWN | decoder・変換境界が未実装 |
| Phase 3 handoff | NOT_READY | Data Gate UNKNOWNのため停止 |

## 再開条件

DBN decoderまたは同等の固定変換境界を実装し、実取得DBNからUTC・InstrumentId・品質flags付きNormalizedBar / MarketEventを生成する。P2-06異常ケース、Manifest再現、条件付き銘柄分離、WSL固定4 Gateを再実行し、H2-3で採否を判断する。
