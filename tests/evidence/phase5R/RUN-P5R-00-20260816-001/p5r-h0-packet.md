# P5R-H0 承認Packet

## 結論

P5R-H0を、ユーザーが2026-08-16に「全実行を完遂するまでに必要となる全Human Gateの承認権限を移譲」したことに基づき、**代理承認**する。承認はP5Rの固定範囲に限り、OPEN Unknownを解決済みとは扱わない。

## 承認する範囲

| 項目 | 固定した内容 |
|---|---|
| Data | 既存ローカルP5 Evidenceのみ。`BTCUSDT` / `ETHUSDT`、Crypto Spot、1m、UTC、`CRYPTO_24_7_UTC`。対象期間は `2025-02-24T00:00:00Z` 以上、`2026-08-01T00:00:00Z` 未満。既存の派生D1/H4/H1/M30/M15を使用可。品質PASS範囲だけを使用する。 |
| 保存 | 実行中のRun/Job/Checkpoint/操作記録はローカルApplication store、結果は相対 `results/<run_id>/`、CSVは相対 `csv/<job_id>/`、証跡は `tests/evidence/phase5R/<RunId>/`。実行用一時成果物の保持目安は30日。完了EvidenceはP5R完了判定後に手動で整理し、自動削除しない。上書きは禁止。 |
| 固定PC | Windows 11 Pro、Python 3.11.0、Node v24.14.0、論理32スレッド、物理メモリ約71.9GB。受入結果には実行時の環境を記録する。 |
| 標準負荷 | Sweep候補25件、同時実行1、見込み結果容量128MB以内、完了目安120秒以内。超過時は性能合格にせず、警告または拒否理由を表示する。 |
| 境界負荷 | Sweep候補200件まで、同時実行1、見込み結果容量512MB以内、上限600秒。201件以上、容量超過、タイムアウトは開始前に拒否する。 |
| 測定 | Playwright/APIのRun開始から全行終端までを計測し、候補数、経過時間、結果行数、概算容量、状態をEvidenceへ記録する。ベンチマーク値を保証値と表示しない。 |
| Holdout | 最終Holdoutは `2026-07-01T00:00:00Z` 以上、`2026-08-01T00:00:00Z` 未満。調整・候補選択前に読めず、確定後に一度だけ読める。 |
| Walk-forward | 半開区間、3窓、各窓 `train=60日`、`validation=15日`、`evaluation=15日`、stride=30日。W1は2025-02-24開始、W2は2025-03-26開始、W3は2025-04-25開始。train < validation < evaluation、重複・隙間・未来参照・Holdout再利用を拒否する。 |
| UI境界 | UIは計算しない。UI → 型付きApplication API → Backtest専用実行境界 → 既存Core/Data Adapter → 結果Artifactの一方向接続とする。 |
| AC | P5R-AC-01〜16を受入対象とする。正常系だけでなく、入力拒否、取消、失敗、再開、部分失敗、比較不可、CSV失敗、Holdout早期参照、Walk-forward未来参照拒否、keyboard/a11yを含む。 |

## 明示的な対象外

外部Data追加取得、Provider変更、Data再配布、Secret/API key、Broker、注文、実資金、Cloud公開、複数運用Unit、Portfolio、実運用Risk、OMS、Forward、Shadow、Paper、Live候補、小規模Live、通常LiveはP5Rに含めない。

## 未解決のまま残すUnknown

`P5R-UNK-001`（Provider利用・保持・再配布条件、P5-08 host isolation、P5時点のchild Agent未起動、execution cost実測不足）はOPEN_NOT_PASSとする。P5Rは既存ローカルEvidenceの読取りに限定し、外部取得や実市場コスト適合の根拠へ拡張しない。

## 次Stepへの許可

P5R-00A、P5R-01、P5R-02、P5R-02A、H1 packet作成までを許可する。H1承認前のP5R品質scope登録、実装、test subprocess、実UI接続、Playwright撮影は許可しない。
