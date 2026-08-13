# CTX-01 受入・脅威・テスト設計

- 対象文書: `CTXMAP-D01`
- 状態: `DESIGN_REVIEW_MATERIAL / 実装試験は未実施`
- 判定規則: `Critical` または `High` が未解決の間は、CTX-01を実装着手可にしない。

## 1. Findings first

|ID|重大度|対象|指摘・実装影響|修正・再確認条件|
|---|---|---|---|---|
|`CTXMAP-F-01`|High|`auto-commit.sh:9`|現行は`git add -A`であり、CTX-00基準線にもある既存未追跡ファイルをstageし得る。意図しない資料やSecret候補をcommitする事故につながる。やさしい説明: 関係ないメモまで一緒に箱へ入れて送ってしまう状態である。|CTX-07で、開始時snapshotとGateのallowlistだけを`git add --`する実装に置換し、既存未追跡物がstageされないGit index fixtureをPASSさせる。|
|`CTXMAP-F-02`|High|`CTXMAP-UNK-01`|JS/TS、PowerShell、shellの完全構文抽出に使える既存parserは未実測である。正規表現だけで`FULL`を名乗ると、importやexportを見落としてrelation graphが誤る。やさしい説明: 読めない言語を「全部読めた」と表示すると、必要な資料へたどれなくなる。|CTX-05で既存依存の実測fixtureを実行するまで`PARTIAL`を維持する。追加依存が必要なら名称・用途・ライセンスを提示し、取得せず停止する。|
|`CTXMAP-F-03`|High|A07/A08 runtime|OrchestratorとA82の明示起動はwait timeout、A91/A70/A80の再起動はスレッド上限または固定model制約となり、指定JSON定義どおりの独立完了receiptを閉じられなかった。やさしい説明: 点検係の材料は一部届いたが、全員の確認結果を同じ作業票で照合できていない。|`CTX-01_dispatch_receipt.json`へ実起動・timeout・部分材料・未受領を分離記録する。H0承認時も独立レビュー未完了を前提にし、CTX-02以降で同じfallback契約を満たす。|
|`CTXMAP-F-04`|High|A07/A08・MCP安全境界|文書本文のprompt injection、Secret検査順、MCPのTOCTOU・junction・symlink、返却前再hashの実装証跡がまだない。|モデル呼出し前のraw scan、ID先行、canonical root検証、読取前後hash一致、上限超過rejectをCTX-03/06でfixture化し、全件PASSまでcommitを許可しない。|
|`CTXMAP-F-05`|High|watcher・H1|H1未承認のwatcher拒否、単一worker、event ID、自己更新除外、retry上限が設計候補であり、現行watch経路への反映は未実施。|CTX-07/09でH1 receipt確認をstartとworker双方へ実装し、失敗時停止・再開条件を検証する。|
|`CTXMAP-F-06`|Medium|`CTXMAP-UNK-02`|evidence、巨大履歴、未追跡物の個別本文索引範囲が未確定である。|初期実装は境界recordだけとし、個別本文取得を拒否する。CTX-08でmanaged全件とのcoverageを再確認する。|

Criticalは0件、Highは5件が残る。従って本設計は実装完了・H1候補ではない。HighはH0の人間判断材料であり、H0承認後も各再確認条件を満たすまで実装品質のPassにしてはならない。

## 2. 受入基準

この表は、後続実装が何を満たせば設計契約を守ったと判断できるかを示す。

|ID|受入条件|機械的な確認方法|失敗時の扱い|
|---|---|---|---|
|`CTXMAP-AC-01`|managed対象はartifact/codeのどちらかに1対1で対応し、未分類を0件にする。|CTX-00の682件とfull validatorのpath集合・分類・countを比較する。|差分、重複、未分類のいずれかで非0終了する。|
|`CTXMAP-AC-02`|新規文書はA07の`record_add` receiptなしにcommitできない。|新規Markdown/HTML fixtureでA07 receipt欠落を検出する。|Gateがstage/commit前に停止する。|
|`CTXMAP-AC-03`|大幅文書変更はA07の明示判定を持つ。|見出し・ID・20%超・120行超のfixtureを実行する。|receiptのaction/hashが不正なら停止する。|
|`CTXMAP-AC-04`|コード構造変更はcode manifestとrelation graphの再解析を要求する。|export/import/function/class変更fixtureでstateを検査する。|stale hashまたは抽出結果欠落で停止する。|
|`CTXMAP-AC-05`|A08はmanifest先行で主資料を最大3件選ぶ。|固定routing fixtureで`primary_ids`と理由を検査する。|本文読取、4件以上、理由欠落を不合格とする。|
|`CTXMAP-AC-06`|MCPはstdio、repo境界、Secret拒否、文字数上限を守る。|negative security testとprocess listener検査を行う。|1件でも境界突破・過大返却なら停止する。|
|`CTXMAP-AC-07`|auto-commitは既存未追跡物を自動stageしない。|dirty worktree/index fixtureでstage集合を比較する。|indexが変われば不合格。commit/pushは実行しない。|
|`CTXMAP-AC-08`|初回全量manifestはmanaged対象100%を対象にする。|CTX-08 coverage reportとvalidatorを照合する。|`PARTIAL`/`blocked`/未分類を成功件数へ含めない。|
|`CTXMAP-AC-09`|AI部品・設定・AI基盤HTML・入口文書の名称とリンクが一致する。|CTX-02でJSON parse、完全名検索、リンク検証を行う。|不一致は同期未完了として停止する。|
|`CTXMAP-AC-10`|完成後の詳細解説HTMLが単独で運用を理解でき、doc/indexから到達する。|CTX-10でHTML/link/Mermaid/独立レビューを確認する。|到達不能、Critical/High残存は不合格。|

