# WSL2隔離品質ゲート: Windows作業引継ぎコンテキスト

更新日: 2026-08-07

## この文書の目的

このリポジトリは、Linux側の `/home/oue/strategy_test` で実装・検証を進めた後、
Windows側の `C:\project\strategy_test` で起動するCodexへ作業を引き継ぐための文書である。
Windows側では、この文書と `07_WindowsCodex引継ぎプロンプト.md` を最初に読むこと。

この作業は `RUN-P2-IC-001-WSL` の隔離品質ゲートである。P2-D07の固定fixtureに対して、
WSL2の `networkingMode=none` 下で固定4 Gateを実行し、隔離と復元を証跡化する。
Human Gateは未承認であり、成功した場合でも自動的にPASSへ進めてはならない。

## リポジトリと実行環境

| 役割 | パス | 備考 |
|---|---|---|
| Windows側の作業・host wrapper | `C:\project\strategy_test` | この引継ぎの対象。Git pull後にCodexが作業するclone。 |
| WSL側の実行対象 | `/home/oue/strategy_test` | Linux runner、`.venv/bin/python`、wheelhouse、fixtureを使用するclone。 |
| 対象distro | `Ubuntu-24.04` | WSL2でなければならない。 |
| 固定Run ID | `RUN-P2-IC-001-WSL` | 任意のRun IDやcommandへ差し替えてはならない。 |

Windows側の `run_test.ps1` はWindows cloneから実行し、Linux runnerは `-RepositoryPath /home/oue/strategy_test` でWSL cloneを実行する。実機Runの前に、ユーザーが必要なタイミングでWSL側に `git pull --ff-only` を実行し、二つのcloneのHEADを確認する。AIはWSL cloneを同時更新しない。

## 実装済みの成果物

### 固定scopeと隔離runner

- `scripts/quality_gate/trusted_scopes.json`
  - WSL専用 `RUN-P2-IC-001-WSL` を追加済み。
  - formatter、lint、type、testの4 commandは `.venv/bin/python` に固定。
- `tests/evidence/phase2/RUN-P2-IC-001-WSL/run-manifest.json`
  - P2-D07、REQ-Q02/19/20/23、固定fixture checksum、`scope_mode=target_only` を記録済み。
- `scripts/wsl_quality_gate/prepare_offline_wsl_env.sh`
  - 承認済みwheelhouseだけを使用し、ネットワークなしでLinux venvを準備するスクリプト。
- `scripts/wsl_quality_gate/run_isolated_p2.sh`
  - WSL内runner。repository、manifest、Linux venv、wheelhouse、registry、fixture、WSL2 kernel、network隔離、固定tool versionを4 Gate前に確認する。
  - default routeまたは外向きNICが残る場合はBLOCKEDにする。
  - 隔離確認後だけ `QUALITY_GATE_NETWORK_ISOLATION_CONFIRMED=1` を設定し、`host-isolation.json` と `verification.json` を残す。

### Windows host wrapperと自動ログ取得

- `scripts/wsl_quality_gate/run_isolated_p2.ps1`
  - `.wslconfig` の元バイト列とSHA-256をbackupする。
  - `[wsl2] networkingMode=none` と `firewall=true` を一時設定する。
  - `wsl --shutdown` 後にLinux runnerを一回だけ起動し、finallyで設定を完全復元して再度shutdownする。
  - PowerShell配列の`.Count`、`List[string].AddRange`、WSL出力のNUL文字に関する既知の失敗を修正済み。
  - Windows hostだけの確認を先に行い、`uname -r`、repository、venv等は隔離後のLinux runnerへ移動済み。
  - WSL内からの起動は拒否する。
  - `-AllowRunningDistro` は、UNCパスを読むだけで対象WSLが起動する場合の明示的な続行許可である。対象WSL内のCodexや他の処理が停止済みである場合だけ使う。
  - 隔離中にWSL cloneの `verification.json` を採取し、host wrapperのexecution IDを含む `wsl-verification-capture.json` として保存する。隔離解除後に証跡取得のためだけにWSLを再起動しない。
- `scripts/wsl_quality_gate/run_test.ps1`
  - 人間向けの入口。wrapperの標準出力・標準エラー、終了コード、選択した証跡を `tests/evidence/phase2/RUN-P2-IC-001-WSL/automation/` に保存する。
  - 180秒のwrapper timeoutと45秒の証跡取得timeoutを持つ。
  - 通常実行では、今回のexecution IDと一致する `wsl-verification-capture.json` だけを使う。Windows clone内の `verification.json` は候補にしない。設定前にBLOCKEDとなったときだけ、同じexecution IDかつ今回更新された `preflight.json` を使う。
  - `-AllowRunningDistro` 使用時にrunnerが開始済みなら、automation証跡を書いた後に `wsl --shutdown` を実行する。
- `tests/quality_gate/test_wsl_quality_gate_contract.py`
  - 固定scope、wrapperの復元・起動順、Linux runnerのfail-closed条件、automationログの契約を静的に確認する。

### 設計・運用文書

