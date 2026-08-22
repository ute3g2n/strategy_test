# P5R2-DELETE-G1 Human Gate Evidence

- Gate: `P5R2-DELETE-G1`
- Run: `RUN-P5R2-DELETE-G1-PACKET-001`
- Status: `APPROVED_BOUNDED_P5R2_21_FIXTURE_ONLY`
- Packet: [`08_P5R2-DELETE-G1承認packet.html`](../../../../doc/phase5R2/08_DELETE-G1/08_P5R2-DELETE-G1承認packet.html)
- Decision: [`P5R2-DELETE-G1_HumanGate_2026-08-23.md`](../../../../plan/phase5R2/ログ/P5R2-DELETE-G1_HumanGate_2026-08-23.md)
- Authority: [`P5R2-HumanGate権限移譲_2026-08-22.md`](../../../../plan/phase5R2/ログ/P5R2-HumanGate権限移譲_2026-08-22.md)

## 承認範囲

P5R2-21の実装と、新規に作る一時fixtureだけを使う物理削除受入を承認した。対象はterminal ResultArtifactだけであり、logical IDからサーバーが固定root内の対象を解決する。呼出元指定path、traversal、root外、symlink／Windows reparse point、TOCTOU、ID不一致、active／recovery中、CSV Export中、保持選択中は拒否する。

## 保護範囲

Export済みCSV、Historical Data、Catalog、Run本体、Run manifest、Audit、tombstone、Evidence、screenshot、quality receipt、既存の実Data／Run／CSV／Evidenceを削除しない。cascade削除、一括purge、restore API、外部I/O、Secret、費用、P6開始は承認していない。

## Gate時点の実施結果

- packet、P5R2-15 guard／RED／GREEN、P5R2-19 UI境界、権限移譲記録を確認した。
- 外部requestは0。
- Gate中の物理削除は0。
- 指定Agentの独立完了は成立していないため、runtime receiptへfallbackを記録した。
- 安全のため、管理用hash、manifest、fingerprint、stale、retry、receipt hashの経路は作成しない。

P5R2-21では、まず新規一時fixtureの存在と保護対象を確認し、対象ResultArtifactだけを物理削除する。既存Evidenceや通常Dataを削除対象にしない。
