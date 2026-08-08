# P2-08 H2-2承認後の最小取得結果

実行日: 2026-08-08  
Run ID: `RUN-P2-DP-002`  
承認: `human-gate-user-declaration.md`

## 固定した取得範囲

- dataset: `GLBX.MDP3`
- schema: `ohlcv-1m`
- symbol: `MCL.FUT`
- UTC期間: `2026-06-15T12:00:00+00:00` から `2026-06-15T12:01:00+00:00`
- endpoint: `https://hist.databento.com/v0/timeseries.get_range`
- encoding: DBN
- 取得回数: 1

## 結果

- HTTP status: `200`
- payload: `22,760 bytes`
- DBN magic/headerを確認
- payload SHA256: `sha256:8fd0286a477e073c83e8306c4e1a8ebec3af693141010563edd7e0ec1990b65e`
- metadata/request planへAPI key、Authorization、Secret値は出力していない。
- Raw DBNはGitへ登録せず、ローカル `raw/` 配下を `.gitignore` で除外した。checksumと取得条件を本証跡へ固定した。

## 制限

これはH2-2で承認された最小取得の接続確認であり、Raw / Normalized Storeへの変換、複数日取得、費用最適化、定期実行、Strategy評価はP2-09以降の対象である。HTTP 401/403/206/404/429、payload上限超過、通信失敗はfail-closedで停止する。
