# 要件定義書 v3 作成・Phase 5R ロードマップ再編 実行計画書

- 文書ID: `RQV3-PLAN-001`
- 作成日: 2026-08-16（Asia/Tokyo）
- 状態: `STEP1_PROMPT_GROUP_CREATED / STEP2_COMPLETED`
- 対象: `doc/requirements/01_自動トレードシステム要件定義書_v3.html`
- 旧版: `doc/requirements/01_自動トレードシステム要件定義書_v2.html`（履歴として保持し、上書きしない）
- 根拠: `plan/Phase5R_バックテスト製品完全化_再構成提案・実行計画書_v0.1_2026-08-16.md`

## 0. この計画で決めること

この計画は、要件定義書 v2 の内容を失わずに v3 を作り、次の方針を正式な要件上の順序として記録するためのものである。

1. Phase 5 の直後に **Phase 5R** を置く。Phase 5R は、UIから実行でき、実データ・実計算・異常時・履歴・比較まで確認できるローカルBacktest製品を完成させる。
2. Phase 5R に入れる「多数の実験をまとめて扱う機能」は、Backtest Experiment Set / Sweepである。複数の運用Unit、Portfolio、実運用Risk、OMS、注文、実口座は入れない。
3. Phase 6以降は、能力を安全な順番で一つずつ積み上げる。完成順は、**Forward Test → Shadow → Paper → Live候補 → 小規模Live → 通常Live** とする。
4. 各能力を必ず1 Phaseで終えるとは限らない。特にForward Testは、P6で安全な運用土台を完成させ、P7で実時間・仮想のForward Testを完成させる二段階とする。
5. 小規模Liveより前に外部注文や実資金を使わない。Live候補は「実注文できる状態」ではなく、実注文前の最終確認状態である。

> 中学生向けの説明: Backtestは「過去問を解く練習」、Forwardは「今日からの問題を、本物のお金なしで毎日解く練習」、Shadowは「本番候補と同じ答えを出すか横で観察する練習」、Paperは「おもちゃのお金の家計簿で運用する練習」である。小規模Liveは、いきなり大金を使わず、決めた少額だけで安全装置を確認する段階である。

## 1. 完成物と変更範囲

| 種別 | パス | この計画での扱い |
|---|---|---|
| 新しい正式要件 | `doc/requirements/01_自動トレードシステム要件定義書_v3.html` | 作成する。v2の既存要件IDは保持し、v3の変更・追加を明記する |
| 旧要件 | `doc/requirements/01_自動トレードシステム要件定義書_v2.html` | 変更しない。履歴・根拠として保存する |
| HTML入口 | `doc/index.html` | v3を現行要件として追加し、v2を履歴として表示する |
| 現在状態の正本 | `doc/00_全Phase残課題Blocked統合台帳.html` | P5RがP6の前にあること、P5のOpen UnknownがP5R・P6以降へ引き継がれることを更新する |
| P5からの引渡し | `plan/phase5/Phase6計画入力一覧_2026-08-12.md` | P6へ直接開始する入力ではなく、P5Rを経由してP6へ渡す履歴入力であることを注記する |
| 実行プロンプト群 | この計画書 | Step 1として先に作成し、Step 2で下から順に一つずつ実行する |

### 1.1 対象外

- P5Rの実装、外部市場Dataの追加取得、Broker接続、Secret投入、Paper実行、実注文、実資金、Cloud、DB migrationは行わない。
- P5で残っているProvider条件、外部Runのhost isolation、実行費、子Agent起動のUnknownを解消済みと表示しない。
- v2の既存要件ID、旧証拠、完了判定を削除しない。
- 実Liveの開始承認を、この文書作成だけで行わない。

## 2. v3で採用するロードマップ

| Phase | 完成させる能力 | 完了と呼べる条件 | 代表的な禁止事項 |
|---|---|---|---|
| P4 | 固定ローカルの製品土台 | 既存完了記録の範囲 | 実市場のBacktest完成と誤認しない |
| P5 | 限定市場Dataの品質・期間分割 | 既存P5完了記録の範囲 | Open UnknownをPass化しない |
| **P5R** | UIから使うBacktest製品 | 実データでのRun / Sweep / 5指標 / 中止・再開 / 履歴・比較 / CSV / Holdout / Walk-forwardが受入済み | 運用Unit、Portfolio、実運用Risk、OMS、Forward、Shadow、Paper、Broker、Liveを混ぜない |
| **P6** | Forwardの安全な共通土台 | 複数運用Unit、Portfolio、Risk、OMS、仮想注文状態、停止・照合・復旧を固定Simulationで受入済み | 外部注文、実口座、実資金、実時間Forwardの完成宣言 |
| **P7** | Forward Test（実時間・仮想） | 実時間Dataの確定足で仮想Signal / Fill / Positionを継続記録し、外部Orderが0件であることを受入済み | Shadow、Paper、実口座、実注文への自動昇格 |
| **P8** | Shadow（本番候補の複製・注文なし） | 本番候補と同じ設定の複製を実時間で観察し、差分・遅延・停止を説明でき、外部Orderが0件であることを受入済み | 実注文、実口座変更、Shadow結果だけでのLive承認 |
| **P9** | Paper（仮想口座・仮想Ledger） | 仮想Account / Ledger / Order / Fill / Positionが再現でき、外部Orderが0件であることを受入済み | Broker注文、実資金、Paper完了だけでのLive昇格 |
| **P10** | Live候補（実注文前の最終確認） | Candidate、Risk、Data、Account照合、Kill、監査、運用手順、未達が明示され、実注文経路が無効であることを受入済み | 実注文、実資金、無承認のSecret利用 |
| **P11** | 小規模Live（限定実資金） | 個別Human Gate、限定Account / Unit / 銘柄 / 上限 / 期間でのみ実注文し、照合・停止・復旧の実証を完了 | 範囲外拡大、自動昇格、限度を超える注文 |
| **P12** | 通常Live | P11の実績、再承認済み範囲、監視・Kill・照合・復旧・監査の継続受入を満たす | 「通常」を無制限・無監視と解釈すること |

