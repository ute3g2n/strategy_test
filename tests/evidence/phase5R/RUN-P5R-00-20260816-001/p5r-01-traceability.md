# P5R-01 要件・画面・API・Core・Test・Evidence追跡

| AC | 内容 | 現状 | P5R実装対象 | 主な画面/API/Test |
|---|---|---|---|---|
| AC-01 | 入力、型、単位、未来参照、品質の事前検査 | PARTIAL | preflightと入力エラー表示 | SCREEN-08 / `POST /api/backtest/preflight` / P5R-T-01 |
| AC-02 | P5承認範囲のDataだけ許可 | PARTIAL | BTC/ETH、Spot、1m、UTC、期間範囲拒否 | SCREEN-08 / preflight / P5R-T-02 |
| AC-03 | Single RunのQueue、進捗、残り時間、状態 | PARTIAL | 実Run worker、progress、ETA | SCREEN-08/09 / runs API / P5R-T-03 |
| AC-04 | cancel/stop/failure/retry/checkpoint resume | PARTIAL | 状態機械、checkpoint、resume | SCREEN-09 / cancel/resume API / P5R-T-04 |
| AC-05 | 総損益、最大DD、勝率、取引数、最終残高 | NOT_IMPLEMENTED | 実バーから計算し根拠表示 | SCREEN-10 / result API / P5R-T-05 |
| AC-06 | Signal、Trade、仮想Fill、残高、Cost/Slippage | PARTIAL | 行別ledgerとprovenance | SCREEN-11 / rows API / P5R-T-06 |
| AC-07 | Sweep範囲、刻み、上限、重複、件数、負荷 | PARTIAL | 展開前検査と拒否 | SCREEN-08/09 / sweeps API / P5R-T-07 |
| AC-08 | Sweepの行別状態、部分失敗、cancel、resume | NOT_IMPLEMENTED | parent/child worker | SCREEN-09 / sweeps API / P5R-T-08 |
| AC-09 | 履歴、同条件、最新、上書き禁止 | PARTIAL | in-memory/local result storeの分離 | SCREEN-12 / runs API / P5R-T-09 |
| AC-10 | 比較可能性と比較不能理由 | PARTIAL | condition契約と理由表示 | SCREEN-12 / compare API / P5R-T-10 |
| AC-11 | 大量表、非同期CSV、進捗、cancel、失敗 | PARTIAL | CSV Jobと相対保存 | SCREEN-12 / csv-jobs API / P5R-T-11 |
| AC-12 | train/validation/holdoutの役割と再利用禁止 | PARTIAL | holdout gateと履歴 | SCREEN-13 / holdout API / P5R-T-12 |
| AC-13 | 窓ごとの実Walk-forward、未来参照拒否 | NOT_IMPLEMENTED | 3固定窓の実行と集計 | SCREEN-13 / walk-forward API / P5R-T-13 |
| AC-14 | 固定ダミーではなく実Application API結果 | NOT_IMPLEMENTED | Python HTTP API + React接続 | SCREEN-08〜13 / API integration / P5R-T-14 |
| AC-15 | PC/mobile、role、label、keyboard、focus | PARTIAL | real UIのアクセシビリティ | 全P5R画面 / Playwright + axe / P5R-T-15 |
| AC-16 | AC、Evidence、Unknown、対象外、P6引渡し | PARTIAL | 手順書、完了表、P6 handoff | manual / completion / P5R-T-16 |

## P5Rで固定する対象外

P6の複数Unit/Portfolio/Account/Risk/OMS、P7以降のForward/Shadow/Paper/Live候補/小規模Live/通常Live、Broker、Secret、外部Data、Cloud、実注文、実資金はP5Rの実装・Evidence・UI撮影対象外である。

## Unknown

`P5R-UNK-001`はOPEN_NOT_PASS。Provider条件、P5-08 host isolation、P5時点のchild Agent未起動、execution cost実測不足は、P5Rのローカルfixture-only実装を越えて解決しない。
