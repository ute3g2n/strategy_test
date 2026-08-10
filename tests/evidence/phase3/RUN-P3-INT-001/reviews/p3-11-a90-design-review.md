# P3-11 A90 設計・追跡レビュー

- reviewer: `AutoTrade_A90_DesignReviewer_v0_1`
- step: `P3-11`
- scope: P3-D01〜P3-D10、P3-AC-01〜08、総合台帳、P3-10 Run証跡
- verdict: `RETURN_FOR_H3-3`
- critical: 0
- high: 2
- medium: 2

## Findings first

1. `P3-IR-001` / High: Calendar 6ケースのうち実装動作の証拠がnormal/DSTの3ケースに限られ、holiday/short_day/daily_haltはfixture存在確認に留まる。`BacktestRunner`と`CalendarPort`の責務接続も確認できない。
2. `P3-IR-002` / High: RUN-P3-BIAS-001のcanonical PASSとcapture/automation/host状態が一致しない。P3-10 source auditがcanonical verificationだけを参照する。
3. `P3-IR-003` / Medium: M30直接集約が欠落したsource IDを合成IDで補完し、入力provenanceを単体で束縛しない。
4. `P3-IR-004` / Medium: P3-10のreview JSONが実質的な独立分析ではなく、対象ファイル存在とsource audit状態からAPPROVEを生成する。

## 確認

- P3-AC-03は独立監査上BLOCKED、P3-AC-01/04はCONDITIONAL。
- Unknown `UNK-P3-01/05/07`は解消扱いにしていない。
- H3-3承認なしにP3-12へ進めない。

証拠: [P3-D11](../../../../../doc/phase3/09_統合レビュー/10_Phase3統合レビュー結果.html)、[P3-D12](../../../../../doc/phase3/09_統合レビュー/11_Phase3レッドチーム監査結果.html)。