## 3. テスト設計

次の表は、実装後に省略してはいけない試験を入力fixture、操作、期待結果、合否基準まで固定する。CTX-01ではテストを作成・実行しない。

|テストID|種別|条件と操作|期待結果・合否基準|
|---|---|---|---|
|`CTXMAP-T-01`|unit|安全な新規Markdownを追加し、A07 stubが有効な`record_add`を返すfixtureを保守入口へ渡す。|artifact record、state、sanitized receiptが同じsource hashで作られ、validatorがPASSする。本文全量がreceiptにないことを確認する。|
|`CTXMAP-T-02`|unit|新規HTMLを追加し、title、h1-h3、ローカルリンク、REQを含むfixtureを処理する。|構造抽出とA07 record_addが一致し、local link relationが作られる。外部URL本文を取得しない。|
|`CTXMAP-T-03`|unit|文書の句読点だけを変更し、20%・120行・構造変更未満にする。|A07を起動せず、stateのhashと小変更根拠だけを更新する。summaryとpurposeを勝手に変更しない。|
|`CTXMAP-T-04`|unit|title、h2、REQを変更するfixtureを処理する。|大幅変更としてA07が必ず起動し、`record_update`または`metadata_unchanged`と理由を返す。|
|`CTXMAP-T-05`|unit|正規化本文を20%超、または120行超変更するfixtureを処理する。|閾値判定が安全側でmajorとなり、A07 receiptなしではvalidatorがFAILする。|
|`CTXMAP-T-06`|unit|Python function、class、importを追加・削除・renameするfixtureを処理する。|標準ASTのsymbols/imports/line rangeが更新され、構造変更ならcode stateがstaleにならない。|
|`CTXMAP-T-07`|unit|Python syntax error fixtureを処理する。|例外で落ちず`PARTIAL`または`blocked`とlimitationsを返す。`FULL`を返さない。|
|`CTXMAP-T-08`|unit|JS/TS export/import、PowerShell function、shell function/source、cmd label/callのfixtureを処理する。|実測できた範囲だけを出力し、未保証要素は`PARTIAL`とする。追加parserを自動取得しない。|
|`CTXMAP-T-09`|unit|JSON/YAML/TOMLにSecretらしきkeyを含むfixtureを処理する。|値をmanifestへ書かず、policyに従い`blocked`または安全なkey名のみの結果を返す。|
|`CTXMAP-T-10`|integration|同一hashの文書を一対一renameするbefore/after fixtureを処理する。|旧artifact_idを維持し、path historyとrename relationが残る。relation IDを破棄しない。|
|`CTXMAP-T-11`|negative|一対多rename、同内容の重複、hash不一致rename候補を処理する。|自動同一視せず`rename_ambiguous`で停止する。誤った旧IDを割り当てない。|
|`CTXMAP-T-12`|integration|登録済み文書・コードを削除するfixtureを処理する。|recordはtombstoneへ移り、last hash/pathを保持し、edgeはinactiveとなる。物理削除しない。|
|`CTXMAP-T-13`|negative|schemaを壊したmanifest、重複ID、孤立relation、stale source hashをvalidatorへ渡す。|それぞれ非0で停止し、Gateはstage/commit/pushを開始しない。|
|`CTXMAP-T-14`|negative|A07未起動、timeout、strict JSON違反、confidence不足、18,001文字の入力を与える。|`blocked` receiptだけが作られ、new/major文書はvalidator FAILとなる。代替Agentや手書きPassを許さない。|
|`CTXMAP-T-15`|integration|A08に同じrouting fixtureを複数回渡す。|primary 1〜3、supporting 0〜6、理由、JIT予算が決定的に一致する。本文読み込みがない。|
|`CTXMAP-T-16`|negative|MCPへ`../../`、`C:\\`、UNC、symlink escape、未知ID、存在しないsymbolを渡す。|固定拒否codeを返し、repo外を読まず、絶対pathを返さない。|
|`CTXMAP-T-17`|negative|MCPへ`.env`、秘密鍵名、prompt injection文字列、12,001文字要求、巨大range、無効UTF-8を渡す。|内容非表示で拒否または安全な縮約を行い、stdio以外のlistenerを開かない。|
|`CTXMAP-T-18`|regression|CTX-00の固定path/hash一覧を入力にfull indexを二回実行する。|順序、ID、hash、relationの直列化が一致する。差異はtest failureとする。|
|`CTXMAP-T-19`|regression|新規文書、大幅変更、コード構造変更、rename、削除を順に適用する。|各transactionがreceipt/state/manifestを整合させ、後続validatorがPASSする。|
|`CTXMAP-T-20`|mutation相当|validatorのSecret check、source hash照合、new/major receipt要求、path confinement、limit checkを各1箇所だけ意図的に無効化したmutantを試験する。|対応する負例が必ずFAILとなる。mutantが生き残る場合は試験不足として不合格。|
|`CTXMAP-T-21`|integration|watch開始前のdirty worktreeに既存未追跡物・手動stage済み変更を置き、event由来の新規managed文書を加える。|H1前はwatch startを拒否する。H1後のfixtureでは既存未追跡物・既存indexを変更せず、allowlistだけがstage候補になる。|
|`CTXMAP-T-22`|negative|validator failure、Secret疑い、A07 timeout、source staleの各状態でcommit経路を呼ぶ。|`git add`、commit、pushを一切実行せず、index/worktreeが開始時と同じである。|
|`CTXMAP-T-23`|integration|manifest自身の更新と同一hashのイベントを連続投入する。|単一worker、debounce、transaction IDにより1回だけ処理され、自己更新ループと無限retryが発生しない。|
|`CTXMAP-T-24`|performance/negative|policy上限を超える巨大文書・巨大code・多数relationを渡す。|処理時間・文字数・メモリ上限の前に安全停止し、部分本文やSecretらしき内容を保存しない。|

