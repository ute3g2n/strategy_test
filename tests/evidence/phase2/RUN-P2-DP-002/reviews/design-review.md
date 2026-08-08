# P2-08承認後設計レビュー

## Findings first

- Critical: なし
- High: なし
- Medium: 実取得はユーザー承認済みの固定1分・1symbolに限定。定期取得・大容量取得・Raw Store変換はP2-09以降へ分離。
- Low: DBNの正規化とMarketEvent変換は未実施で、P2-09のReplay検証へ引き渡す。

## 確認

`ExternalGateway`はDatabento依存をAdapter内へ閉じ、endpointを公式hostへallowlistした。API keyはAuthorization headerを組み立てるためだけに使用し、metadataへ漏らさない。HTTP error、payload上限、endpoint不許可はfail-closedで停止する。
