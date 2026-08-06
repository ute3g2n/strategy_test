# RUN-P2-IC-001 S4.1–S4.4 現況・Blocked 台帳

> **全プロジェクトの現在状態は [全Phase 残課題・Blocked 統合台帳](../../../../doc/00_全Phase残課題Blocked統合台帳.html) が正本です。** 本書は `RUN-P2-IC-001` の詳しい証跡として残し、このRunの更新結果を統合台帳へ反映します。

更新日: 2026-08-06  
Run ID: `RUN-P2-IC-001`  
Design: `P2-D07`  
Requirements: `REQ-Q02` / `REQ-Q19` / `REQ-Q20` / `REQ-Q23`  
HEAD: `8d3f3d3dd41b6d5b33e6b870a3f5b4f1b10ffab4`  
実差分 SHA-256: `sha256:f36cc96229e5ba713af953593a57a3d9b4b9e4d3526305bd25f5e22fd2e7c42a`  
fixture SHA-256: `sha256:94022229698e972353b8ec9537f455af5cb29d47253f5f2a1ed5d33b08b50169`

注: S4.4の独立レビューは旧差分hashを入力に実施した。その後、対象限定scope変更により、現在のchange_hashは上記へ更新した。対象外の文書・設定差分を理由に停止するルールは廃止し、`RES-RUN-TARGET-ONLY` として解消した。レビューの再実施が必要な項目は別欄に残す。

## 結論

S4.1 から S4.4 を実行した結果、初期の実装・ツール不足は大部分が解消された。しかし、Run の受入条件はまだ満たしていない。対象限定scopeへの変更で差分判定の問題は解消した。現在の根本的な Blocked は次の **2系統** である。

1. **High: hostのoutbound isolationが未確認**。現在の端末ではRunnerが子プロセスを一つも起動せず停止する。
2. **High: 権限者による署名済み Human Gate が存在しない**。作業 Agent の自己承認は不可であり、worktree 外の秘密鍵署名と repository 管理公開鍵による検証が必要である。

したがって、現在の状態は `BLOCKED`。Human Gate 承認依頼および `decision=approved` の承認 JSON は作成していない。

## S4.1–S4.4 の実行結果

| Step | 実施内容 | 解消したもの | 残ったもの | 判定 | 主な証跡 |
|---|---|---|---|---|---|
| S4.1 | P2-D07 の読み取り評価。S2 bootstrap scope、未導入 ruff/mypy/pyright、未解決 change_hash、Human Gate 未承認を確認 | なし（問題を可視化） | 4項目すべて | BLOCKED | `baseline.json`、`04_パイロット評価.md` |
| S4.2 | trusted scope registry、P2 wrapper、Manifest照合、差分停止、host isolation fail-closed、TDD RED/GREEN を実装 | Runner の P2 scope 拒否、Manifest改変許容、固定 wrapper 不在 | ツール、hash、scope外差分、Human Gate | BLOCKED | `trusted_scopes.json`、`runner.py`、`tdd-quality-gate-extension-red.md` |
| S4.3 | ruff 0.16.1、mypy 2.3.0、pytest 9.1.1、pytest-cov 7.1.0 を導入。formatter/lint/type/test/coverageを実行。change_hash確定、`.coverage`をindex除外 | ツール未導入、change_hash未解決、fixture/coverage証跡不足 | scope外差分、Human Gate | BLOCKED | `s4-3-tooling.md`、`verification.json`、`coverage.json` |
| S4.4 | Pythonレビュー → 取引安全レビュー → 品質ゲートレビューを順番に実施 | コード上のCritical/High、外部接続経路、hash不一致、Unknownはなし | 署名済みHuman Gate不在 | BLOCKED | `reviews/s4-4-*.md`、`verification.json` |

## 解消済み項目

| 項目 | 現在の確認結果 | 根拠 |
|---|---|---|
| RunnerのP2 scope拒否 | 解消。registry登録済み、Manifestの固定scope/command/moduleを照合可能 | `scripts/quality_gate/trusted_scopes.json`、`scripts/quality_gate/runner.py` |
| ruff/mypy/pytest/pytest-cov | 解消。固定版を開発設定へ記録し、導入済み | `requirements-dev.txt`、`pyproject.toml` |
| formatter/lint/type | 解消。各終了コード 0 | `verification.json` |
| P2 pytest / TDD | 解消。P2 wrapper 9 passed、quality-gate 35 passed、全体42 passed。RED/GREEN証跡あり | `tdd-quality-gate-extension-red.md`、`verification.json` |
| coverage | 解消。88.43%、閾値80% | `coverage.json`、`verification.json` |
| fixture checksum | 解消。registry、Manifest、実ファイルが一致 | `trusted_scopes.json`、`run-manifest.json`、`baseline.json` |
| change_hash | 解消。Runner再計算値とManifest値が一致 | `verification.json` の `hashes` |
| Unknown | 解消。registry/Manifestとも `unknowns=[]` | `trusted_scopes.json`、`run-manifest.json` |
| 外部接続 | 解消。Runnerはhost isolation未確認時に停止、wrapperはsocket接続を拒否 | `runner.py`、`local_p2_pytest.py`、取引安全レビュー |
| 証跡欠落 | S4.4レビュー個別ファイルを追加済み | `reviews/s4-4-python-review.md`、`s4-4-trading-safety-review.md`、`s4-4-quality-gate-review.md` |
| 試験対象の判定 | 解消。HEAD全体ではなく、registryの三つのtarget_pathsだけで差分とhashを判定 | `scripts/quality_gate/trusted_scopes.json`、`scripts/quality_gate/runner.py`、`tests/quality_gate/test_runner.py` |

