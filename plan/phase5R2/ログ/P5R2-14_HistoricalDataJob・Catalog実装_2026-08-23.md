# P5R2-14 Historical Data Job・Catalog・local generation 実装ログ

## 判定

`P5R2-14_GREEN_CONFIRMED`。P5R2-15へ移行する。

## 実装範囲

- `HistoricalDownloadJob`はDATA-G1前に外部I/Oを行わず、明示的に拒否する。
- `TimeframeGenerationJob`は15m／30m／1h／4h／1dを対象に、1m local source、指定UTC期間、source identity、coverage、quality、provenanceを検証する。結果はCatalog検証前の`STAGED`／`usable=false`とし、partial／recovery／orphanを昇格させない。
- Job返却値はserver-owned registryのdeep copy。operation token、owner、revisionを使い、Snapshot改変、古いrevision、二重遷移、別Job参照を拒否する。
- Catalogは`stage_local_dataset`でJob registryのowner／token／revision、source_job_id、symbol、LOCAL_FAKE境界、OHLCVを再検証する。staging token、preview token、最終Dataset、request、影響Run／Result、replace、revisionを束縛する。
- 同一timestamp同値はdedupe、値競合は明示replaceがない限り停止、非重複期間はpreview確認後にmergeする。過去Runの結果が変わり得ることを理由にmergeを拒否しない。
- Datasetの旧版はexclusive version保存、Resultの初回公開はowner付きO_EXCL、同一payloadだけ冪等とした。ownerなし成功Resultは復旧要求に倒す。

## 検証

Windowsローカルでformatter／lint／mypy、対象テスト52件、対象回帰33件をPASS。固定WSL入口 `RUN-P5R2-14-LOCAL-001` はhost outbound isolation（networking mode none）を確認し、4 GateすべてPASSした。Evidenceは同Runの`verification.json`、`automation/run-test-summary.json`、`host-isolation.json`、`P5R2-14_GREEN.json`、`P5R2-14_A95_policy.json`に保存した。

追加read-only監査はCritical／Highなし。指定Project Coordinator／Agent rosterの独立dispatchは成立していないため、実行済みとは扱わずruntime receiptへ明記した。

## 境界と引継ぎ

外部Provider、login、契約、API call、Data download、Secret、費用、実Data／Run／Evidence／監査／CSVの実削除、Playwright、npm、P6開始は行っていない。プロセス再起動をまたぐJob registry永続化、migration、統合recoveryはP5R2-16へ引き継ぐ。P5R2-15ではRun取消とResult Artifact削除guardを扱うが、DELETE-G1前の実unlinkは行わない。
