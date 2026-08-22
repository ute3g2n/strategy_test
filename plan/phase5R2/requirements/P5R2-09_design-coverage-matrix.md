# P5R2-09 詳細設計書セット coverage matrix

状態: `DESIGN_COMPLETE / P5R2-H1_APPROVED_BY_DELEGATED_AUTHORITY / LOCAL_IMPLEMENTATION_EVIDENCE_AVAILABLE`。作成時点のH1未承認という履歴はP5R2-09ログへ保持する。これは設計coverageの現在同期であり、P5R2-13〜22の実装・試験・Manual Evidenceへの入口を示す。P5Rの既存Evidence/Test/Manualは履歴参照だけであり、P5R2の合否証拠へ昇格しない。

| atomic Requirement | 下位Requirement | 主設計書 | 実装前に固定する契約 | Test雛形の責務 | Gate / Unknown |
|---|---|---|---|---|---|
| P5R2-CREQ-TF-001 | TF-001, TF-004 | 01 | 5戦略足、UTC anchor、closed bar、有効終了 | 選択肢、1m拒否、30m、partial拒否 | H1承認済み、P5R2-13 local GREEN |
| P5R2-CREQ-TF-002 | TF-002, TF-005, TF-006 | 01, 02, 05 | 1m source/derived分離、補間、生成遷移 | 補間の正負例、生成入力引継ぎ | H1判断済み、P5R2-13／14／22 local、H2 review |
| P5R2-CREQ-TF-003 | TF-003, TF-004 | 01, 04, 05 | legacyを閲覧専用に分離 | legacyを新規Runへ渡さない | H1承認済み、P5R2-16／22 local |
| P5R2-CREQ-HD-001 | HD-001, HD-002 | 02, 04, 05 | Download/Generationの別ID・別状態 | Gate前無通信、Job/DataSet分離 | H1承認済み、DATA-G1 bounded／External blocked |
| P5R2-CREQ-HD-002 | HD-003～HD-007 | 02, 04, 05 | identity、coverage、quality、promotion | dedupe/conflict/merge/replace/recovery | H1判断済み、P5R2-14／16／22 local、H2 review |
| P5R2-CREQ-RUN-001 | RUN-001, RUN-002 | 03, 04, 05 | 3画面共通cancel、OperationGuard、terminal不変 | 二重押下、再送、別tab、再起動 | H1承認済み、P5R2-15／16／19 local |
| P5R2-CREQ-RUN-002 | RUN-003, RUN-004 | 03, 04, 05 | Artifact状態、論理ID、安全な許可root | traversal/symlink/reparse/TOCTOU/CSV保護 | H1承認済み、DELETE-G1 bounded／P5R2-21 local |
| P5R2-CREQ-DOC-001 | AUDIT-001, DOC-001, GATE-001 | 05（横断01～04） | DTO、dialog、a11y、Manual/Evidence registry | UI/Manualの未実証拒否 | H1承認済み、P5R2-22 local candidate、H2 review |

## 設計判断とUnknown

| ID | 内容 | 掲載先 | 状態 |
|---|---|---|---|
| DD-01 | 新規strategy timeframeは5種類、1mはsourceだけ | 01, 05 | 設計契約 |
| DD-02 | UTC anchorとclosed barをRun前提にする | 01 | 設計契約 |
| DD-03 | DownloadとGenerationは同一基盤を使っても別Job | 02 | 設計契約 |
| DD-04 | DataSetは検証・promotion後だけusable | 02, 04 | 設計契約 |
| DD-05 | cancelはRun専用OperationGuardで直列化する | 03 | 設計契約 |
| DD-06 | terminal cancelは状態不変で監査する | 03 | 設計契約 |
| DD-07 | 削除入力は論理Artifact IDだけ | 03, 04 | 設計契約 |
| DD-08 | DELETE-G1前は物理削除をfail-closedにする | 03, 04 | Gate待ち |
| DD-09 | SQLite/file操作はintent→commit→recoveryで扱う | 04 | 設計契約 |
| DD-10 | legacyは読取専用、暗黙移行しない | 01, 04, 05 | 設計契約 |
| DD-11 | UIはDTO/error codeで画面差をなくす | 05 | 設計契約 |
| DD-12 | ManualはP5R2-22で実証済み操作だけ更新する | 05 | Gate待ち |
| P5R2-UNK-TF-004 | H1で確定した補間候補のAPI/Persistence/negative testへの写像 | 01, 02 | P5R2-13 local Evidence済み。候補外Dataをusable/Run入力へしない。H2で残Unknown扱いを確認 |
| P5R2-UNK-TF-006 | H1で確定した「現在生成可能な全期間」の算出規則 | 01, 02, 05 | P5R2-13／14／22 local Evidence済み。sourceなしの既定期間を表示・実装しない。H2で残Unknown扱いを確認 |
| P5R2-UNK-QG-001 | P5R2 Quality namespaceと固定入口 | 05 | P5R2-12／18 local Evidenceで解消。External Runのhost-level isolationへ読み替えない |
| P5R2-UNK-QG-002 | fixtureと保護境界 | 04, 05 | P5R2-12／18でread-only確認済み。管理目的の同一性照合経路を新設しない |

