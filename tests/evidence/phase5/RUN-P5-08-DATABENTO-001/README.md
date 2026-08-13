# RUN-P5-08-DATABENTO-001

P5-DATA-G1の承認範囲に従うP5-08専用Evidence rootの雛形です。

## 現在状態

- 状態: `RUNNER_CREATED_NOT_EXECUTED`
- 外部I/O: `false`
- Secret値アクセス: `false`
- 実Data取得: `false`
- 費用見積り必須: `false`（2026-08-13のユーザー指示で廃止）
- 費用上限: 1 Run 25 USD、チーム月額50 USD
- 実行後usage監査: 必須
- host isolation: `UNKNOWN`
- entitlement／budget control: `UNKNOWN`

## 実行前に埋めるファイル

1. `entitlement-confirmation.json` の`status`をアカウント確認後に`CONFIRMED`へ更新する。
2. `budget-control.json`へProvider／チーム側のbudget control設定証跡を入れ、`status`を`CONFIRMED`へ更新する。
3. `secret-metadata.json`へSecretの監査参照だけを入れる。Secret値は入れない。
4. `host-isolation-policy.json`と`host-isolation-audit.template.json`に外部Run専用の事前・事後監査結果を反映し、`verification_status`を`VERIFIED`へ更新する。
5. `request.json`と承認Evidenceの範囲が一致することを再確認する。

## コマンド

外部I/Oなしの検証:

```powershell
powershell.exe -NoProfile -File scripts/phase5_external_data/run_databento_historical.ps1 -Request tests/evidence/phase5/RUN-P5-08-DATABENTO-001/request.json -RunId RUN-P5-08-DATABENTO-001 -EvidenceRoot tests/evidence/phase5/RUN-P5-08-DATABENTO-001 -MaxCostUsd 25 -NoLive
```

実行モードは`-Execute`を明示しない限り起動しません。現在は`entitlement-confirmation.json`、`budget-control.json`、`host-isolation-policy.json`が未確認のため、実行モードへ進めません。

## 禁止事項

- API keyをCLI、JSON、HTML、ログへ書かない。
- `src/`、P4 Evidence、P5-06 local Evidence、Core、DB、Broker、Cloudへ書かない。
- `hist.databento.com:443`以外へ接続しない。
- P4 synthetic／P5-06 local結果を実市場Evidenceへ一般化しない。
- scope、期間、schema、費用上限を変更しない。変更時はP5-DATA-G1を再承認する。
