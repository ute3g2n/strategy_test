# CTX-00 棚卸し・対象分類

## 1. 実行結果

- 実行日: 2026-08-14（Asia/Tokyo）
- 対象リポジトリ: C:/project/strategy_test
- ブランチ: main
- 基準HEAD: 200f556cee868fadc3a13d8267bc5b26cb212b32
- 実行状態: 完了（ルート責務チェックリストによるフォールバック）
- 独立サブエージェント完了: なし
- ディスパッチ状態: RUNTIME_DISPATCH_FALLBACK_REQUIRED
- 詳細な起動証跡: CTX-00_dispatch_receipt.json

CTX-00担当サブエージェントは長時間完了しなかったため停止した。未完了の独立レビューを完了扱いにせず、同じ調査条件をルートで再実行し、成果物を作成した。CTX-01以降の正式な設計判断は、CTX-00の独立完了証跡がないことを前提に扱う。

## 2. 棚卸しの対象と除外

管理対象として拡張子が次のいずれかであるファイルを走査した。

- 文書: .md、.html
- ソース: .py、.js、.mjs、.cjs、.ts、.tsx、.ps1、.sh、.cmd
- 設定・メタデータ: .json、.toml、.yaml、.yml

次の境界は、管理対象の分類結果に混ぜず、存在・Git ignore状態を別途確認した。

- third_party
- node_modules
- .venv
- tests/evidence
- dist、build、coverage
- .codex-remote-attachments

この扱いは「対象外として放置する」という意味ではない。第三者コード、生成物、証跡、添付物、秘密情報候補を通常の参照マニフェストへ混入させないための境界であり、CTX-02以降のポリシーとCTX-08の完全インデックスで明文化する。

## 3. 分類結果

### 3.1 管理対象インベントリ

| 分類 | 件数 | 分類基準 |
|---|---:|---|
| managed_document | 409 | .md、.html。人間またはAIが参照する正式・計画・運用文書 |
| managed_source | 166 | 実行ロジック、スクリプト、テスト補助を含むソース |
| managed_config | 107 | JSON、TOML、YAML、YMLの設定・メタデータ |
| sensitive_or_unknown | 0 | 今回の管理対象走査では該当なし。境界配下の未確認内容は別管理 |
| 合計 | 682 | 境界ディレクトリを除く拡張子対象 |

各ファイルの相対パス、分類、Git追跡状態、サイズ、SHA-256は
CTX-00_対象パスハッシュ.tsv に固定した。基準線全体の再計算用ダイジェストは
CTX-00_変更基準線.json の inventory_digest_sha256 に記録した。

### 3.2 境界サーフェス

| パス | 存在 | Git ignore | 初期判断 |
|---|---|---|---|
| third_party | あり | あり | 第三者・依存物境界 |
| node_modules | あり | あり | ランタイム生成物境界 |
| .venv | あり | あり | Python実行環境境界 |
| tests/evidence | あり | なし | 証跡。完全インデックスで参照可否を決める |
| dist | なし | なし | 未使用 |
| build | なし | なし | 未使用 |
| coverage | なし | なし | 未使用 |
| .codex-remote-attachments | あり | なし | ユーザー提供の未追跡物。自動登録しない |

## 4. 既存導線とAI部品の確認

- doc配下のHTML: 115件
- doc/index.html等への直接参照を単純ヒューリスティックで検出できたHTML: 108件
- 直接参照を検出できなかったHTML: 7件。これは未到達と断定せず、リンク解決とマニフェスト網羅性をCTXMAP-UNK-02で再確認する。
- 既存Skill: 59件
- 既存Agent定義JSON: 46件
- 既存Orchestrator定義JSON: 9件
- 自動コミット監視: 停止中。watch-commit is stopped.
- auto-commit.sh / auto-commit.cmd は git add -A を含むため、将来の自動化ではユーザー未追跡物を巻き込まない対象制御が必要。

既存の標準基盤として、Phase計画、AI部品ライフサイクル、設計文書セット、実装詳細設計、品質検証に関するOrchestrator・Agent・Skillが存在する。CTX-00時点では参照マニフェスト専用部品は実体化していない。

## 5. 変更基準線

- 正本基準線: CTX-00_変更基準線.json
- 詳細ハッシュ一覧: CTX-00_対象パスハッシュ.tsv
- インベントリSHA-256: 4b5a888a1cd0ae23f146747b90560990125294a2b5894b80d4a83cd7001f5a22
- 以後の各CTXでは、作業前後に同じ走査を行い、対象外のユーザー変更を差分へ混ぜない。

今回のGit作業ツリーに既に存在した変更は次の3件であり、今回の成果物には含めない。

- .codex-remote-attachments/
- plan/backtest_and_turtles_full_chat_history.md
- plan/資料参照効率化施策.md

## 6. Unknownと次工程への引き渡し

- CTXMAP-UNK-01: TypeScript／PowerShell／shellの構文抽出方式が未確定。CTX-02で既存依存だけによる精度を試験し、追加parserが必要なら別承認に止める。
- CTXMAP-UNK-02: 境界配下、生成証跡、未追跡ファイル、新規追加ファイルを含む完全な網羅性・相互リンクの自動検証が未確定。CTX-02の適用ルールとCTX-08の完全インデックスで確定する。
- CTX-00で新規Unknown IDは追加していない。今回の7件の直接参照未検出は、未到達と断定せずCTXMAP-UNK-02へ集約した。

## 7. CTX-00受入チェック

- [x] 指定拡張子の管理対象を分類した
- [x] 境界ディレクトリの存在とGit ignore状態を確認した
- [x] ファイルごとのSHA-256一覧を保存した
- [x] 基準HEAD、ブランチ、origin、既存ユーザー変更を記録した
- [x] doc HTMLの導線をヒューリスティック確認した
- [x] 既存AI部品数と自動コミット監視状態を確認した
- [x] Unknownを既存統合台帳のIDへ接続した
- [x] 独立サブエージェント未完了をdispatch receiptへ記録した
- [ ] CTXMAP-H0承認（CTX-01の設計候補・High指摘・runtime fallback確認後に人間が判断）

CTX-01の設計候補作成まで完了した。次はCTXMAP-H0の人間確認であり、承認されるまでCTX-02のAI部品作成、実装、依存追加、MCP登録、監視変更へ進まない。
