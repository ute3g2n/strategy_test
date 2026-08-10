# P3-08A RED/GREEN record

初回RED: Manifest未作成時に`tests/engine_prep/test_lean_prep_contract.py`が2件のFileNotFoundErrorとなった。

GREEN: 公式固定digest、image tar hash、LICENSE hash、preflight条件をManifestへ反映し、契約テスト2件、固定4 Gate対象267件がPASSした。

重要な失敗: read-only rootだけで起動した初回preflightは、LEANの既定`./storage`と`log.txt`への書込みで失敗した。設定を改訂し、`ConsoleLogHandler`、`object-store-root=/tmp/storage`、`results-destination-folder=/results`を固定したnetwork none/read-only preflightでexit code 0を確認した。失敗を隠さず、最終コマンドと出力を正本Manifestへ記録した。
