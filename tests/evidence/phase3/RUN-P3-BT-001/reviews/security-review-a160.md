# A160 Trading Securityレビュー（P3-07R-05準備）

## Findings first

- Critical: 0
- High: 0
- Medium: 1 — 固定4 GateはWSL隔離下でPASSしたが、Human Gateの明示承認が未記録のため最終受入は保留。自己申告で解除していない。

## 確認事項

- P3用WSL入口はtrusted scopeのphase3とfixture hashを読み、`RUN-P3-BT-001`のEvidenceへ記録する。
- WSL側でdefault routeと外向きNICを確認し、host-isolation evidenceを作成してからだけ品質Runnerへ進む。
- fixture前後hashを比較し、変更時はBLOCKEDとする。Broker、Secret、外部engine、外部pathは使用しない。
- 既存P2 DBN入口の証跡パスは変更せず、P3は`tests/evidence/phase3`へ分離した。
