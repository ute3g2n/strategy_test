# P2-11 Trading Securityレビュー再確認

## Findings first

- Critical: なし
- High: 実DBNからNormalizedBar / MarketEventへ変換する本番境界が未実装。Data Gate UNKNOWN、Signal生成停止、Phase 3への引渡し禁止を維持する。
- 追加監査（対応済み）: timezoneなし時刻が警告だけで通らないことを確認。<code>TIMESTAMP_INVALID</code> をfail-closedへ修正し、Signal生成停止の回帰テストをPASSさせた。
- 追加監査（対応済み）: Normalized snapshotの品質異常を伴うbars改ざんをreplay前に再品質検証し、Manifest/Report不整合として拒否すること、排他的保存で上書き競合を防ぐことを確認した。
- Low: なし

条件付き銘柄の本線混入、異常データの警告だけの通過、checksum不一致の昇格を確認しなかった。正規化内容digestと証跡の束縛はP2-11で解消済み。P2-08 Secret・外部取得の証跡はP2-DP-002を参照する。
