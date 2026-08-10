# P3-08A LEAN公式一次情報調査

確認日: 2026-08-10（Asia/Tokyo）
Phase: Phase 3 / Step P3-08A

## 採用候補

- 公式Docker repository: https://hub.docker.com/r/quantconnect/lean
- 公式tag: `17991`
- Docker Hub tag API: https://hub.docker.com/v2/repositories/quantconnect/lean/tags/17991
- multi-arch image index digest: `sha256:bc01b22a27262ff1e69bdd7f451234e565463292350626aaa2479bda7a54765d`
- Linux amd64 platform digest: `sha256:9712dfd8c52d05e7292848cf0b365a02f6d603551bc883d423d2ce0877363263`
- 公式LEAN source: https://github.com/QuantConnect/Lean
- tag `17991` source commit: `c6cc3b743ed7b65d5e0b9fa2bfc18b7d3ac2aea0`
- 公式LICENSE: https://raw.githubusercontent.com/QuantConnect/Lean/master/LICENSE
- ライセンス: Apache License 2.0
- 公式local backtest / Docker実行説明: https://www.quantconnect.com/docs/v2/lean-cli/backtesting/deployment

## 採用ルール

- 可変tagだけでは実行せず、image index digestとlinux/amd64 digestを併記する。
- 取得物は `E:\strategy_test_data\phase3\engine_poc\lean\` に保存し、GitにはManifest・hash・ライセンス要約だけを保存する。
- `--network none`、Local data provider、Cloud/Broker/Secret/自動データ取得なしでpreflightする。
- 公式source、Docker Hub、公式QuantConnectドキュメント以外を依存取得元にしない。

## 未確認事項

- Docker image tarの保存hash、Docker image ID、実行時のEntryPointは、image pull完了後に確定する。
- P3-09のStrategy適合、Backtest結果、性能、実取引所CalendarはP3-08Aの対象外で、未実施のまま残す。
