# RUN-P2-DBN-001 P2-12-01 RED結果

- 実行日: 2026-08-08
- 実行場所: Windows側の作業ツリー
- 実行コマンド: `.venv\\Scripts\\python.exe -m pytest -q tests/market_data/test_p2_12_dbn_replay_contract.py`
- 外部接続: なし
- Secret: 使用・出力ともになし
- WSL: 使用しない。実DBNのコピー、依存導入、隔離実行は行わない。
- 実DBN: 開かない。P2-08証跡に記録済みのSHA-256 `8fd0286a477e073c83e8306c4e1a8ebec3af693141010563edd7e0ec1990b65e`だけを設計の入力識別子として固定した。

## 結果

| 区分 | 件数 | 状態 | 意味 |
|---|---:|---|---|
| 実DBN入力識別子の固定 | 1 | GREEN | P2-08の記録済みSHA-256を設計の識別子として固定した。実物を開いた意味ではない。 |
| 実装前契約 | 23 | RED | `dbn_contracts`、Decoder Adapter、Normalizer、MarketEvent Factory、DBN用Manifest入力、既存WSL入口への事前検査登録が未実装のため、意図どおり停止した。 |

pytestの要約は **23 failed, 1 passed** である。21件は全て `ModuleNotFoundError: autotrade.market_data.dbn_contracts`、Adapter境界の1件は予定モジュールが未作成のため `FileNotFoundError`、WSL事前検査の1件は既存入口へ<code>RUN-P2-DBN-001</code>が未登録のため失敗した。これはP2-12-01の設計先行状態を固定する期待どおりのREDであり、Data GateのPassや実DBN Replayの成功を意味しない。テスト中にGit管理外DBNを開いていない。

## REDとして固定した停止条件

1. payload SHA-256が違う場合は、Decoderを始めず `RAW_CHECKSUM_MISMATCH` で止める。
2. Raw受信UTC時刻が無い場合は、現在時刻やイベント時刻で補わず `RAW_RECEIVED_AT_MISSING` で止める。
3. DBNの外部銘柄を内部Catalogへ一意に対応付けられない場合は、推測せず `CATALOG_MAPPING_UNRESOLVED` で止める。
4. 品質が公開不可なら、MarketEventを作らず `QUALITY_REJECTED` で止める。
5. Coreの公開契約にVendor SDK型、APIキー、認証情報、SDK例外を含めない。
6. 壊れたheader、未対応schema/record、時刻・価格・出来高・順序不正を通常行にしない。
7. decoderの版・成果物hash・取得条件のどれかが変われば、別の<code>data_version</code>にする。
8. Adapter以外のモジュールがVendor SDK、通信、環境変数を読み込まない。

やさしい説明: まだ翻訳機を作っていないので、今は「読めたこと」にして先へ進めません。作った後も、箱が違う・いつ届いたか分からない・何の商品か決められない、のどれかなら売買の判断には使いません。

## 次の作業と人による承認

P2-12-02は、このREDをGREENにする最小実装である。ただし実DBNを読む依存の導入、WSLの保護場所への人による配置、隔離ReplayはH2-5の承認後だけに行う。既存証跡から受信UTC時刻またはCatalog対応を復元できず、新規の最小取得が必要になる場合は、H2-2を改めて承認してから行う。

## 設計レビュー

`AutoTrade_A91_ImplementationDetailReviewer_v0_1` は、実DBNをH2-5前に開かないこと、source mode別のManifest、Catalog Binding、既存WSL入口の利用を再確認し、**Critical 0 / High 0** でP2-12-01の設計+REDを受入可と判定した。P2-12-02では、取得条件・Catalog・規則・コード版の差分と、順序付きMarketEvent列を比較するGREEN試験を追加する。
