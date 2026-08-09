# RUN-P3-BT-REPAIR-001 RED結果

## 判定

P3-07R-01の実装前RED固定は完了した。新規敵対テストは34件を収集し、33件が失敗、独立oracleの1件だけが成功した。

- 終了コード: `1`
- skip: `0`
- xfail: `0`
- fixture変更: なし
- 外部engine / Broker / Secret / 外部通信: 実施なし

## 失敗の意味

失敗は、DTOがまだ存在しないこと、`BacktestRunner.run`がないこと、現行stubがManifest・Replay・Snapshot・Engine・Offline・Performanceの入力フラグだけでPASSを返せることを示す。これは期待されたREDであり、P3-07の受入可やP3-ACのGREENを意味しない。

## 独立oracle

`test_parent_manifest_matches_independent_child_oracle`だけはPASSした。親Manifestから期待hashを再利用せず、テストコードに固定した10子のpath/hashと実bytesを比較した。全10件が一致したため、REDを作るためにfixtureを壊していない。

## 中学生でも分かる説明

新しい安全確認の問題を先に出しました。今のBacktestは、問題を本当に解く箱がまだないので33問で止まりました。問題の答えを変えたり、最初から合格にしたりはしていません。材料の指紋を確かめる1問だけは通ったため、材料をすり替えていないことは確認できています。
