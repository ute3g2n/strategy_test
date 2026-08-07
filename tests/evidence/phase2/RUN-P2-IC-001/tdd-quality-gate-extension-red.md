# P2-D07 Quality Gate 拡張 TDD 証跡（RED）

対象: `RUN-P2-IC-001` / `P2-D07`  
指定Orchestrator: `AutoTradeComponentLifecycle_Orchestrator_v0_1`、`AutoTradeProject_ImplementationQuality_Orchestrator_v0_1`

## 実行

```text
.venv/Scripts/python.exe -m pytest tests/quality_gate/test_runner.py -q
```

## 結果

- 終了状態: `RED`
- 収集時エラー: `ImportError: cannot import name 'local_p2_pytest' from scripts.quality_gate`
- 原因: P2-D07用の固定pytest wrapper、trusted scope registry、P2 Manifest検証、host outbound isolation判定をまだ実装していない。
- 外部ネットワーク、Databento、Broker、Secret、実データへの接続: なし。

この失敗を確認してから、最小実装へ進む。REDテストは削除・skip・弱体化しない。

## GREEN 再検証

実装後に同じテストを再実行した。

```text
.venv/Scripts/python.exe -m pytest tests/quality_gate/test_runner.py -q
30 passed

.venv/Scripts/python.exe -m pytest tests -q
42 passed

.venv/Scripts/python.exe -m pytest tests/quality_gate -q
33 passed

.venv/Scripts/python.exe -m scripts.quality_gate.local_p2_pytest
9 passed
```

P2用テストは GREEN になった。ただし、実Run Manifest は既存の未解決 `change_hash` のため、実行結果をPassへ変更していない。