## 現在の Blocked 台帳（根本原因で重複排除）

| ID | 重要度 | 状態 | 原因 | 証拠 | 解消条件 | 影響 |
|---|---|---|---|---|---|---|
| BLK-RUN-003 | High | OPEN | 現在のhostでoutbound isolationの確認がなく、Runnerのnetwork probeがfail-closedで停止する。 | `verification.json` の `post_global_ledger_runner_probe` | 承認済みのOS隔離、Firewall、Sandbox等で外向き通信を遮断し、host側の確認を記録する。環境変数だけを承認根拠にしない。 | scope検査・4 Gate subprocess開始不可。 |
| BLK-P2-S4-HUMAN-001 | High | OPEN | 署名済み承認 JSON がなく、Human Gate は未承認。作業 Agent の自己承認は禁止。 | `human-gate.md`、`verification.json` の `approval_json=not_created` | worktree 外で権限者が秘密鍵署名。Runnerが repository 公開鍵で `decision=approved`、`approved_by`、`approved_at`、Run ID、commit、change_hash、fixture_hash、`remaining_items=[]` を検証。 | verification/RunnerをPASSへ更新不可。 |

### 重複 Finding の対応関係

- scope外差分: `S4.4-PY-002`、`S4.4-TS-002`、`S4.4-QG-002` → `BLK-P2-S4-SCOPE-001`
- Human Gate不在: `S4.4-TS-003`、`S4.4-QG-003` → `BLK-P2-S4-HUMAN-001`

## 状態更新の運用契約

この台帳は上書きせず、各再実行の結果を末尾へ追記する。change_hashに影響する実装・計画ファイルへ台帳本文を置かず、証跡 root 内に保存する。

### 解消確認の順番

1. HEAD commit、fixture SHA-256、Manifest、registryを読み取る。
2. Runnerで実差分 hashを再計算し、Manifestと一致することを確認する。
3. target/excluded path、skip、削除、Unknown、禁止依存を確認する。scope外があれば即BLOCKED。
4. formatter → lint → type →固定P2 pytest → coverageを実行し、終了コード・version・scope・証跡を追記する。
5. Pythonレビュー → 取引安全レビュー → 品質ゲートレビューを順番に実行し、各Findingに再レビュー結果を追記する。
6. Critical/High、証跡欠落、設計外変更が0になった場合だけ、権限者へのHuman Gate承認依頼を作成する。
7. 承認 JSONはAgentが作成・自己承認せず、worktree外の署名をRunnerが公開鍵で検証する。内容不一致・署名不正・拒否・未承認なら `HUMAN_GATE_REQUIRED` または `BLOCKED` を維持する。
8. すべての条件が揃った場合だけ `verification.json` とRunnerの状態を `PASS` へ更新し、承認証跡の検証結果を追記する。

### 追記テンプレート

```text
## Update YYYY-MM-DDTHH:MM:SS+09:00
- actor / role:
- trigger:
- HEAD commit:
- actual change_hash:
- fixture_hash:
- changed blocker IDs:
- command/evidence paths:
- result: OPEN / RESOLVED / REOPENED
- next stop condition:
```

## Update 2026-08-06T00:00:00+09:00
- actor / role: Codex / Runner改訂
- trigger: BLK-RUN-001のユーザー指示
- HEAD commit: `8d3f3d3dd41b6d5b33e6b870a3f5b4f1b10ffab4`
- actual change_hash: `sha256:f36cc96229e5ba713af953593a57a3d9b4b9e4d3526305bd25f5e22fd2e7c42a`
- fixture_hash: `sha256:94022229698e972353b8ec9537f455af5cb29d47253f5f2a1ed5d33b08b50169`
- changed blocker IDs: `BLK-RUN-001` → `RES-RUN-TARGET-ONLY`
- command/evidence paths: `tests/quality_gate/test_runner.py`, `scripts/quality_gate/runner.py`, `scripts/quality_gate/trusted_scopes.json`
- result: RESOLVED（対象限定scopeのGREENテスト済み）
- next stop condition: `BLK-RUN-003` または `BLK-P2-S4-HUMAN-001` が残る間はPassにしない

## Update 2026-08-06T00:05:00+09:00
- actor / role: ユーザー / 権限者
- trigger: BLK-RUN-002の承認申告
- changed blocker IDs: `BLK-RUN-002` → `RES-RUN-HUMAN-APPROVAL`
- result: 台帳上は解決済み。正式な署名JSONの検証は、RunnerをPASSへ変更する直前の必須確認として残す。
- remaining operational blocker: `BLK-RUN-003`（host outbound isolation未確認）
- concrete resolution: 承認済みWindows Sandbox/VMまたはnetwork-disabled CIで送信通信を遮断し、host設定の確認者・時刻・設定証拠を保存してからRunnerを実行する。
