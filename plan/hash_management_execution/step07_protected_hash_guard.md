# Step 07 保護hash限定ガード導入記録

実施日: 2026-08-15

## 実施内容

- `autotrade_skill_protected_hash_policy_guard_v0_1` を新設した。
- `AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1` を新設し、固定model `gpt-5.6-luna`、`reasoning_effort=low`、超軽量の静的発火条件、3値判定、出力schema、停止境界を定義した。
- A95はhash値、manifest、stale、fingerprint、receipt hash、hash retryを計算・取得・保存・比較しない。
- 新設した `scripts/ai_foundation/protected_hash_policy_guard.py` は、対象パスの境界と候補語句だけを確認し、hash値を扱わず、ALLOW／NEEDS_HUMAN_GATE／BLOCKEDをJSONで返す。
- Phase計画、AI部品Lifecycle、設計書セット、HTML writer、Implementation Qualityの各経路へHASH-FUTURE-01〜08とA95発火条件を同期した。
- `AGENTS.md`、`README.md`、`settings/ai_component_rules.md`、AI foundation 03〜19へ現行ルールを追記した。A07/A08の文章manifest通常経路は復活させていない。

## 判定境界

| 候補 | 判定 | 扱い |
|---|---|---|
| manifest、証跡、差分許可、file identity、stale、受入、receiptの管理hash | BLOCKED | path、schema、link、状態、意味的IDへ置換し、hash retryをしない |
| 安全・データ・再現性へ直接因果のある既存protected hash | ALLOW | 目的、保護対象、失敗時停止範囲を明記し、既存fail-closedを維持 |
| 用途不明、仕様衝突、根拠不足 | NEEDS_HUMAN_GATE | 推測で追加・削除・置換しない |

## 検証

- A95のJSON、関連Orchestrator、Agent JSON: JSON parse PASS。
- Skill creatorの`quick_validate.py`: 実行したが、実行環境にPyYAMLがなく起動不能。プロジェクトの既存underscore命名規約を維持し、frontmatterの必須項目・description・本文構造を手動確認した。
- `ruff check scripts/ai_foundation/protected_hash_policy_guard.py tests/ai_foundation/test_protected_hash_policy_guard.py`: PASS。
- `pytest tests/ai_foundation/test_protected_hash_policy_guard.py -q`: `3 passed`。
- スクリプトの合成入力確認: management候補はBLOCKED、protected data/repro候補は目的付きALLOW、用途不明checksumはNEEDS_HUMAN_GATE。
- 外部I/O、Secret、Broker、Live、Git write、WSL実行: 実施していない。

## 権限適用

文章管理基盤と廃止対象の管理用hashチェックを強制スキップして完了する。安全・データ・再現性に直結する保護対象hashは維持する。A95自身はhashを計算せず、管理hash不一致を理由にretryしない。
