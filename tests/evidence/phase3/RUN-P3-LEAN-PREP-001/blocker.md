# RUN-P3-LEAN-PREP-001 — 初回境界の履歴（解消済み）

判定日: 2026-08-10（JST）

## 初回の事実

- 公式QuantConnect/LEAN Docker Hubのtag `17991`を、Linux amd64固定digestで取得した。
- 対象digestは image index `sha256:bc01b22a27262ff1e69bdd7f451234e565463292350626aaa2479bda7a54765d`、Linux amd64 manifest `sha256:9712dfd8c52d05e7292848cf0b365a02f6d603551bc883d423d2ce0877363263`。
- 2026-08-10 08:03:28 JSTから09:03:14 JSTまで、約60分の取得を1回だけ実行した。
- 取得プロセスは終了時まで稼働していたが、`docker images --digests quantconnect/lean`への完成イメージ登録はなく、`docker system df`のImagesも0件だった。
- 途中状態を成果物として保存せず、digest変更、別tag試行、reset、cache削除は行っていない。

## 代替経路の判定

公式固定commit `c6cc3b743ed7b65d5e0b9fa2bfc18b7d3ac2aea0`のDockerfileを確認したが、公式LEAN Foundation imageと大規模なOS/Python依存、および.NET SDKを前提とする。Windows側にも.NET SDKは導入されていない。したがって、今回のP3-08Aの時間境界内で安全に完了できる代替経路ではない。

## その後の解消

ユーザーの「もっと待て」という指示を受け、同じ公式固定digestで取得を継続した。09:46:39 JSTにDockerの完成イメージ登録が完了し、Eドライブへのtar保存、完全hash、公式LICENSE hash、network none / read-only / Local providerのオフライン起動をPASSにした。最終判定は `tests/evidence/phase3/RUN-P3-LEAN-PREP-001/verification.json` と `run-manifest.json` を正本とする。

## 初回時点の安全停止

初回境界ではimage tarとlicenseの完全hash、ローカルentrypoint、offline preflight、trusted scope登録は未完了だった。これらを捏造せず一時停止し、追加待機後に再開した。初回時点ではP3-09、実engine、Broker、Paper、Liveを開始しなかった。

## 再開前に確認した条件

公式固定digestの完成イメージをローカルに登録し、Eドライブへ保存して全hashを記録した。その後、network none / read-only / Local providerのオフライン起動を完了した。trusted scope登録、固定4 Gate、独立レビューは次の準備作業として実施する。