## 3. Step 1 — そのまま実行する詳細プロンプト群

以下の各ブロックが、順番に一つずつ実行するプロンプトである。各Stepは前Stepの成果物を入力にし、未承認の外部操作を行わない。各Stepは開始前に指定CoordinatorとAgentの起動・待機を試み、利用不能時は `RUNTIME_DISPATCH_FALLBACK_REQUIRED`、未起動Agent、`agent_id=N/A`、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK` を成果物に残す。名前を読んだだけで独立レビュー済みと書いてはならない。

### Step V3-01 — 入力を固定し、変更対象を追跡する

~~~text
Phase ID: REQUIREMENTS-V3
Step: V3-01
目的: v2、P5R提案、P5引渡し、統合台帳から、v3で継承する事実・変更する事実・未確定の事実を混ぜずに整理する。

使用するAI部品:
- Orchestrator: AutoTradePhasePlanning_Orchestrator_v0_1（.codex/orchestrators/AutoTradePhasePlanning_Orchestrator_v0_1.json、model=gpt-5.6-terra）
- Agents: AutoTrade_A05_PhaseExecutionPlanner_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
- Skills: autotrade_skill_phase_execution_planning_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1

開始時の必須動作:
1. multi_agent_v1__spawn_agent / multi_agent_v1__wait_agent の利用可否を確認する。
2. Coordinatorを固定modelで実起動し、Coordinatorに上記4 Agentを各JSONの固定modelで起動・待機するよう依頼する。
3. できない場合は、未起動のAgent名、理由、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを先に記録する。

入力:
- doc/requirements/01_自動トレードシステム要件定義書_v2.html
- plan/Phase5R_バックテスト製品完全化_再構成提案・実行計画書_v0.1_2026-08-16.md
- plan/phase5/Phase6計画入力一覧_2026-08-12.md
- doc/phase5/06_完了/08_Phase5完了判定・Phase6計画引渡し.html
- doc/00_全Phase残課題Blocked統合台帳.html

実施:
1. REQ-V2-0044〜0055をP5Rへ、REQ-V2-0056〜0065をP6以降へ、REQ-V2-0066〜0079をP6の土台と後続Liveに分けて整理する。
2. 「Backtest Experiment Set / Sweep」と「継続運用Unit」を別の用語・別の責務として定義する。
3. P5のOpen Unknownと停止条件を一覧化し、どのPhaseで解消候補にするかを記す。ただし根拠なしに解決済みにしない。
4. v2の全既存REQ IDを保持し、v3で新設するIDが重複しないよう番号帯を決める。

成果物:
- この計画書の「Step 2 実行記録」に、入力要約、追跡マトリクス、Unknown一覧、受領記録を追記する。

完了条件:
- v3に必要な根拠、既存ID、P5R境界、Open Unknown、更新対象ファイルが表で追える。
- UnknownをPassと記載しない。
- 管理目的の照合経路を新設しない。
~~~

### Step V3-02 — P5RとP6〜P12の能力順序を要件化する

~~~text
Phase ID: REQUIREMENTS-V3
Step: V3-02
目的: P5Rを正式に挿入し、Forward→Shadow→Paper→Live候補→小規模Live→通常Liveの順序、各Phaseの開始・完了・禁止事項・Human Gateを決める。

使用するAI部品:
- Orchestrator: AutoTradePhasePlanning_Orchestrator_v0_1（model=gpt-5.6-terra）
- Agents: AutoTrade_A05_PhaseExecutionPlanner_v0_1、AutoTrade_A20_ArchitectureDomainArchitect_v0_1、AutoTrade_A70_OpsSecurityArchitect_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
- Skills: autotrade_skill_phase_execution_planning_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1

開始時の必須動作:
- Step V3-01と同じ実ランタイム起動・待機・Fallback開示を行う。Coordinatorと各AgentのJSON path、固定model、agent_id、受付・完了状態、出力参照、independent、review_modeを記録する。

入力:
- V3-01の入力要約・追跡表
- P5R再構成提案のP5R対象/P6残置表
- v2の章23〜30、62.5の旧ロードマップ

実施:
1. P5Rに含めるBacktestの完成条件を、UI、実計算、Data範囲、異常、保存、比較、CSV、Walk-forward、受入テストで定義する。
2. P6は「Forwardを可能にする安全な共通土台」、P7は「実時間・仮想Forwardの完成」とし、P6とP7の境界を明記する。
3. P8 Shadow、P9 Paper、P10 Live候補、P11 小規模Live、P12 通常Liveについて、前の能力を飛ばせない昇格条件と停止条件を定義する。
4. P10までは外部Orderを送らない。P11だけが限定実資金を扱えるPhaseであり、P12は再承認された範囲だけを扱う、と明記する。
5. 既存REQ-V2-0056〜0079の意味を削らず、v3の対象Phaseと現実装状態を更新する。

成果物:
- この計画書の「Step 2 実行記録」に、v3ロードマップ、昇格Gate表、各Phaseの非対象、High/Criticalリスクを追記する。

完了条件:
- P5Rに運用Unit/Portfolio/実Risk/OMSを混ぜていない。
- P6以降の能力順序、各Human Gate、実注文が許される最初の地点が一意である。
- 実Liveへの自動昇格がない。
~~~

### Step V3-03 — v3 HTMLの改訂方針と追跡表を作る

~~~text
Phase ID: REQUIREMENTS-V3
Step: V3-03
目的: v2を履歴として保持したまま、v3をどの章・要求・状態・変更履歴で構成するかを確定する。

使用するAI部品:
- Orchestrator: AutoTradePhasePlanning_Orchestrator_v0_1（model=gpt-5.6-terra）
- Agents: AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
- Skills: autotrade_skill_source_reader_v0_1、autotrade_skill_html_doc_writer_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1

開始時の必須動作:
- Step V3-01と同じ実ランタイム起動・待機・Fallback開示を行う。

入力:
- v2の全章、REQ-V2-0001〜0112、UC/Q/Screen/State/図表の対応
- V3-01の追跡表
- V3-02のロードマップとGate表

実施:
1. v3はv2の既存要件・図表・履歴を継承し、新たな要件はREQ-V3-0113以降で追加する方針を確定する。
2. v2の章19〜22、23〜30、62.5を、v3のP5RとP6〜P12の正本に置き換えるか、v3の改訂章で明示的に上書きするかを決める。矛盾する旧記述をそのまま有効に残さない。
3. 文書情報、v2との関係、現在状態、変更理由、採否表、残課題、レビュー履歴、参照先を含むHTML構造を設計する。
4. doc/index.html、統合台帳、P6引渡し入力に必要な最小更新を確定する。

成果物:
- この計画書の「Step 2 実行記録」に、v3章構成、REQ-V3一覧、変更採否表、更新ファイル一覧を追記する。

完了条件:
- v3が単独で「今どのPhaseが次か」「何を完成と呼ぶか」「何が禁止か」を読める構造になっている。
- 旧REQ IDの追跡が失われない。
~~~

### Step V3-04 — v3と関連する正式導線を作成する

~~~text
Phase ID: REQUIREMENTS-V3
Step: V3-04
目的: 承認済みのv3改訂方針を、正式HTMLと最小限の関連導線へ反映する。

使用するAI部品:
- Orchestrator: AutoTradePhasePlanning_Orchestrator_v0_1（model=gpt-5.6-terra）
- Agents: AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
- Skills: autotrade_skill_html_doc_writer_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1

開始時の必須動作:
- Step V3-01と同じ実ランタイム起動・待機・Fallback開示を行う。

実施:
1. doc/requirements/01_自動トレードシステム要件定義書_v3.html を作成する。v2を履歴として残し、既存要件IDを削除しない。
2. 文書の冒頭に、v3の正本性、v2との関係、P5R採用、P6〜P12ロードマップ、禁止事項を記載する。
3. P5RではREQ-V2-0044〜0055の完成条件と現在状態を更新する。P6以降では既存REQ-V2-0056〜0079の対象Phaseと境界を更新し、必要なREQ-V3を追加する。
4. 各Phaseに、目的、対象、完了条件、開始Gate、停止条件、後続への引渡し、やさしい説明を記載する。
5. doc/index.htmlを更新し、v3を現行、v2を履歴としてリンクする。
6. 統合台帳へ、P5Rが次の正式計画対象であること、P5のOpen UnknownをPass化していないこと、P6の正式開始はP5R後であることを反映する。
7. P6引渡し入力に、P5Rを経由することとP6直接開始の禁止を注記する。P5の完了事実は改変しない。

禁止:
- 外部I/O、Secret、Broker、Paper、Live、実資金の実行を開始しない。
- P5R-H0を承認済みと書かない。
- P5のOpen Unknownを解決済みと書かない。

成果物:
- doc/requirements/01_自動トレードシステム要件定義書_v3.html
- doc/index.htmlの更新
- doc/00_全Phase残課題Blocked統合台帳.htmlの最小更新
- plan/phase5/Phase6計画入力一覧_2026-08-12.mdの最小注記

完了条件:
- v3のリンク・ID・現在状態・ロードマップが相互に矛盾しない。
- v3からP5RとP6〜P12の境界を誰でも追える。
~~~

### Step V3-05 — Findings firstの設計レビューと改訂を行う

~~~text
Phase ID: REQUIREMENTS-V3
Step: V3-05
目的: v3のロードマップ、要件ID、昇格Gate、Human Gate、Live安全境界に矛盾や危険な飛び越えがないかを確認し、必要な修正を反映する。

使用するAI部品:
- Orchestrator: AutoTradePhasePlanning_Orchestrator_v0_1（model=gpt-5.6-terra）
- Agents: AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A70_OpsSecurityArchitect_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
- Skills: autotrade_skill_design_review_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1

開始時の必須動作:
- Step V3-01と同じ実ランタイム起動・待機・Fallback開示を行う。

確認項目:
1. P5RがBacktest Experiment Set / Sweepだけを扱い、継続運用Unitを扱わないこと。
2. P6〜P7でForwardを完成させる説明が一貫し、P7以前に実時間Forward完成と表示していないこと。
3. P8 Shadow、P9 Paper、P10 Live候補、P11小規模Live、P12通常Liveの順序を飛ばせないこと。
4. P10まで外部Orderが0件であり、P11だけが限定実資金を扱うこと。
5. 外部注文、Secret、Account、費用、実資金、Data Providerの各Gateが別の承認として残っていること。
6. REQ-V2/REQ-V3、UC、Screen、State、Test、Evidence、Unknown、Phaseの追跡が切れていないこと。
7. P5のUnknown、High/Critical、P5R-H0の未承認を隠していないこと。

成果物:
- この計画書の「Step 2 実行記録」に、Finding、重要度、採否、修正、残リスクを追記する。
- 必要な修正をv3と関連導線へ反映する。

完了条件:
- Critical/Highが0、または残る場合はv3を完成扱いにせず停止理由と再開条件を明記する。
- Findingsを先に記録し、まとめだけで終えない。
~~~

### Step V3-06 — 静的確認、受入確認、最終化を行う

~~~text
Phase ID: REQUIREMENTS-V3
Step: V3-06
目的: 新規HTML・更新した関連文書について、パス、HTML構造、リンク、Secret、状態、追跡、保護対象以外の管理用照合経路の非導入を確認し、v3を完成させる。

使用するAI部品:
- Orchestrator: AutoTradePhasePlanning_Orchestrator_v0_1（model=gpt-5.6-terra）
- Agents: AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
- Skills: autotrade_skill_html_doc_writer_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1

開始時の必須動作:
- Step V3-01と同じ実ランタイム起動・待機・Fallback開示を行う。

検証:
1. v3がUTF-8 HTMLであり、doctype、title、main、見出し、文書情報、状態、入力、判断、Unknown、変更履歴、レビュー履歴を持つこと。
2. doc/index.htmlからv3へ到達でき、v2が履歴として残ること。
3. v3、統合台帳、P6入力のP5R / P6 / P7〜P12の現在状態と次Phaseが一致すること。
4. ローカルリンクが存在し、外部URLを新設していないこと。
5. Secretらしい値が文書に含まれないこと。
6. A95相当の静的ポリシー確認がALLOWであること。用途不明の保護対象はHuman Gateへ送る。
7. git diff --checkを通すこと。今回変更したファイルだけをstageし、差分を確認してからコミット・追跡先へのpushを試行する。

停止:
- Critical/High未解決、リンク欠落、状態矛盾、Secret疑い、UnknownのPass化、無承認の外部操作、A95のBLOCKEDを検出した場合。

成果物:
- この計画書の「Step 2 実行記録」に、検証コマンド、結果、受領記録、コミット/Push結果を追記する。

完了条件:
- v3が現行要件として単独で読め、P5Rから通常Liveまでの順序と安全境界を誤解なく説明できる。
~~~

## 4. Step 2 — プロンプト群の実行記録

この節は、上のStep V3-01からV3-06を一つずつ実行した事実だけを追記する。未実行のStepを完了扱いにしない。

### V3-01 実行記録

**状態: `COMPLETED_WITH_CHILD_DISPATCH_FALLBACK`**

#### 入力から確認した事実

| 区分 | v3へ持ち込む事実 | v3での扱い |
|---|---|---|
| P5完了 | `P5-11_COMPLETE_WITH_OPEN_UNKNOWN`。限定対象はBTCUSDT / ETHUSDT、Spot、1m、UTC、`CRYPTO_24_7_UTC` | P5Rは既存ローカルDataだけを入力にできる。対象を自動拡大しない |
| P5の未解決事項 | Providerの利用・保持・再配布条件、外部取得Runのhost isolation、P5 child Agent未起動、fee / slippage / 内部実行費未測定 | `OPEN_NOT_PASS`のままP5R・P6以降へ引き継ぐ。追加取得や実取引の許可とはしない |
| Backtest | `REQ-V2-0044`〜`REQ-V2-0055`は単一Run、Sweep、5指標、停止・再開、履歴、比較、CSV、Holdout、Walk-forwardを要求する | P5Rの完了対象へ再配置する。固定Coreや固定UI表示だけで完了とはしない |
| Backtest専用の束 | Sweepは「独立した過去実験を多数行う束」である | P5Rに含める。実資金・共有Portfolio・実注文は持たない |
| 継続運用Unit | `REQ-V2-0036`〜`0043`、`0066`〜`0079`は複数Unit、資源、Portfolio、Account、Risk、OMS、競合、照合、Killを扱う | P6に残す。P5Rへ前倒ししない |
| 実行Mode | `REQ-V2-0056`〜`0065`はForward、Shadow、Paper、Live候補、小規模Live、通常Liveの副作用境界と昇格を定義する | v3でP6〜P12の能力順とGateを明示する |

#### 既存IDの継承・上書き方針

| ID群 | v3での扱い | 主な対象Phase |
|---|---|---|
| `REQ-V2-0001`〜`0035` | 継続。文書、Data、Strategy、時刻、基本境界の現行要件 | P5R以降の共通前提 |
| `REQ-V2-0036`〜`0043` | 継続。Backtest専用部分だけP5R、継続運用部分はP6 | P5R / P6 |
| `REQ-V2-0044`〜`0055` | P5Rの完了対象として具体化・状態更新 | P5R |
| `REQ-V2-0056`〜`0065` | 実行Modeの順序・昇格条件をv3の新ロードマップで上書き | P6〜P12 |
| `REQ-V2-0066`〜`0079` | P6の安全な運用土台、P10〜P12の実運用Gateへ再配置 | P6 / P10〜P12 |
| `REQ-V2-0080`〜`0112` | 保存、監査、UI、Security、性能、Unknown、追跡の共通要件として継続 | P5R〜P12 |
| `REQ-V3-0113`以降 | P5Rの完成定義とP6〜P12の能力順序を新設する | P5R〜P12 |

#### 実ランタイム受領記録

| 項目 | 結果 |
|---|---|
| runtime backend | `multi_agent_v1` |
| Coordinator | `AutoTradePhasePlanning_Orchestrator_v0_1` |
| Coordinator JSON | `.codex/orchestrators/AutoTradePhasePlanning_Orchestrator_v0_1.json` |
| 固定model | `gpt-5.6-terra` |
| root coordinator agent_id | `01a0082c-050f-7a81-bf31-d3499d476e44` |
| root結果 | 読み取りレビューを受領。作業ツリーへの変更は依頼していない |
| 子Agent起動 | Coordinator環境ではspawn / waitを利用できず、A05 / A10 / A20 / A70 / A90 / A95は未起動 |
| child状態 | `RUNTIME_DISPATCH_FALLBACK_REQUIRED`、`agent_id=N/A`、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK` |

