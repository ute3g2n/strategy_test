# Windows Codex引継ぎプロンプト

以下を、`C:\project\strategy_test` で起動したWindows側Codexへそのまま渡す。

```text
あなたはWindows側の引継ぎ担当です。現在地は C:\project\strategy_test です。
Linux側で実装されたWSL隔離品質ゲートを引き継ぎ、実機実行前の欠陥を直し、証跡を正しく収集できる状態へしてください。

最初に必ず次を読むこと。
1. AGENTS.md
2. plan/phase2-5_ai_foundation/06_WSL2隔離品質ゲート_Windows引継ぎコンテキスト.md
3. README.md
4. plan/phase2-5_ai_foundation/05_WSL2隔離品質ゲート構築_CodexCLI依頼プロンプト.md
5. scripts/wsl_quality_gate/run_test.ps1
6. scripts/wsl_quality_gate/run_isolated_p2.ps1
7. scripts/wsl_quality_gate/run_isolated_p2.sh
8. tests/quality_gate/test_wsl_quality_gate_contract.py

最優先の問題
----------------
Windows cloneの C:\project\strategy_test と、WSL cloneの /home/oue/strategy_test は別の作業ツリーです。
現在の run_test.ps1 は通常実行時にWindows cloneの既存 verification.json を先に読む可能性があります。
そのため、WSL runnerが今回生成した verification.json ではなく、Windows cloneに残った古いDRY_RUN証跡をautomationログへ保存する危険があります。

実機4 Gateの前に、この証跡取り違えを修正してください。
次のいずれかを選び、既存の設計に最も小さく整合する形で実装してください。
- 今回のrun開始時刻より新しいWSL側証跡だけを読む。
- wrapper execution IDと一致するWSL側証跡だけを読む。
- automation証跡の配置・取得をWSL側へ統一する。

古いWindows側 verification.json と、新しいWSL側 verification.json が共存しても、新しいWSL側を選ぶ回帰テストを追加してください。

制約
----
- RUN-P2-IC-001-WSL、P2-D07、REQ-Q02/19/20/23、target_only、固定fixture checksum、固定4 commandを変更しない。
- 通常WSL NAT、外部ネットワーク、Databento、Broker、Secret、実データ、実取引、隔離後のpip installを使わない。
- Human Gateを自己承認しない。
- run_isolated_p2.ps1 はWSL内から実行してはならない。
- -AllowRunningDistro は、UNC経由でスクリプトを読むために対象distroだけが起動した場合に限る。対象WSL内のCodex、VS Code Remote、端末が動いている状態では使わない。
- ユーザーの明示許可なしに、.wslconfigを書き換える実機隔離runを開始しない。まず静的・DryRun検証を行う。

実施順序
----------
1. git status と git log -1 を確認し、origin/mainを fast-forwardでpullする。
2. Windows cloneとWSL cloneのHEADが一致することを読み取り確認する。
3. P0の証跡取り違えを修正し、回帰テストを追加する。
4. PowerShell parserで run_test.ps1 と run_isolated_p2.ps1 の構文を確認する。
5. Python契約テスト、Bash構文、git diff --checkを実行する。
6. 結果・未解決事項・実機run可否を日本語で報告する。

実機隔離runを行う許可が後で得られた場合だけ、Windows native PowerShellから次を使う。

powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\wsl_quality_gate\run_test.ps1 -Distro Ubuntu-24.04 -RepositoryPath /home/oue/strategy_test -RunId RUN-P2-IC-001-WSL

Windowsローカルcloneから起動する場合は、通常 -AllowRunningDistro を付けない。UNC上のスクリプトとして実行し、対象distroがファイル読み取りだけで起動した場合だけ、対象WSL内の処理が停止済みであることを確認したうえで -AllowRunningDistro を付ける。

実機run後は、次を確認する。
- Windows側automationログとWSL側verification.jsonが今回の同一実行を示していること。
- host-isolation.json、verification.json、restore.jsonのstateとexecution IDを確認すること。
- formatter、lint、type、testの4 Gateすべての結果を確認すること。
- 成功してもBLK-RUN-003とHuman Gateを勝手に解決済みにしないこと。
```