## 非管理値確認

- path: 新規HTMLは `doc/phase5R2/04_実装詳細設計/`、補助成果物は `plan/phase5R2/` に限定する。
- schema: HTMLはUTF-8、local Mermaid asset参照、文書ID・状態・入力・追跡・レビューを持つ。
- link: `doc/index.html` と5冊の相互リンクを更新する。
- Secret: Secret、実Provider認証値、口座情報、実Dataは含めない。
- 状態: H1/DATA-G1/DELETE-G1/H2を未承認のまま保持する。
- A95静的判定: 管理目的の同一性照合経路を追加していないため `ALLOW`（候補なし）。
+
## P5R2-10 レビュー・改訂・再レビュー（2026-08-22）

初回レビューはFindings firstで実施し、次のHighを改訂した。P5R2-H1は未承認のままであり、本記録は実装、RED/GREEN、品質Run、外部I/O、実削除のEvidenceではない。

| Finding ID | 初回重要度 | 対象 / 節 | 事故シナリオ | 改訂 | 受入Evidence |
|---|---|---|---|---|---|
| P5R2-10-H-001 | High | 5冊 / AF-D16 0、13〜22 | 実装者が型、依存、例外、Run Manifest、Gate、レビュー根拠を推測し、Gate外の実装を始める。 | 各冊を0〜22の完全構成へ改訂し、N/A理由・確認者・代替リンクを16章へ記載した。 | 各HTMLのh2 0〜22、21章の改訂履歴。 |
| P5R2-10-H-002 | High | 5冊 / 6章 | 試験条件・操作・合格条件が一体で、抜けた負例や誤った合格判定が検出できない。 | 全テスト表をID、概要、条件、操作、期待結果、合否基準の6列・日本語文章へ改訂した。 | 各HTML 6章の6列テスト表。 |
| P5R2-10-H-003 | High | D03/D04 / 11、16、18章 | ResultArtifact削除にpath差替え、traversal、symlink/reparse、TOCTOU、別IDを使い、保護対象を誤って消す。 | 論理IDだけを入力にし、DELETE-G1前の物理I/O停止、全path攻撃拒否、CSV/Data/Run/Audit/Evidence保護を明記した。 | D03 RUN-06、D04 PS-05/PS-06、エラー表。 |
| P5R2-10-H-004 | High | D02 / 6、14、18、19章 | 同一identityの後続期間mergeを、過去Run結果が変わり得るという誤った理由で禁止し、正しいdata_version追加も不能になる。 | 非重複期間は明示MERGEで既存版を消さず新data_versionとして追加、完全一致はdedupe、異値は明示replaceなしで停止とした。 | D02 HD-04〜HD-06、18章、Run Manifest/data_version契約。 |
| P5R2-10-M-001 | Medium | 5冊 / 3、7〜19章 | 表の目的が曖昧で、確認者が判断すべき停止条件を読み飛ばす。 | 各仕様表の直前へ目的と判断事項の文章を追加した。 | 各HTML 3〜19章の表前段落。 |
| P5R2-10-M-002 | Medium | D01/D02/D05 / 14、19章 | UTC/closed/partial/補間候補とTF-004、全期間defaultとTF-006を混同してUnknownをPassにする。 | TF-004/006を別行にし、未決時はusable昇格、default表示・送信、Run入力を停止することを固定した。 | D01 TF-04/TF-05、D02/D05 14章。 |

### AF-D16 再レビュー充足表

| 確認項目 | 01 | 02 | 03 | 04 | 05 | 再レビュー |
|---|---|---|---|---|---|---|
| 0〜22構成、N/A理由・確認者・代替リンク | Pass | Pass | Pass | Pass | Pass | Pass |
| 平易な概要、file tree、Mermaid構造図、矢印名、直後の受渡し表 | Pass | Pass | Pass | Pass | Pass | Pass |
| 型付きAPI、永続化schema、transaction/sequence、例外、recovery | Pass | Pass | Pass | Pass | Pass | Pass |
| 全テストの6列日本語文章、Run Manifest/data_version、Secret/Human Gate | Pass | Pass | Pass | Pass | Pass | Pass |
| P5R旧Test/Evidence/ManualをP5R2合否へ昇格しない | Pass | Pass | Pass | Pass | Pass | Pass |
| 管理目的の同一性照合経路を追加しない | Pass | Pass | Pass | Pass | Pass | Pass |

再レビュー判定: `Critical=0 / High=0 / Medium=0 / Low=0`。P5R2-UNK-TF-004／006はH1判断とlocal Evidenceを得たが、H2で残Unknownとしての扱いを最終確認する。P5R2-UNK-QG-001／002はlocal scopeでは解消済みで、P5R2-UNK-QG-003（External host-level isolation）、DATA-G1外部受入、DELETE-G1のbounded範囲外、H2はOpenのままであり、Passとは扱わない。
