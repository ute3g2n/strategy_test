# P6引渡し

## P5Rから渡す入力

- P5RのBacktest Run / Sweep / 履歴 / CSV / Holdout / Walk-forwardの結果は、実運用UnitやPortfolioの残高・注文へ自動昇格しない。
- P5R-UNK-001はOPEN_NOT_PASSのまま。Provider、host isolation、過去child dispatch、execution costの未解決をP6の合格条件へ混ぜない。
- P5Rで確定した「外部request 0件、Broker / Secret / 実注文なし」の境界を維持する。
- P5RのRun ID・条件・結果・停止理由・Evidenceを、P6の固定Simulation設計の入力として参照する。

## P6で新たに完成させるもの

P6では、複数の継続運用Unit、Portfolio、Account、Risk、OMS、競合防止、Kill、照合、復旧を固定Simulationで作る。P5RのSweep子Runを運用Unitとして流用せず、責務と識別子を分ける。外部Order、実Account変更、実資金はP6にも持ち込まない。

## 後続の能力順

P6の後は、Forward Test（実時間・仮想）、Shadow（本番候補の複製・注文なし）、Paper（仮想口座・仮想Ledger）、Live候補、小規模Live、通常Liveの順に、各段階を別Gateで完成させる。P5R-H2はこの順序を確認しただけで、後続Phaseの実装・実行を開始していない。
