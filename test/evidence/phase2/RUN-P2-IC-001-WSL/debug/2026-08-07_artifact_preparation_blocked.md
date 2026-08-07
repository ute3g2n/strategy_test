# Python 3.12.13 artifact準備の停止記録

## 読み取り結果

- 承認済みartifact保管場所（`C:\approved-artifacts` など）は存在しない。
- WSLの既存venvは Python 3.12.3 である。
- WSLの `wheelhouse/` は空である。
- Windows側には CPython 3.12.13 があるが、Windows実行ファイルであり、WSLのLinux venvには使用できない。
- WSL側にPython 3.12.13のLinux実行ファイルは見つからない。

## 判定

承認済みLinux Python 3.12.13 artifactと、固定版ツールのLinux wheelがないため、venv再作成とオフライン導入を開始していない。外部ネットワーク、apt、通常のpip取得は使用していない。

## 必要な入力

承認元が発行したLinux x86_64 / glibc対応 Python 3.12.13 artifact、SHA-256 manifest、ruff 0.16.1・mypy 2.3.0・pytest 9.1.1・pytest-cov 7.1.0と依存パッケージのLinux wheel一式。
