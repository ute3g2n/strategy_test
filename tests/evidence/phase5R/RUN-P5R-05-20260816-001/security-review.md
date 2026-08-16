# P5R local API Security Review

- Review ID: `P5R-SEC-01`
- 対象: `src/autotrade/application/http_server.py`, `src/autotrade/application/backtest_product.py`, `ui/mock/src/backtestApi.ts`, `ui/mock/src/P5RBacktestScreen.tsx`
- 判定: `PASS_WITH_EXPLICIT_LOCAL_ONLY_BOUNDARY`
- Critical / High: 0

## 確認したこと

- HTTPサーバーは `127.0.0.1` または `localhost` 以外へのbindを拒否する。
- CORSは `http://127.0.0.1:4173` に固定し、Cache-Control `no-store` と `X-Content-Type-Options: nosniff` を付ける。
- JSON bodyは1 MBを上限とし、壊れたJSON・巨大body・オブジェクト以外を拒否する。
- OSError / RuntimeErrorの内部文字列をHTTP応答へ出さず、`LOCAL_API_FAILURE`へ置き換える。
- 銘柄、単位、期間、相対fixture pathを許可リストと範囲検査で制限する。
- UIはReactの通常レンダリングで値を表示し、HTML文字列として結果を解釈しない。
- Secret、API key、Broker SDK、外部URL、実注文、実資金、DB外部接続、SQL実行は追加していない。
- `tests/phase5R/test_http_server_security.py` で非ループバックbind拒否とbody/origin制限定数を確認し、P5Rテスト全体179件がPASSした。

## 残る境界

これはP5R専用のローカル試験サーバーであり、認証、CSRF対策、TLS、レート制限、公開ネットワーク運用は提供しない。将来このAPIをループバック外へ出す場合は、現在の実装をそのまま再利用せず、別PhaseのSecurity/Human Gateで設計・実装・再検証する。
