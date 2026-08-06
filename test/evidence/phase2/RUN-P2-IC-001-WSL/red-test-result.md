# RED記録

実装前に `tests/quality_gate/test_wsl_quality_gate_contract.py` を追加した。

実行コマンド: `pytest -q tests/quality_gate/test_wsl_quality_gate_contract.py`

結果: RED実行環境に `pytest` がなく、`pytest: command not found` で終了コード127。これはテスト失敗ではなく、承認済みLinux wheelhouseとWSL用venvが未準備であるための環境BLOCKEDである。4 Gateは開始していない。
