# P2-12-02 実装・固定契約試験の記録

- Run: `RUN-P2-DBN-001`
- 対象設計: `P2-D16`
- H2-5: 承認済み（記録: `human-gate-user-declaration.md`）
- 実DBNを開いたか: いいえ。P2-12-03の保護されたWSL入力だけで行う。
- 外部接続・Secret・Broker・Signal生成: いずれも使用していない。

## 実装したこと

- 保存済みbytesのhashを先に照合してからDBNを読むAdapter
- 固定Catalogへ一意に結べない行を止める正規化処理
- BarとDBN内の順番を一組で保持する`DbnNormalizedRecord`
- 品質不合格ならMarketEventを0件にする処理
- DBN用の取得条件・decoder版・artifact hashを`data_version`へ結ぶManifest
- これらを書き換えたSnapshotを拒否するStore検査
- DBN入力を保護場所・読取専用・hash一致・依存wheel hash一致で確認するP2-12-03用事前検査

やさしい説明: 本物の市場データを読むための翻訳機を作り、練習用のデータで「順番、内容、品質の記録が変わったら止まる」ことを確かめた段階です。本物の箱を開く試験はまだしていません。

## 確認結果

| 確認 | 結果 |
|---|---|
| `pytest tests/market_data` | PASS: 90件 |
| coverage | PASS: 81.58%（基準80%） |
| ruff | PASS |
| mypy | PASS |
| ローカル外部接続禁止付きpytest | PASS: 90件 |
| 品質Gate回帰試験 | PASS: 136件 |

## まだ完了していないこと

- 保護されたWSL入力で実DBNを実際に再生すること
- P2-08の「受信UTC時刻」を証跡から確定すること
- DBNの外部銘柄IDを内部Catalogへ一意に結ぶこと

やさしい説明: 翻訳機はできましたが、本物の箱に「いつ届いたか」「何の商品か」の札が足りないかもしれません。札が確認できるまで、Signal生成とPhase 3への引渡しは止めたままです。