CoordinatorはP5RへSweepを入れ、継続運用UnitをP6へ残すことを推奨した。後続ModeについてはForwardとShadowを同じPhaseへ置く案も示したが、ユーザーが指定した能力順をより明確に守るため、V3-02でForwardとShadowを別の完了Phaseとして判断する。

### V3-02 実行記録

**状態: `COMPLETED`**

#### 採用する能力順序

| 順序 | Phase | なぜこの順番か | 完成の判定 | 次へ進めない条件 |
|---|---|---|---|---|
| 0 | P5R | 過去Dataを使う実験室を先に完成させ、固定ダミーや不完全な計算を次の土台にしない | UIから単一Run / Sweep / 中止・再開 / 結果 / 比較 / CSV / Holdout / Walk-forwardを実データ・実計算で使える | UIが固定値、5指標の根拠不足、結果保存不能、High/Critical、P5R-H0未承認 |
| 1a | P6 | 実時間に進む前に、複数Unit、資金、Risk、注文状態が衝突しても安全に止まる土台を作る | 固定Simulationで複数Unit / Portfolio / Account / Risk / OMS / Kill / 再起動照合 / 復旧を受入済み | 実注文、実資金、実時間Data、外部Accountへ接続する要求が混入 |
| 1b | P7 | P6の安全土台を使い、初めて「今届く市場Data」を仮想的に追う | 実時間の確定足で仮想Signal / OrderIntent / Fill / Positionを記録し、外部Orderが0件 | Data Gate未承認、遅延・欠損・再接続で止まれない、外部Order経路がある |
| 2 | P8 | Forwardが正しく動くことを確かめた後、本番候補と同じ設定を横で複製して違いを観察する | 候補の複製、差分、遅延、欠損、停止、観測期間を説明でき、外部Orderが0件 | Shadowを実注文の承認証拠にする、実口座を変更する |
| 3 | P9 | 実市場の時間の流れで、仮想の財布と家計簿を動かして継続運用を確かめる | 仮想Account / Ledger / Order / Fill / Position / PnL / 再起動復旧が再現でき、外部Orderが0件 | 仮想Ledger差分未解決、外部Order、実資金、Paper完了だけでLive昇格 |
| 4 | P10 | お金を動かす直前に、候補・Risk・Kill・照合・監査・運用者操作を最終確認する | 実注文経路を無効のまま、Start Review、未達、停止、復旧、Candidate Evidenceを受入済み | 実注文・実資金、無承認のSecret、未照合Account、Kill不能 |
| 5 | P11 | はじめて限定した実資金で安全装置を実証する | 個別Human Gateが承認したAccount / Unit / 銘柄 / 時間 / 資金 / 損失 / 注文 / Exposure上限だけで実注文し、照合と停止を実証済み | 範囲外の注文、自動増額、自動昇格、未解決Critical/High |
| 6 | P12 | 小規模Liveの実績をレビュー後、承認された通常範囲へ広げる | 継続監視、Kill、照合、復旧、監査、再承認の条件を満たした範囲を運用 | 「通常」を無制限と解釈する、自動拡張、P11の不具合未解決 |

