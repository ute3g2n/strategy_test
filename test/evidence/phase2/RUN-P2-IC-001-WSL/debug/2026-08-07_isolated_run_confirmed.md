# 2026-08-07 隔離実機runの確認結果

## 結果

`RUN-P2-IC-001-WSL` をWindows native PowerShellから実行した。Windows側の古い `verification.json` ではなく、今回のWSL実行IDと一致するcaptureだけを選択した。

## 確認事項

- `host-isolation.json`: `state=CONFIRMED`, `networking_mode=none`
- `restore.json`: `state=RESTORED`
- formatter / lint / type / pytest: すべて `PASS`, exit code `0`
- fixture SHA-256: `sha256:94022229698e972353b8ec9537f455af5cb29d47253f5f2a1ed5d33b08b50169`
- target-only change SHA-256: `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

## 残件

Runの最終状態は `HUMAN_GATE_REQUIRED`。作業Agentによる自己承認は行わず、権限者の署名付き承認JSONが必要である。したがって、今回解消したのは隔離実行条件（BLK-RUN-003）だけであり、Run全体のPassやHuman Gate承認済みとは扱わない。
