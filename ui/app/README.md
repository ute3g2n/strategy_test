# AutoTrade UI

AutoTradeの現行Web UIです。Vite、React、TypeScriptで動作し、ローカルのApplication APIへ接続してBacktest条件、ヒストリカルData Catalog、Run状態、結果表示を確認します。

## 起動

リポジトリルートから次を実行します。

```powershell
npm --prefix ui/app ci
npm --prefix ui/app run dev
```

APIを含む一括起動は、リポジトリルートの`start_autotrade.bat`を使用します。停止は`stop_autotrade.bat`です。

## 品質確認

```powershell
npm --prefix ui/app run lint
npm --prefix ui/app run test
npm --prefix ui/app run build
```

ブラウザ確認は、`ui/app`をカレントディレクトリにしてPlaywrightの各設定を実行します。外部Provider接続や外部Data取得はこのUIの通常確認には含めません。