#### P5RとP6の責務境界

| 項目 | P5R | P6 |
|---|---|---|
| 複数対象 | 過去Dataで試す独立Experiment Set / Sweep | 継続して動く複数運用Unit |
| 資金 | 実験ごとの仮定値。共有の実運用資金は持たない | Portfolio / Account / 資金配分の固定Simulation |
| Risk | 入力検査とBacktestの仮定値。実運用の合算Riskではない | 複数UnitをまたぐRisk判定、拒否、停止、限度 |
| 注文 | 仮想結果を過去Dataから計算するだけ | Signal→Target Position→OrderIntent→Order→Fill→Positionの状態機械を固定Simulationで検証 |
| 再開 | Backtest Job / checkpointの再開 | 実時間運用に備えた再起動、照合、重複防止、Kill、Recovery |
| 絶対にしないこと | 外部注文、実口座、実資金、Forward、Shadow、Paper | 外部注文、実口座、実資金、実時間Dataの完成宣言 |

#### 必須Human Gateと副作用境界

| Gate | 人が確認すること | このGateより前に可能なこと | このGateより前に禁止すること |
|---|---|---|---|
| `P5R-H0` | P5R範囲、負荷受入値、保存、Walk-forward窓、UI実接続 | 要件・詳細設計・REDテスト | P5Rの実装を完了扱い、外部Data追加取得 |
| `P5R-H1` | P5R詳細設計、Data Adapter、5指標、Sweep / CSV / Holdout異常系、RED / Goldenテスト設計 | P5R-H0承認後の詳細化 | P5R実装・テストGreen化・完了宣言 |
| `P5R-H2` | 全P5R受入、対象外境界、Open Unknown、P6再引渡し | P5Rの統合受入・レビュー | P6の実装・実行、Paper / Liveの開始 |
| `P6-H0` | 複数Unit / Risk / OMS固定Simulationの設計 | P5R完了記録の利用 | 外部Order、実資金、実時間Provider接続 |
| `P7-DATA-G1` | 実時間Data Provider、対象、費用、利用条件、通信隔離 | P6の固定Simulation | 実時間外部Dataの受信 |
| `P8-H0` | Shadow対象候補、複製条件、比較期間、差分の扱い | P7のForward結果 | ShadowをLiveの許可に使うこと |
| `P9-H0` | Paper仮想資金、仮想Ledger、仮想約定、日次照合 | P8のShadow結果 | Broker注文、実資金 |
| `P10-H0` | Live候補の開始審査、必要なら読み取り専用接続の範囲、停止と復旧 | P9のPaper結果 | 実注文、実資金、無承認のSecret |
| `P11-LIVE-G1` | 小規模Liveの実資金・上限・Account・対象・時間・監視者 | P10のCandidate Evidence | 上限外・対象外の実注文 |
| `P12-LIVE-G2` | 通常Liveの拡張範囲、再承認、継続監視 | P11の実績・事後レビュー | 自動拡張、無監視・無制限の運用 |

