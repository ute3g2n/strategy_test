# A160 Trading Security Review — P3-08R-02

対象: P3-09準備入口とfire-control

## Findings first

- Critical: 0
- High: 0
- Medium: 0
- Secret検出: 0
- 外部接続経路: 0
- Broker/Paper/Live/Cloud到達経路: 0

## 安全境界

1. `input-contract.json`のP3-09 scopeが`execution_allowed=false`でなければ停止する。
2. 入力はrepository-relativeなfixture pathに限定し、symlink、path traversal、固定path外のcontract/Manifestを拒否する。
3. `network_mode=none`、Local、automatic data download false、Cloud/Broker/Secret NOT_USEDをManifest契約で固定する。
4. engine identityはimage index digestとLinux amd64 digestの両方を要求し、tagだけを受け付けない。
5. `--mode run`は`P3_09_EXECUTION_NOT_IMPLEMENTED_IN_PREPARE_ENTRY`で停止するため、prepare入口から実engineへ暗黙到達しない。

## 判定

P3-08R-02の安全境界は受入可。P3-09実行の許可、実engineのnetwork isolation観測、Core/LEAN parityは後続Stepの証拠が揃うまで未実施とする。
