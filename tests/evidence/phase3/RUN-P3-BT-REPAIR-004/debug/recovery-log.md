# P3-07R-04 Debug / Recovery Log

## 仮説と修正回数

| 仮説 | 最小修正 | 回数 | 再検証 |
|---|---|---:|---|
| EngineFailureとtyped identityが不足している | frozen DTO、全field検証、Fake parity比較を追加 | 1 | R-04契約テストGREEN |
| offline evidenceがcaller boolだけでPASSし得る | 実ファイルhash、root/reparse、AST、Secret/URL走査、socket guardを追加 | 1 | Offline hostile cases GREEN |
| 性能証跡がsha256形だけを受け入れる | 決定的generator、実測monotonic/RSS、二回result hash、observed flagを追加 | 1 | Performance hostile cases GREEN |
| 固定Gate wrapperがtrusted runnerに登録されていない | R-04 scopeとlocal_p3_r04_pytestを登録 | 1 | dry-run GREEN |

## 停止した環境条件

登録済み品質Gateを実行した結果、host outbound isolation markerが無いため、runnerは固定Gate subprocessを開始せずBLOCKEDにした。これはネットワークを自己申告で許可したものではなく、直接pytestの結果を最終Gateへ昇格させないための停止である。

再開条件は、同じRun Manifest、同じchange hash、同じfixture hashを、trusted host outbound isolationが確認できる環境から実行すること。P3-09の正式性能閾値はこのRunでは判定しない。