## 4. Agent担当、依存、受領条件

|担当|依存する入力|独立して返すべき材料|受領条件|
|---|---|---|---|
|`AutoTrade_A82_ImplementationDetailDesigner_v0_1`|CTX-00、計画、既存Git/auto-commit、schema候補|モジュール、型付き契約、永続化、順序、例外、テスト、追跡表|すべての必須設計9項目に対応し、UnknownをPassにしない。|
|`AutoTrade_A91_ImplementationDetailReviewer_v0_1`|A82案、詳細設計skill、受入表|Findings first、構成充足、Critical/High、再レビュー条件|各findingに対象・ID・実装影響・修正条件がある。|
|`AutoTrade_A70_OpsSecurityArchitect_v0_1`|MCP/A07/A08/監視/commit境界|脅威モデル、Secret/監査/fail-closed/復旧設計|prompt injection、path traversal、Secret、巨大ファイル、監視loop、誤stageを全て判定する。|
|`AutoTrade_A80_DocumentIntegrator_v0_1`|承認済み設計・review|成果物配置、追跡リンク、改訂履歴|CTX-01ではMarkdown候補のみ。正式HTMLとdoc/index更新はCTX-10以降でありN/A。|

依存順序は `A82設計 → A91/A70独立レビュー → A82改訂 → A91再レビュー → A80統合` とする。ただし本runでは指定Orchestrator/A82の明示起動がtimeoutとなり、A91/A70/A80の再起動は制約により完了しなかった。関連subagentから材料は到着したが、指定JSON定義どおりの独立closed-loop receiptとしては受領していない。root自己レビューはこの表の観点を用いた代替であり、独立レビューの代わりではない。

## 5. Dispatch fallback証跡と次の停止条件

必須backendの`multi_agent_v1__spawn_agent`と`multi_agent_v1__wait_agent`は利用できたが、指定Orchestrator/A82のwait timeout、A91/A70/A80の再起動制約、固定model gpt-5.1の利用不可が発生した。そのため`RUNTIME_DISPATCH_FALLBACK_REQUIRED`とし、実起動ID、timeout、部分材料、未受領Agent、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK`をreceiptへ分離記録した。

次に進むための順序は以下のとおりである。

1. 人がHigh 5件、`CTXMAP-UNK-01/02`、A82/A91/A70/A80の独立closed-loop未完了を含めて設計候補を確認する。
2. ユーザーが`CTXMAP-H0を承認します`と明示した場合だけCTX-02へ進む。
3. H0後も追加依存、外部通信、Secret、監視起動は別の停止条件であり、自動的に許可されない。
