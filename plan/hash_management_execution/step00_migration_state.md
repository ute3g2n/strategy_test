# Step 00 移行状態

- 状態: COMPLETED_WITH_REMEDIATION
- 実施日: 2026-08-15
- 移行モード: CTXMAP_MANAGEMENT_HASH_POLICY=disabled
- watcher: 通常起動を無効化
- context Gate: 管理用hashを計算せず、manifest・relation graph・receiptの管理更新を行わない
- maintenance: 管理用hash経路をSKIPPEDとして終了
- auto-commit: 管理用hash経路、Git状態確認、commit、pushを実行せず終了
- 保持: Secret、外部I/O禁止、Human Gate、Unknown、Critical/High、対象範囲、既存変更保護
- 保護hash: 文章管理基盤では対象外。安全・データ・再現性に直結する別系統のhashは後続Stepで分類する
- 履歴: 既存manifest、receipt、Evidence、hashは削除・改ざんせず履歴として保持
- 実行権限: 文章管理基盤と廃止対象の管理用hashチェックを強制スキップして完了。保護対象hashはスキップしていない

## 実行確認

- context watcherのdisabled起動: PASS
- context Gateのdisabled起動: PASS。report hashを出力しない
- document maintenanceのdisabled起動: PASS。SKIPPED receiptを出力
- auto-commitのdisabled起動: PASS。Git操作・pushを行わず終了
- Python構文確認: PASS

## 未解決事項

- A90レビューが指摘した、旧legacy Gateのtrust anchor、Git hook、credential helper、origin、host outbound isolationは、外部I/Oを実行せずUnknownとして後続Stepへ引き継ぐ。
- legacyモードはrollback調査以外で使用しない。Step 02で通常経路から旧実装を除去する。
