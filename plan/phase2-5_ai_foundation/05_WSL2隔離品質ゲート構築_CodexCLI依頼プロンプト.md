# WSL2隔離品質ゲート構築: Codex CLI依頼プロンプト

次の本文を、WSL2上で起動したCodex CLIへそのまま渡す。

```text
あなたは AutoTradeProject_ImplementationQuality_Orchestrator_v0_1 と
AutoTradeComponentLifecycle_Orchestrator_v0_1 のルールに従う実装担当です。

目的
----
WSL2上のクローンで、RUN-P2-IC-001 と同じP2-D07の固定fixture試験を、
外向きネットワークを使わない隔離環境で安全に実行できる基盤を構築してください。
人間の実行操作は、Windowsホストから一つのPowerShellコマンドを実行するだけにします。
そのコマンドは、Windows側のhost確認 → 隔離設定 → wsl --shutdown → Linux側の前提確認 → 固定4 Gate → 証跡保存 → 隔離設定の完全復元を
try/finallyで必ず行わなければなりません。

最重要の前提
--------------
- WSL2の通常NATは隔離ではない。WSL2の networkingMode=none だけを、テスト実行時の隔離方式として採用する。
- Windows用の .venv/Scripts/python.exe をWSLから実行してはならない。Windows側で実行され、WSLの隔離を失うためである。
- RUN-P2-IC-001 はWindows用の固定commandを持つ証跡として変更しない。
  新しいRun ID RUN-P2-IC-001-WSL を、repository管理のtrusted scope registryへ新設する。
- WSL用Runは .venv/bin/python の固定commandだけを使う。
- 試験対象は src/autotrade/market_data、tests/market_data、tests/fixtures/market_data だけ。
  scope_mode=target_only とし、対象外のHEAD/worktree差分で試験対象を決めない。
- 外部ネットワーク、Databento、Broker、Secret、実データ、実取引への接続は禁止する。
- 隔離後のpip installは禁止する。Python依存は隔離前に、承認済みローカルwheelhouseだけから固定版を用意する。
- Human Gateを作業Agentが自己承認してはならない。今回の自動処理はPASSを自己宣言せず、必要ならHUMAN_GATE_REQUIREDで止める。

最初に読むもの
--------------
1. README.md
2. AGENTS.md
3. settings/language.md
4. settings/ai_component_rules.md
5. doc/00_全Phase残課題Blocked統合台帳.html の BLK-RUN-003 節
6. scripts/quality_gate/runner.py
7. scripts/quality_gate/trusted_scopes.json
8. test/evidence/phase2/RUN-P2-IC-001/run-manifest.json
9. .codex/orchestrators/AutoTradeProject_ImplementationQuality_Orchestrator_v0_1.json

実装前の必須作業（TDD）
------------------------
次の失敗テストを先に追加し、pytestでREDを記録してください。

1. RUN-P2-IC-001-WSLだけが、registryのWSL用固定4 command、P2-D07、REQ-Q02/19/20/23、
   固定fixture checksum、scope_mode=target_onlyを完全一致で受理する。
2. Windows用command、任意のPython module、任意pytest、別target_paths、別fixture checksum、
   別baseline、別scope_modeは実行前にManifestValidationErrorまたはBLOCKEDになる。
3. WSL用Host PowerShell wrapperのDryRunは、.wslconfigを変更せず、予定した隔離・復元・
   WSL実行コマンドだけを出力する。
4. Host wrapperは、元の %UserProfile%\.wslconfig が存在した場合も存在しなかった場合も、
   実行成功・テスト失敗・例外の全てで元の状態を正確に復元する。
5. WSL内runnerはdefault routeが残る、wheelhouseが不足、Linux用ツールversion不一致、
   target hash不一致、host-isolation証跡欠落のいずれかで、4 Gate開始前にBLOCKEDになる。

RED証跡は test/evidence/phase2/RUN-P2-IC-001-WSL/ に保存してください。
その後、最小の実装を追加して同じテストをGREENにしてください。

実装する成果物
----------------
既存部品を再利用し、同じ責務のRunnerやwrapperを二重に作らないこと。

1. scripts/quality_gate/trusted_scopes.json
   - RUN-P2-IC-001-WSLを追加する。
   - phase_id、requirements、design、fixture、target_paths、excluded_paths、baseline_ref、
     scope_mode=target_only、network_isolation_required=trueは元Runと同じ安全条件にする。
   - 4 commandは次だけに固定する。Python実行ファイルは .venv/bin/python とする。
     formatter: .venv/bin/python -m ruff format --check src/autotrade/market_data tests/market_data
     lint:      .venv/bin/python -m ruff check src/autotrade/market_data tests/market_data
     type:      .venv/bin/python -m mypy src/autotrade/market_data
     test:      .venv/bin/python -m scripts.quality_gate.local_p2_pytest

2. test/evidence/phase2/RUN-P2-IC-001-WSL/run-manifest.json
   - 新Run ID、P2-D07、REQ-Q02/REQ-Q19/REQ-Q20/REQ-Q23、WSL固定commandを記録する。
   - change_hashはWSL cloneの対象3パスだけから計算する。変更前に仮値を置いて通してはいけない。

3. scripts/wsl_quality_gate/run_isolated_p2.ps1
   - これは `run_test.ps1` から内部的に呼ばれるWindows host wrapperとする。人間が使う唯一の入口は `run_test.ps1` とし、WSL内から .wslconfig を切り替えようとしてはならない。
   - パラメータは少なくとも -Distro、-RepositoryPath、-RunId（既定RUN-P2-IC-001-WSL）、-DryRun を持つ。
   - 実行前はWindows側で、wsl --version、wsl -l -v、対象がVERSION 2、RepositoryPathの安全な形式だけを確認する。
     全ディストリビューションがStoppedでない場合や対象がWSL2でない場合は、設定変更前にBLOCKEDで終了する。
     この段階で `wsl -d` によるLinux起動、repository、manifest、wheelhouse、WSL用venvの確認をしてはならない。
   - %UserProfile%\.wslconfig の存在有無と元バイト列のSHA-256を一意な一時backupへ保存する。
   - [wsl2] networkingMode=none と firewall=true を設定し、wsl --shutdown で反映する。
     既存の別設定は壊さない。実装が安全にpatchできない場合は、元ファイルを完全backupして
     一時的に置換し、finallyで元バイト列を完全復元する。
   - 設定反映後にWSLを非対話で一回だけ起動し、下記のLinux runnerを呼ぶ。Linux runnerがWSL2 kernel、repository、manifest、registry、
     wheelhouse、WSL用venv、network隔離、Linux tool version、fixture checksumを確認し、成功した場合だけ固定4 Gateを開始する。
   - 成功、テスト失敗、PowerShell例外、Ctrl+C相当の終了でも finally を使い、
     元の .wslconfig を復元し、再度 wsl --shutdown を実行する。
   - 復元後に、元の存在有無とSHA-256が一致することを確認する。違えば最優先FAILEDにする。
   - isolation証跡とrestore証跡を test/evidence/phase2/RUN-P2-IC-001-WSL/ に書く。
   - 通常ホストでmarkerだけを設定する分岐、外部疎通テスト、Firewallの恒久変更は禁止する。

4. scripts/wsl_quality_gate/run_isolated_p2.sh
   - WSL内でだけ呼ばれる。bashは strict mode を使う。
   - 外部接続テストはしない。ip addr と ip route を読み取り、default routeまたは通常の外向きNICが
     残る場合は、QUALITY_GATE_NETWORK_ISOLATION_CONFIRMEDを設定せずBLOCKEDで終了する。
   - .venv/bin/python、ruff、mypy、pytest、pytest-covの固定versionを確認する。
   - 禁止語・禁止依存（Databento、Broker、Secret、socket外部接続、network client）を、
     registryで許可された対象とwrapper以外に広げず、既存の検査方式を再利用して確認する。
   - host-isolation.jsonへ、WSL version、distro、networkingMode=noneを設定したhost wrapperの実行ID、
     ip addr要約、ip route要約、確認時刻、対象scope、fixture hashを保存する。
   - これらの確認に成功したそのプロセスだけで QUALITY_GATE_NETWORK_ISOLATION_CONFIRMED=1 を設定し、
     run_quality_gateを指定Manifestで実行する。
   - verification.jsonへ実行コマンド、終了コード、tool version、scope、fixture SHA-256、
     target-only change SHA-256、Gate結果、復元待ち状態を保存する。
   - 成功してもHuman Gateを自己承認せず、HUMAN_GATE_REQUIREDまたは既存の正式な状態遷移を維持する。

5. scripts/wsl_quality_gate/prepare_offline_wsl_env.sh
   - 隔離前に一度だけ実行する準備用スクリプトとする。
   - 承認済みwheelhouseを入力とし、--no-index --find-links を使ってWSL内 .venv を構成する。
   - wheelhouseがない場合にネットワークへ取りに行かずBLOCKEDとする。
   - requirements-dev.txtの固定versionを照合し、versionとwheelhouseファイルSHA-256を証跡へ記録する。

6. 関連テスト、README.md、AGENTS.md、doc/ai_foundation、doc/index.html、
   doc/00_全Phase残課題Blocked統合台帳.html
   - AI部品・保存先・WSL用Run ID・実行入口・証跡の意味だけを必要最小限同期する。
   - BLK-RUN-003は、実際の隔離実行と復元証跡が揃うまでは解決済みに変更しない。

単一の人間実行コマンド
--------------------------
実装・GREEN・レビュー後に、READMEと最終報告で次の形式の一行だけを示してください。
これはWindows PowerShellから実行する。WSL内から実行してはならない。

powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\wsl_quality_gate\run_test.ps1

この一行の期待動作は、Windows側host確認 → 隔離設定 → wsl --shutdown → WSL内前提確認 → 固定4 Gate →
証跡保存 → .wslconfig完全復元 → wsl --shutdown である。
`run_test.ps1` はwrapper出力、終了コード、最新の前提確認またはverification証跡を automationディレクトリへ保存する。
どこか一つでも失敗した場合、4 Gateを始めないか、失敗として証跡を残し、復元後に非0で終了する。

検証とレビュー
--------------
- formatter、lint、mypy、pytestを実施する。
- PowerShell wrapperはDryRunと失敗時復元を必ず検証する。通常ホストのネットワークを実際に切る本番実行は、
  DryRun/GREEN後かつ人間が上記の一行を実行した時だけにする。
- 独立Pythonレビューと取引安全レビューを実施し、Critical/High、scope外実行の可能性、
  復元不能、外部接続、証跡欠落が残る場合は停止する。
- 実装中・テスト中に外部ネットワーク、Databento、Broker、Secret、実データ、実取引へ接続してはならない。

最終報告
--------
次を日本語で簡潔に報告する。
1. 作成・変更したファイル
2. RED/GREEN、formatter、lint、type、pytest、レビューの結果
3. 実行前の準備条件（WSL2 version、wheelhouse、cloneのcommit固定）
4. 人間が実行する一行コマンド
5. 保存される証跡パス
6. PASSに進めない残件。自己承認はしないこと。
```

## 人間がこのプロンプトを使う前の確認

- Codex CLIはWSL2内で起動する。WSL1ではない。
- リポジトリは対象commitへ固定してクローンする。未コミットのWindows作業ツリーをWSLから直接試験対象にしない。
- 依存wheelhouseは隔離前に承認済み入手元から用意する。隔離ランナーはネットワーク取得をしない。
- 単一実行コマンドは、Codexが作成した後にWindows PowerShellから実行する。
