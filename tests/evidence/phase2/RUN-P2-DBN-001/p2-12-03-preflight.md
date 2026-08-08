# P2-12-03 実DBN Replay・WSL隔離品質Gate 事前確認

- 確認日時（UTC）: 2026-08-08T17:59:33Z
- Run: `RUN-P2-DBN-001`
- 結果: **BLOCKED**
- 停止理由: `PROTECTED_DBN_INPUT_MISSING`

WSLの保護場所 `/var/lib/autotrade/replay/RUN-P2-DBN-001/input.dbn` を読取専用で確認したところ、ファイルは存在しなかった。期待する内容確認値は `sha256:8fd0286a477e073c83e8306c4e1a8ebec3af693141010563edd7e0ec1990b65e` であるが、ファイルが無いため照合できない。

やさしい説明: 本物のデータ箱が、決めた鍵付きの場所に置かれていません。箱が無いのに別の場所を探したり、以前の結果で「大丈夫」と言ったりしないため、試験を止めました。

このため、実DBN変換、Replay比較、WSL固定4 Gate、Data GateのPASS判定は実行していない。Data GateはUNKNOWN、Signal生成とPhase 3への引渡しは禁止のままである。

実行していないこと: 追加取得、外部接続、Secret投入、Broker接続、AIによるDBNコピー、Windows側の実行結果による代用。