#### 判断理由

Coordinatorの案にはForwardとShadowを同じP7で完成させる案があった。しかしユーザーは「Forward Test → Shadow → Paper → Live候補 → 小規模Live → 通常Live」という能力順を明示している。ShadowはForwardの継続動作を確認した後に初めて意味を持つため、v3ではP7をForward完了、P8をShadow完了として分ける。これはPhase数を増やすことが目的ではなく、何が未完成なら次へ行けないかを一目で分かるようにするためである。

### V3-03 実行記録

**状態: `COMPLETED`**

#### v3の文書構成

| v3節 | 目的 | 根拠・追跡 |
|---|---|---|
| 00. 文書情報とv2との関係 | v3が現行の要件であり、v2は詳細な継承元・履歴であることを明示する | `AT-REQ-002`、REQ-V2-0001、REQ-V2-0106、REQ-V2-0112 |
| 01. Findings first | P5Rを入れない場合の誤認、固定UI、5指標、運用Unit混在、Liveの飛び越えを先に示す | P5R-F-001〜005、P5 Open Unknown |
| 02. 用語と完成の意味 | Backtest Experiment Setと運用Unit、各Mode、各「完成」の意味を区別する | REQ-V2-0036、0044〜0055、0056〜0065 |
| 03. 現在地 | P4 / P5の完了範囲と未完了範囲を区別する | P4完了HTML、P5-11、統合台帳 |
| 04. v3のPhaseロードマップ | P5R、P6〜P12の目的、開始Gate、完了、禁止事項を一表にする | この計画のV3-02 |
| 05. P5R要件 | UIから使えるBacktestを完成させる要件と16受入観点を記す | REQ-V2-0044〜0055、P5R提案 |
| 06. P6〜P12要件 | Forward、Shadow、Paper、Live候補、小規模Live、通常Liveを一つずつ完成させる要件を記す | REQ-V2-0036〜0043、0056〜0079 |
| 07. 昇格・Human Gate | 自動昇格を禁止し、各外部副作用の承認範囲を分ける | REQ-V2-0057、0058、0063〜0065、0101、0105 |
| 08. 継承REQと新設REQ | REQ-V2の継続・上書き・新設REQ-V3を表にする | REQ-V2-0001〜0112、REQ-V3-0113〜0127 |
| 09. Unknownと停止条件 | P5からのUnknown、P5R-H0 / H1 / H2、Data/Broker/実資金のGateを残す | 統合台帳、P5-11引渡し |
| 10. 追跡・レビュー・変更履歴 | 根拠、変更採否、レビュー所見、v3完了条件を残す | REQ-V2-0106、0112 |

