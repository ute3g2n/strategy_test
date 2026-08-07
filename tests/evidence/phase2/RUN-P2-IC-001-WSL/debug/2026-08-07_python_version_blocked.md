# Python 固定版不一致による BLOCKED 記録

## 実行結果

RUN-P2-IC-001-WSL は、execution IDをWSLへ渡した後、固定Gate開始前に `Python version mismatch` で停止した。

## 確認値

| 項目 | 実際の値 | 必要な値 | 判定 |
|---|---:|---:|---|
| Python | 3.12.3 | 3.12.13 | 不一致 |
| ruff | 0.16.1 | 0.16.1 | 一致 |
| mypy | 2.3.0 | 2.3.0 | 一致 |
| pytest | 9.1.1 | 9.1.1 | 一致 |
| pytest-cov | 7.1.0 | 7.1.0 | 一致 |

## 停止理由

固定版を満たさないPythonで4 Gateを開始すると、実行結果の再現性が失われるため、formatter、lint、type、pytestは開始していない。BLK-RUN-003の解消証拠にはしない。

## 次の安全な対応

承認済み・事前取得済みのPython 3.12.13 artifactを隔離前にWSLへ配置し、Linux venvを作り直す。隔離後のpip install、外部ネットワークからの取得、runnerの期待版の無断変更は禁止する。
