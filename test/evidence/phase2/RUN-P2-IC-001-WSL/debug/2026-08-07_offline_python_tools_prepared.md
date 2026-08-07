# 2026-08-07 オフライン実行環境の準備結果

## 結果

WSL専用の `.venv` を Python 3.12.13 で作り直し、隔離開始前にユーザーが許可した公開Web取得で用意した wheel だけから固定ツールを導入した。隔離開始後の `pip install` は行っていない。社内の承認済みartifact保管場所は存在しなかったため、その事実を `offline-preparation.json` に明記した。

## 確認した固定バージョン

- Python 3.12.13
- ruff 0.16.1
- mypy 2.3.0
- pytest 9.1.1
- pytest-cov 7.1.0
- `pip check`: `No broken requirements found`

## 証拠

- `offline-preparation.json`
- `wheelhouse/`（WSL clone内、Git追跡外）
- `.venv/bin/python`（Python 3.12.13で作成）

依存の取得は隔離前の準備段階にだけ行った。実行時はネットワークなしのWSL2で固定コマンドを使った。