#### v3のID方針

| 種別 | 方針 |
|---|---|
| `REQ-V2-*` | 削除・改番しない。詳細な既存要件として継続する |
| `REQ-V3-0113`〜`0118` | P5Rの挿入、UI実接続、5指標、Sweep、分析、Walk-forward、運用Unit分離 |
| `REQ-V3-0119` | P6の複数運用Unit・Portfolio・Risk・OMS固定Simulation |
| `REQ-V3-0120` | P7の実時間・仮想Forward Test |
| `REQ-V3-0121` | P8の本番候補複製・注文なしShadow |
| `REQ-V3-0122` | P9の仮想Account・仮想Ledger Paper |
| `REQ-V3-0123` | P10の実注文前Live候補・Start Review |
| `REQ-V3-0124` | P11の限定実資金Small Live |
| `REQ-V3-0125` | P12の再承認済み通常Live |
| `REQ-V3-0126` | Mode昇格を自動化せず、Human Gateを分離する |
| `REQ-V3-0127` | Phase状態、統合台帳、index、引渡しを同じ現在地に保つ |

#### 改訂の採否

| 項目 | 採否 | 理由 |
|---|---|---|
| v2をそのまま複製する | 不採用 | v2には履歴としての旧管理情報が含まれ、新しい現行文書へそのまま持ち込むと、現行運用と矛盾するため |
| v2をリンクだけにして詳細をすべて削る | 不採用 | 既存REQの追跡性が弱くなり、P5Rと後続Phaseの根拠を読めなくなるため |
| v3を独立した現行要件にし、v2の既存REQを明示継承する | 採用 | 旧IDを壊さず、v3で変更した現在の順序・状態・Gateだけを正本化できるため |
| P5Rに複数運用Unitを入れる | 不採用 | Backtestの完成判断と実運用の安全機能を混ぜるため |
| ForwardとShadowを同一完了Phaseにする | 不採用 | ユーザー指定の能力順を不明確にし、Shadowの開始前提を曖昧にするため |
| P6〜P12を採用する | 採用 | Forwardの土台と完了を分け、以後の5能力を一つずつ検証できるため |