- `AGENTS.md`
- `README.md`
- `plan/phase2-5_ai_foundation/05_WSL2隔離品質ゲート構築_CodexCLI依頼プロンプト.md`
- `doc/00_全Phase残課題Blocked統合台帳.html`
- `doc/ai_foundation/19_Phase2-5実装品質基盤実装検証.html`

これらは、host-only確認 → 一時隔離設定 → `wsl --shutdown` → Linux側前提確認 → 固定4 Gate → 証跡 → 完全復元、という順序へ同期済みである。

## 実行・デバッグ履歴

1. 初期のPowerShell wrapperは、`.wslconfig`読み込み結果が単一行の場合に配列ではなくscalarになり、`$lines.Count` で失敗した。`[string[]]`で明示的に正規化して修正済み。
2. 次に、`List[string].AddRange()` へ `System.Object[]` を渡して失敗した。`[string[]]`へのcastで修正済み。
3. PowerShell構文エラーが発生した版は破棄し、配列を変数へ代入する構文へ直した。
4. `wsl -l -v` の出力にはNUL文字が混在した。host wrapperはNULを除去してからdistro状態を判定する。
5. 2026-08-06 21:52 JSTの最新実行は4 Gateを開始していない。`preflight.json` は `BLOCKED` で、理由は対象 `Ubuntu-24.04` がRunningだったことである。
6. そのときの `run-test-summary.json` はchild PowerShellの終了コードがnullとなり、過去の `verification.json`（`DRY_RUN`）を読んで `FAILED` と誤表示した。この誤判定を避ける更新時刻判定はソースへ実装済みだが、修正後の実機実行はまだ行っていない。

現在の生成証跡は履歴であり、実機4 Gateの成功証明ではない。特に `verification.json` の `DRY_RUN` は古い計画結果である。

## 未解決事項と優先順

### P0: Windows/WSL二重cloneでの証跡取り違え（静的改訂済み、実機未確認）

Windows cloneから `run_test.ps1` を実行すると、`$evidenceRoot` は `C:\project\strategy_test\tests\evidence\...` になる。一方、Linux runnerが更新する `verification.json` も `/home/oue/strategy_test/tests/evidence/...` である。

2026-08-07に、wrapper execution IDで照合する方式を実装した。host wrapperは隔離中にWSL側 `verification.json` を採取し、`wsl-verification-capture.json` に採取元のWSLパス、execution ID、採取時刻、WSL証跡本体を保存する。`run_test.ps1` はこの採取物だけを選び、Windows cloneの `verification.json` を候補にしない。隔離解除後にWSLを再起動して読み直すこともない。

古いWindows側 `verification.json`（`DRY_RUN`）と、新しいWSL側採取証跡が共存する回帰テストを追加し、WSL側の `BLOCKED` 証跡だけを選ぶことを確認した。PowerShell parser、Bash構文、契約テストは通過した。実機隔離runで同じexecution IDの証跡が得られることは、ユーザー承認後に別途確認するまで未確認である。

### P1: 実機PowerShell構文・隔離実行の未検証

Linux側から `powershell.exe` のPowerShell parserを呼ぼうとしたが、WSL interop socket errorで実施できなかった。Windows側で以下を行うこと。

- `run_isolated_p2.ps1`、`run_test.ps1`、`select_automation_evidence.ps1` のPowerShell parser確認は2026-08-07に通過した。
- `.wslconfig` が存在する場合・存在しない場合のDryRunと復元確認。
- すべての前提が満たされたときの実機隔離run。

### P2: 実行前の準備確認

- ユーザーがWSL cloneで `git pull --ff-only` を実行し、今回のGitコミットへ更新済みであること。AIは更新せず、読み取りでHEADだけ確認する。
- `/home/oue/strategy_test/.venv/bin/python` が存在すること。
- `/home/oue/strategy_test/wheelhouse/` が存在すること。
- `ruff 0.16.1`、`mypy 2.3.0`、`pytest 9.1.1`、`pytest-cov 7.1.0`、Python `3.12.13` がLinux venvに入っていること。
- 他のWSL distroがRunningでないこと。
- `-AllowRunningDistro` は、UNC上のファイル読み取りで対象だけが起動した場合に限ること。対象WSL内のCodex・VS Code Remote・端末を動かしたまま使わないこと。

## 現時点の検証結果

- `./.venv/bin/python -m pytest -q tests/quality_gate/test_wsl_quality_gate_contract.py`: `6 passed`
- `bash -n scripts/wsl_quality_gate/run_isolated_p2.sh`: 成功
- 対象コードのformatter/lint/type/fixed pytestを含む実機4 Gate: 未実行
- PowerShell parser: Windows側で未実行
- Human Gate: 未承認

## Windows側の最初の行動

1. `git pull --ff-only` でこの文書を含む最新commitへ更新する。
2. `AGENTS.md`、この文書、`07_WindowsCodex引継ぎプロンプト.md`、`README.md` を読む。
3. ユーザーがWSL側の `git pull --ff-only` を完了した後に、Windows cloneとWSL cloneのcommitを読み取りで照合する。
4. P0の証跡取り違えを修正し、テストを追加する。
5. PowerShell parserと契約テストを実行する。
6. 隔離runは、P0/P1が解消し、ユーザーが実機実行を許可した場合だけ行う。成功してもHuman Gateを自己承認しない。
