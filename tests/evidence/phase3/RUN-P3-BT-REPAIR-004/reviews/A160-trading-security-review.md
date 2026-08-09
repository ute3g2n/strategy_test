# A160 Trading Securityレビュー

## Findings first

- Critical: 0
- High: 0
- Medium: 1 — host outbound isolationは未確認のため、品質Gateはfail-closedでBLOCKED。再開条件を偽造せず記録した。

## 確認事項

- Offline collectorは許可root配下の実ファイルだけをhashし、UNC、外部root、traversal、symlink/reparseを拒否する。
- ASTで禁止依存を走査し、Secret key/valueとBroker/Cloud URLを検出した場合は`OFFLINE_POLICY_VIOLATION`で停止する。
- socket guardを実際に有効化した観測値が無いとoffline evidenceはPASSにならない。callerの`False`だけではPASSにならない。
- Engine SDK、Broker、Secret、外部ネットワーク、実DBNは使用していない。
- 外部engine identityのdigestは作成していない。