#### 最小更新範囲

1. 新設: `doc/requirements/01_自動トレードシステム要件定義書_v3.html`
2. 更新: `doc/index.html`（v3を現行、v2を履歴へ）
3. 更新: `doc/00_全Phase残課題Blocked統合台帳.html`（次Phase=P5R、P5 Open Unknown継承、P5R-H0 / H1 / H2未承認）
4. 更新: `plan/phase5/Phase6計画入力一覧_2026-08-12.md`（P5Rを経由する履歴入力である旨の注記）
5. 不変: `doc/requirements/01_自動トレードシステム要件定義書_v2.html`、P5完了HTML、P5 Evidence。これらは当時の事実を示す履歴として保持する。

### V3-04 実行記録

**状態: `COMPLETED`**

#### 作成・更新した成果物

| 種別 | パス | 実施内容 |
|---|---|---|
| 新規正式HTML | `doc/requirements/01_自動トレードシステム要件定義書_v3.html` | v2を継承元として明示し、P5R、P6〜P12、REQ-V3-0113〜0127、Gate、Unknown、変更履歴を収容した |
| 入口 | `doc/index.html` | v3を現行要件、v2を履歴として表示し、P5Rと本計画への導線を追加した |
| 現在状態の正本 | `doc/00_全Phase残課題Blocked統合台帳.html` | 現在の次Phase=P5R、P5R-H0 / H1 / H2未承認、P5 Open Unknown、P6→P12順序を追加した |
| P5からの引渡し | `plan/phase5/Phase6計画入力一覧_2026-08-12.md` | P5→P5R→P6の順序と、P6直接開始の禁止を歴史注記として追加した |
| P5R提案 | `plan/Phase5R_バックテスト製品完全化_再構成提案・実行計画書_v0.1_2026-08-16.md` | 状態をv3採用済み、P5R-H0未承認へ更新し、P6〜P12ロードマップに同期した |

#### v3で確定した重要な状態

1. P5Rのロードマップ採用と、P5R実装開始の承認を区別した。現在は前者だけが完了し、`P5R-H0_REQUIRED_NOT_APPROVED`である。
2. P6は複数運用Unit、Portfolio、Account、Risk、OMSの固定Simulationを完成させるPhaseであり、P5Rではない。
3. P7=Forward、P8=Shadow、P9=Paper、P10=Live候補、P11=小規模Live、P12=通常Liveとし、前段を飛ばせない。
4. P11だけが初めて限定実資金と実注文を扱えるPhaseである。P10まで外部Orderは0件でなければならない。
5. P5のProvider条件、host isolation、child dispatch、実行費のUnknownはOpenのままである。

### V3-05 実行記録

**状態: `COMPLETED_WITH_CHILD_DISPATCH_FALLBACK`**

#### Findings first

| ID | 重要度 | 所見 | 修正 | 結果 |
|---|---|---|---|---|
| `RQV3-F-006` | High | P6の説明には固定Simulationがあったが、新設REQのShall文に外部Order・実Account・実資金を禁止する文が明示されていなかった。 | `REQ-V3-0119`へ、外部Order、実Account変更、実資金の禁止と、外部Order 0件の受入を追記した。 | 解消 |
| `RQV3-F-007` | Medium | P5R提案書の追跡表に、旧ロードマップ由来のP6 / P8 / P9以降の参照が残り、v3のP6〜P12と一致しなかった。 | P6 / P9、P10以降、P7へ更新した。 | 解消 |
| `RQV3-F-008` | Medium | doc/index.htmlのP5R計画リンクの表示IDが実際の文書IDと異なっていた。 | `P5R-PLAN-PROPOSAL-001`へ訂正した。 | 解消 |
| `RQV3-F-009` | Low | 新設REQ IDは本文中で説明にも参照されるため、文字列の総出現回数だけでは重複を判定できない。 | HTMLのRequirement anchorを検査し、15件すべて一意であることを確認した。 | 解消 |
| `RQV3-F-010` | Medium | P5R計画にある後続Human Gate `P5R-H1` / `P5R-H2` が、v3のGate表と統合台帳に未登録だった。 | v3のGate・Unknown表と統合台帳に、対象、承認前禁止事項、再開条件を追加した。 | 解消 |
| `RQV3-F-011` | Medium | P5R計画の下部に、Forward / Shadowの完成PhaseをP6と読める旧表現が残っていた。 | P6=固定Simulation土台、P7=Forward完成、P8=Shadow完成へ統一し、v2の旧表現は履歴と明記した。 | 解消 |

#### レビュー結論

- Critical: 0件
- High: 0件（`RQV3-F-006`を修正済み）
- Medium: 0件（`RQV3-F-007`、`RQV3-F-008`、`RQV3-F-010`、`RQV3-F-011`を修正済み）
- Low: 0件（`RQV3-F-009`を確認済み）

