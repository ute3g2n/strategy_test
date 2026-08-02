---
name: autotrade_phase1_skill_source_reader_v0_1
description: Phase 1専用。要件定義書、Phase分割方針、既存成果物を読み、設計入力として整理する。
---

# autotrade_phase1_skill_source_reader_v0_1

## 目的
参照元文書から、Phase 1で固定すべき設計入力と、後続Phaseへ送る詳細項目を抽出する。

## 入力
- `plan/自動トレードシステム_要件定義書.md`
- `plan/Phase分割と設計書整備方針_v0.1_2026-08-02.md`
- P1-00成果物

## 出力
- 要件要約
- Phase 1対象範囲
- Phase 1非対象範囲
- 未確定事項候補

## 禁止事項
- 参照元にない確定事項を作らない。
- 投資助言、売買推奨にしない。
- 文字化けや不明点を成功扱いしない。

## 品質チェック
- 参照元ファイル名が残っている。
- Q番号、OD番号、Phase方針が追跡できる。
- Unknownが明示されている。