子Agentの独立レビューは実行できなかったため、この結果はCoordinatorの読み取りレビューとルートの責務別セルフレビューである。独立Agentレビュー済みとは表現しない。

### V3-06 実行記録

**状態: `COMPLETED`**

#### 静的確認結果

| 確認 | 結果 |
|---|---|
| A95相当の静的ポリシー | v3、index、統合台帳、P5R計画、P6引渡し、この実行計画の6ファイルすべて `ALLOW` |
| v3 HTML | doctype、head、body、mainの開始・終了が各1組 |
| 新設REQ | `REQ-V3-0113`〜`REQ-V3-0127`の15 anchorがすべて一意 |
| ローカルリンク | 6ファイル合計554件を確認し、欠落0件 |
| Secret候補 | 0件 |
| 現在状態 | v3=現行要件、次Phase=P5R、P5R-H0 / H1 / H2未承認、P5→P5R→P6、P6〜P12、P11が初めて実注文可能、の全条件が一致 |
| 状態矛盾 | P6直接開始を禁止する明示文、P5R-H1 / H2の統合台帳登録、P5R計画内のForward / ShadowのPhase表現を補正後、再検査でPASS |

#### Git最終化

今回のタスクで作成・更新したファイルだけをstageし、`git diff --cached --check`、commit、追跡先へのpushをこの実行計画の最終処理として行う。結果は最終報告で明示する。

#### 自己監査（agent-self-evaluation）

| 観点 | 評点（5点満点） | 根拠 |
|---|---:|---|
| 正確さ | 4 | v2、Phase 5完了記録、P5R提案、統合台帳を照合し、P6の外部注文禁止、P5R-H1 / H2の未登録、旧ロードマップの残存をレビューで修正した。実機能の完成をこの文書作成で完了扱いにはしていない。 |
| 完全性 | 5 | 依頼されたStep 1の逐次実行用プロンプト群、Step 2の実行記録、v3、入口、統合台帳、P5→P5R→P6の引渡しを揃えた。 |
| 分かりやすさ | 4 | 各モードを目的・禁止事項・完了条件で分離し、中学生向けの説明を含めた。一方、正式要件として必要な表が多く、分量は大きい。 |
| 実行可能性・安全境界 | 5 | P5R-H0 / H1 / H2からP12-LIVE-G2までの承認前禁止事項、P11が最初の実注文可能段階であること、実Live自動昇格禁止を明記した。 |
| 簡潔さ | 4 | 「超詳細」という依頼に合わせて追跡性を優先したため、同じ事実を要件・台帳・入口で参照できる形にした。 |

**総合: 4.4 / 5.0。**

改善候補（優先順）は次のとおり。

1. P5R-H0承認後に、P5Rの正式な実装計画を別途作成し、各受入条件を実装・E2E証跡へ対応付ける。
2. P5R完了時に、v3の「計画上の完了条件」を実測証跡へ更新し、P6-H0の判断材料を追加する。
3. 将来の各Phase計画では、v3の新設要件IDをテストケース・証跡IDへ1対1で結ぶ。

自己確認として、これは要件・計画文書を完成させる作業であり、P5R実装、外部Data取得、外部注文、実資金の使用は一切実行していない。

## 5. Human Gate一覧

| Gate | 何を承認するか | 承認前に禁止すること |
|---|---|---|
| P5R-H0 | P5Rの実装範囲、固定PCの受入負荷、保存期間、Walk-forward窓、ローカルUIの実行形態 | P5R実装・外部Data追加取得 |
| P5R-H1 | P5R詳細設計、Data Adapter、5指標、Sweep / CSV / Holdoutの異常系、RED / Goldenテスト設計 | P5R実装・テストGreen化・完了宣言 |
| P5R-H2 | P5R全受入、対象外境界、Open Unknown、P6への再引渡し | P6の実装・実行、Paper / Liveの開始 |
| P6-H0 | P6の複数運用Unit・Portfolio・Risk・OMSの固定Simulation設計 | 実時間Data / 外部Orderへの接続 |
| P7-DATA-G1 | 実時間Forwardで使うData Provider、範囲、費用、通信・保持条件 | 実時間外部Data取得 |
| P8-H0 | Shadow候補の複製条件と比較期間 | ShadowをLive承認へ使うこと |
| P9-H0 | Paper仮想資金、Ledger、仮想約定規則 | Paperから実注文へ進むこと |
| P10-H0 | Live候補の最終確認範囲、読み取り専用の外部接続・Secret必要性 | 実注文、実資金の使用 |
| P11-LIVE-G1 | 小規模LiveのAccount、銘柄、Unit、期間、資金、損失・注文・Exposure上限 | 範囲外の実注文 |
| P12-LIVE-G2 | 通常Liveの拡張範囲、継続監視、再承認条件 | 自動拡張、無制限運用 |

## 6. 成功の判定

この文書作成の成功は、BacktestやLive機能そのものを実装したことではない。v3に次のことが矛盾なく記載され、関連する現在状態の正本へ反映されることである。

- P5RがP5とP6の間にある。
- UIから使うBacktestを完璧にする責務がP5Rにある。
- 複数運用UnitはP6に残る。
- Forward、Shadow、Paper、Live候補、小規模Live、通常Liveの完成順が守られる。
- どの段階まで外部Orderが0件か、最初に実注文が可能なのはどこかが明確である。
- UnknownとHuman Gateを隠さず、実Liveへの自動昇格を禁止している。
