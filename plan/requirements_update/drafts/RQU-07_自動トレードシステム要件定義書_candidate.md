# 自動トレードシステム 要件定義書（C4候補）

## 文書情報

| 項目 | 内容 |
|---|---|
| 文書ID | `AT-REQ-001` |
| 版 | `candidate-0.3` |
| 基準日 | 2026-08-10 |
| 状態 | RQU-H3承認前の最終候補。正式正本ではない |
| 編集原稿の正本候補 | `plan/自動トレードシステム_要件定義書.md` |
| 正式HTMLの正本候補 | `doc/requirements/01_自動トレードシステム要件定義書.html` |
| 事実の基準 | Phase 3完了判定、正式詳細設計、src、tests、統合台帳 |

> この文書は、ITを知らない中学生でも読めるようにした要件定義書の候補である。専門用語を消さず、身近なたとえ、正式名称、システム上の意味の順に説明する。RQU-H3承認前は、正式Markdown、正式HTML、`doc/index.html`を差し替えない。

## 目次

1. 30秒で分かる要約と状態の読み方
2. C4 Level 1: System Context
3. C4 Level 2: Container
4. C4 Level 3: Component
5. C4 Level 4: Code / Detail
6. 機能・品質・安全・移行要件
7. Q1〜Q30 / OD-01〜OD-08の現在状態
8. Unknown、証拠、ロードマップ、用語集、変更履歴

## 1. 30秒で分かる要約

このシステムは、過去の市場データを決めた順番で再生し、Turtleを含む売買ルールを固定条件で試す仕組みである。データの身元・品質・hashを確認してから、確定した足だけをStrategyへ渡し、Backtestの結果・停止理由・証拠を保存する。[REQ-CTX-003][REQ-DATA-001][REQ-STR-001][REQ-BT-001]

現在確認できているのは、固定入力・固定契約・固定範囲の検証である。利益保証、本番運用許可、Broker接続、Paper、Live、Secret、Cloudの承認ではない。長期データ、実Cost、正式Calendar、Risk値、外部接続は別のHuman Gateで確認する。[REQ-GATE-001][REQ-GATE-002][REQ-GATE-003][REQ-GATE-004]

### 状態の読み方

| ラベル | 意味 | 図の表現 |
|---|---|---|
| `[実装済み]` | 現在のコード・正式設計に責務がある | 青、実線 |
| `[固定範囲で確認済み]` | 固定入力・契約で証拠がある | 緑、証拠ID |
| `[承認済み延期/Unknown]` | 延期は承認済みだが未解消・未PASS | 黄、破線、`UNK-*` |
| `[将来計画]` | 将来候補・移行条件 | 紫、破線 |
| `[未承認/禁止境界]` | 人の承認なしには接続・実行しない | 赤、太線、停止矢印 |

色だけで状態を判断せず、ラベル、線種、要求ID、証拠IDを併用する。[REQ-QA-001][REQ-GATE-001]

## 2. C4 Level 1: System Context（街の中の建物）

Level 1は「この建物は街のどこにあり、誰が使うか」を説明する。利用者が条件を入力し、システムが過去データを再生し、結果または停止理由を返す。人が承認しなければ越えられない境界を明示する。[REQ-CTX-003][REQ-GATE-001]

```mermaid
flowchart LR
  subgraph PEOPLE["人"]
    USER["利用者\n[実装済み]"]
    APPROVER["承認者\nHuman Gate"]
    OPS["運用者\n[将来計画]"]
  end
  subgraph SYSTEM["自動トレードシステム\n[固定範囲]"]
    CORE["Market Data\nStrategy\nBacktest"]
    EVIDENCE["Result / Manifest / Evidence"]
  end
  subgraph OUTSIDE["外部・将来境界"]
    DATA["市場データ提供元\n[入力境界]"]
    ENGINE["Engine候補\nLEAN PoC"]
    BROKER["Broker / Paper / Live\n[未承認]"]
    CLOUD["Secret / Cloud / 通知\n[将来計画]"]
  end
  USER -->|"設定・Run依頼"| CORE
  DATA -->|"データ・版・由来"| CORE
  CORE -->|"結果・停止理由"| EVIDENCE
  EVIDENCE -->|"証拠・ログ・hash"| USER
  APPROVER -->|"承認・不承認"| CORE
  CORE -.->|"PoC候補"| ENGINE
  CORE -.->|"承認なしでは接続しない"| BROKER
  OPS -.->|"将来の監視"| CLOUD
  classDef implemented fill:#dbeafe,stroke:#1d4ed8,color:#1e3a8a;
  classDef verified fill:#dcfce7,stroke:#15803d,color:#14532d;
  classDef future fill:#f3e8ff,stroke:#7e22ce,color:#581c87,stroke-dasharray:5 5;
  classDef prohibited fill:#fee2e2,stroke:#b91c1c,color:#7f1d1d,stroke-width:3px;
  class USER,DATA implemented;
  class CORE,EVIDENCE verified;
  class OPS,ENGINE,CLOUD future;
  class APPROVER,BROKER prohibited;
```

**この図で見るポイント:** 緑は固定範囲、紫は将来、赤は未承認である。LEANはPoC候補であり、最終Engineの採用決定ではない。Broker、Paper、Live、Secret、Cloudは別Gateの対象である。[REQ-EXE-001][REQ-EXE-003][REQ-OPS-001][REQ-OPS-006]

| 外部・利用者 | 受け渡すもの | 返るもの | 不合格時 |
|---|---|---|---|
| 利用者 | Run ID、期間、市場、設定、実行依頼 | Result、StopReason、Manifest、hash | 必須項目がなければ開始しない [`REQ-BT-002`] |
| 市場データ | Raw/DBN、Catalog、版、provenance | 正規化データ、品質判定 | 欠損・順序・hash不一致なら停止 [`REQ-DATA-001`〜`REQ-DATA-004`] |
| 承認者 | Human Gateの承認・不承認 | 次段階へ進めるかの状態 | 未承認なら停止 [`REQ-GATE-001`〜`REQ-GATE-004`] |
| Engine候補 | Core契約と候補Engine結果 | 型付きResult、EngineIdentity | SDK漏れ・identity不一致なら停止 [`REQ-EXE-001`][`REQ-EXE-002`] |

## 3. C4 Level 2: Container（建物の部屋）

Containerは、責務を考えるための部屋である。必ずしも別サーバーを意味しない。部屋同士は決めた形式の情報だけを交換し、失敗したら安全に停止する。[REQ-EXE-002][REQ-QA-001]

初めて出てくる言葉を先に置き換える。`ClosedBar`は「値が確定した1本の足」、`SignalEvent`は「売買ルールが出した判断メモ」、`TargetPosition`は「持ちたい状態」であり注文そのものではない。`Paper`は「本物のお金を使わない模擬取引」、`OMS`は「注文を管理する係」である。[REQ-DATA-003][REQ-STR-001][REQ-RISK-006][REQ-EXE-003]

```mermaid
flowchart LR
  subgraph INPUT["受付"]
    ENTRY["設定・実行入口"]
  end
  subgraph DATAROOM["データ"]
    MD["Market Data"]
  end
  subgraph CORE["判断・実験"]
    STR["Strategy"]
    BT["Backtest / Experiment"]
    ADAPTER["Engine Adapter"]
  end
  subgraph RECORD["証拠"]
    STORE["Evidence / Result Store"]
  end
  subgraph FUTURE["将来・未承認"]
    RISK["Risk / Account / OMS"]
    BROKER2["Broker Adapter"]
    MON["Monitoring / Secret / Cloud"]
  end
  ENTRY -->|"設定・Run ID"| MD
  MD -->|"品質確認済みClosedBar"| STR
  STR -->|"SignalEvent / TargetPosition"| BT
  BT -->|"Core契約"| ADAPTER
  ADAPTER -->|"EngineIdentity付き結果"| BT
  BT -->|"Result / StopReason"| STORE
  STORE -->|"hash付き証拠"| ENTRY
  STR -.->|"将来の注文意図"| RISK
  RISK -.->|"Paper Gate後だけ"| BROKER2
  MON -.->|"将来の監視"| ENTRY
  classDef current fill:#dcfce7,stroke:#15803d,color:#14532d;
  classDef future fill:#f3e8ff,stroke:#7e22ce,color:#581c87,stroke-dasharray:5 5;
  classDef prohibited fill:#fee2e2,stroke:#b91c1c,color:#7f1d1d,stroke-width:3px;
  class ENTRY,MD,STR,BT,ADAPTER,STORE current;
  class RISK,MON future;
  class BROKER2 prohibited;
```

| 部屋 | 入力 | 出力 | 失敗時 | 要求ID |
|---|---|---|---|---|
| 設定・実行入口 | `ExperimentPlan`、設定版、Run ID | 受付結果 | 必須項目不足で開始しない | `REQ-BT-002`、`REQ-OPS-002` |
| Market Data | Raw/DBN、Catalog、版 | `MarketEvent`、`ClosedBar`、品質、provenance（データの出どころ） | 欠損・未来・重複・hash不一致で停止 | `REQ-DATA-001`〜`REQ-DATA-008` |
| Strategy | ClosedBar、Config、State | SignalEvent、TargetPosition | 未確定足・時間逆行・M30来歴不足で停止 | `REQ-STR-001`〜`REQ-STR-009` |
| Backtest | Manifest、Replay、Calendar、Fill設定 | Result、Snapshot、StopReason | Gate・Replay・Calendar・Fill違反で停止 | `REQ-BT-001`〜`REQ-BT-005` |
| Engine Adapter | Core契約、候補結果 | 型付きResult | SDK漏れ・未許可Engineで停止 | `REQ-EXE-001`、`REQ-EXE-002` |
| Evidence Store | Result、Manifest、hash、ログ | 後から確認できる証拠 | 保存不整合なら結果を採用しない | `REQ-QA-001`、`REQ-QA-003` |
| Risk / OMS / Broker | TargetPosition、承認、Risk判断 | 将来のOrderIntent・外部注文 | 現在は未承認で外部注文へ進めない | `REQ-RISK-006`、`REQ-EXE-003` |

### 3.1 Backtestのシーケンス

```mermaid
sequenceDiagram
  box rgb(254,243,199) 利用者
    participant U as 利用者
  end
  box rgb(219,234,254) 固定範囲システム
    participant E as 実行入口
    participant M as Market Data
    participant S as Strategy
    participant B as Backtest
    participant V as Evidence
  end
  U->>E: Run ID、期間、市場、設定
  E->>M: Manifestと入力版の確認
  M-->>E: 品質、hash、provenance
  alt Gate合格
    E->>S: ClosedBar、StrategyConfig
    S-->>B: SignalEvent、TargetPosition
    B->>B: 時刻順Replay、Calendar、Fill、Cost
    B->>V: Result、Snapshot、hash
    V-->>U: 結果と証拠リンク
  else Gate不合格
    M-->>B: STOPPED、停止理由
    B->>V: 停止理由、hash、ログ
    V-->>U: 停止と再開条件
  end
```

### 3.2 将来PaperのHuman Gate付きシーケンス

```mermaid
sequenceDiagram
  box rgb(219,234,254) 現在
    participant BT as Backtest
    participant EV as Evidence
  end
  box rgb(254,243,199) 人の承認
    participant H as Human Gate
  end
  box rgb(243,232,255) 将来Paper
    participant R as Risk / OMS
    participant P as Paper Broker
  end
  BT->>EV: 固定範囲Result、Unknown、hash
  EV-->>H: 証拠と再開条件
  alt 未承認またはUnknown
    H-->>BT: STOPPED
  else 承認
    H->>R: Risk上限、停止条件
    R->>P: 模擬注文
    P-->>R: 模擬約定または拒否
  end
```

Paper以降は将来設計であり、現在の接続や実行実績を表さない。[REQ-GATE-001][REQ-GATE-003][REQ-OPS-001]

## 4. C4 Level 3: Component（部屋の専門スタッフ）

### 4.1 Market Data / Strategy / Backtest

```mermaid
flowchart TD
  subgraph MARKET["Market Data担当"]
    CAT["Catalog Resolver"]
    RAW["Raw / DBN Store"]
    NOR["Normalized Store"]
    QC["Quality Checker"]
  end
  subgraph STRATEGY["Strategy担当"]
    IND["指標・Donchian・N"]
    TURTLE["Turtle System 1 / 2"]
    STATE["State / Stop / Exit"]
  end
  subgraph BACKTEST["Backtest担当"]
    REPLAY["Deterministic Replay"]
    CAL["Calendar / Roll"]
    FILL["Fill / Cost / Gap"]
    RESULT["Result / Snapshot"]
  end
  CAT --> RAW --> NOR --> QC
  QC -->|"品質済みClosedBar"| IND
  IND --> TURTLE --> STATE
  STATE -->|"TargetPosition"| REPLAY
  REPLAY --> CAL --> FILL --> RESULT
  classDef data fill:#dbeafe,stroke:#1d4ed8,color:#1e3a8a;
  classDef strategy fill:#fef3c7,stroke:#b45309,color:#78350f;
  classDef backtest fill:#dcfce7,stroke:#15803d,color:#14532d;
  class CAT,RAW,NOR,QC data;
  class IND,TURTLE,STATE strategy;
  class REPLAY,CAL,FILL,RESULT backtest;
```

### 4.2 安全停止とM30

```mermaid
flowchart TD
  IN["M1入力を受け取る"] --> COUNT["連続30本か確認"]
  COUNT -->|"不足"| STOP1["STOPPED\nM30 provenance不足"]
  COUNT -->|"十分"| PROV["時刻・銘柄・hash・由来を確認"]
  PROV -->|"不一致"| STOP2["STOPPED\n入力の身元不一致"]
  PROV -->|"一致"| M30["M30を作る"]
  M30 -->|"ClosedBar"| STRATEGY2["Strategyへ渡す"]
  STOP1 --> EVID["理由・hash・再開条件を保存"]
  STOP2 --> EVID
  classDef input fill:#dbeafe,stroke:#1d4ed8,color:#1e3a8a;
  classDef check fill:#fef3c7,stroke:#b45309,color:#78350f;
  classDef good fill:#dcfce7,stroke:#15803d,color:#14532d;
  classDef stop fill:#fee2e2,stroke:#b91c1c,color:#7f1d1d;
  class IN input;
  class COUNT,PROV check;
  class M30,STRATEGY2 good;
  class STOP1,STOP2,EVID stop;
```

M30（30分のまとまり）は実M1（1分の足）連続30本から直接集計する。M15を二本つなぐ近道、由来のないM30、未来の足は受け入れない。[REQ-DATA-003][REQ-QA-002]

## 5. C4 Level 4: Code / Detail（データと状態のマニュアル）

### 5.1 概念データ関係

```mermaid
classDiagram
  class MarketEvent
  class ClosedBar
  class ExperimentPlan
  class ExperimentManifest
  class DataGateDecision
  class SignalEvent
  class TargetPosition
  class OrderIntent
  class Snapshot
  class Result
  class HumanGate
  class Unknown
  MarketEvent --> ClosedBar : 確定
  ClosedBar --> DataGateDecision : 品質・由来
  ExperimentPlan --> ExperimentManifest : 封印
  ExperimentManifest --> DataGateDecision : 入力検査
  ClosedBar --> SignalEvent : Strategy判断
  SignalEvent --> TargetPosition : 目標状態
  TargetPosition --> OrderIntent : Risk承認後候補
  ExperimentManifest --> Result : 版・hash
  Snapshot --> Result : 復旧情報
  Result --> HumanGate : 証拠提示
  HumanGate --> Unknown : 未確定の承認状態
  classDef data fill:#dcfce7,stroke:#15803d,color:#14532d;
  classDef gate fill:#fee2e2,stroke:#b91c1c,color:#7f1d1d;
  classDef future fill:#f3e8ff,stroke:#7e22ce,color:#581c87;
  class MarketEvent data
  class ClosedBar data
  class ExperimentPlan data
  class ExperimentManifest data
  class DataGateDecision gate
  class SignalEvent data
  class TargetPosition data
  class Snapshot data
  class Result data
  class HumanGate gate
  class Unknown gate
  class OrderIntent future
```

### 5.2 Data Gate・Experiment・OrderIntentの状態

状態図は、箱が「いまの状態」、矢印が「状態の変化」を表す。`OrderIntent`の図はPaper以降の将来候補であり、現在の外部注文を表さない。`APPROVED_FOR_PAPER`は人の承認があった場合だけ通る境界である。[REQ-GATE-001][REQ-GATE-003][REQ-EXE-003]

```mermaid
stateDiagram-v2
  [*] --> READY
  READY --> VALIDATING : 入力を受け取る
  VALIDATING --> COMMITTED : 品質・版・hash合格
  VALIDATING --> STOPPED : 欠損・未来・順序異常
  COMMITTED --> REPLAYING : Replay開始
  REPLAYING --> COMPLETED : Result保存
  REPLAYING --> STOPPED : 契約違反
  STOPPED --> RECHECK_REQUIRED : 理由・hash保存
  RECHECK_REQUIRED --> VALIDATING : 新しいRunで再検証
  classDef good fill:#dcfce7,stroke:#15803d,color:#14532d;
  classDef stop fill:#fee2e2,stroke:#b91c1c,color:#7f1d1d;
  class READY,VALIDATING,COMMITTED,REPLAYING,COMPLETED good;
  class STOPPED,RECHECK_REQUIRED stop;
```

```mermaid
stateDiagram-v2
  [*] --> GENERATED
  GENERATED --> RISK_CHECK : TargetPositionから候補
  RISK_CHECK --> REJECTED : Risk不合格・未承認
  RISK_CHECK --> APPROVED_FOR_PAPER : Paper Gate承認
  APPROVED_FOR_PAPER --> PAPER_SENT : 模擬注文
  PAPER_SENT --> PAPER_RESULT : 返事
  PAPER_RESULT --> STOPPED : 異常・接続断・手動停止
  PAPER_RESULT --> [*] : 証拠保存
  REJECTED --> [*]
  STOPPED --> [*]
  classDef normal fill:#dbeafe,stroke:#1d4ed8,color:#1e3a8a;
  classDef approved fill:#dcfce7,stroke:#15803d,color:#14532d;
  classDef stop fill:#fee2e2,stroke:#b91c1c,color:#7f1d1d;
  class GENERATED,RISK_CHECK normal;
  class APPROVED_FOR_PAPER,PAPER_SENT,PAPER_RESULT approved;
  class REJECTED,STOPPED stop;
```

`TargetPosition`は目標状態、`OrderIntent`は将来の注文意図である。Risk・OMS・Human Gateを通らない限り、外部注文にはならない。[REQ-RISK-006][REQ-EXE-003]

| 概念 | 現在の実装・証拠 | 要件上の意味 |
|---|---|---|
| `MarketEvent` / `ClosedBar` | Market Data正規化、`strategy.contracts` | 確定した市場入力 |
| `SignalEvent` | `strategy.contracts.SignalEvent` | ルール判断の記録 |
| `TargetPosition` | `strategy.contracts.TargetPosition` | 目標保有状態 |
| `OrderIntent` | Risk/OMS境界の将来概念 | 承認後の注文意図候補 |
| `ExperimentManifest` | `backtest.contracts`、`experiment_manifest.py` | 実験条件・版・hash |
| `DataGateDecision` | `runner.py` | 入力を通す・止める判断 |
| `Snapshot` | `snapshot.py` | 途中状態から復旧する情報 |
| `Result` | Backtest result DTO | 結果、停止理由、証拠への接続 |
| `HumanGate` / `Unknown` | 統合台帳、P3-D14、RQU記録 | 人の承認と未解決事項 |

## 6. 機能・非機能・安全・移行

### 6.1 機能要件

- Market DataはCatalog、Raw、Normalized、Quality、Manifest、provenanceを扱う。[REQ-DATA-001][REQ-DATA-002][REQ-DATA-003][REQ-DATA-004][REQ-DATA-008]
- StrategyはClosedBar、Turtle variant、SignalEvent、TargetPosition、Snapshotを扱う。[REQ-STR-001][REQ-STR-002][REQ-STR-003][REQ-STR-004][REQ-STR-005][REQ-STR-006][REQ-STR-007][REQ-STR-008][REQ-STR-009]
- Backtestは決定的Replay、Calendar、Fill、Cost、Roll、Manifest、Result、restoreを扱う。[REQ-BT-001][REQ-BT-002][REQ-BT-003][REQ-BT-004][REQ-BT-005]
- Engine Adapterは外部Engine依存を境界に閉じ込める。[REQ-EXE-001][REQ-EXE-002]

### 6.2 非機能・安全要件

| 要件 | 内容 | 状態 |
|---|---|---|
| 再現性 | 同じ入力、設定、版、hashで同じReplayを再現する | 固定範囲で確認済み [`REQ-BT-001`][`REQ-BT-002`] |
| 監査性 | Result、StopReason、Manifest、hash、ログを保存する | 実装済み [`REQ-QA-001`][`REQ-QA-003`] |
| 品質 | Golden、Bias、固定4 Gate、独立レビューを通す | 固定範囲で確認済み [`REQ-QA-002`][`REQ-QA-004`] |
| 安全停止 | 不明・不整合・未承認ではSTOPPEDを固定する | 実装済み [`REQ-RISK-007`][`REQ-OPS-003`] |
| Secret | Secretを出力せず、最小権限で扱う | 外部運用は未承認 [`REQ-OPS-006`] |
| 監視 | 新規注文、接続断、停止、Heartbeatを監視する | 将来計画 [`REQ-OPS-003`][`REQ-OPS-004`][`REQ-OPS-005`] |
| 環境分離 | Offline、host isolation、入力hash前後一致を確認する | 固定範囲確認済み [`REQ-OPS-007`] |

### 6.3 移行条件

`Backtest → Shadow → Paper → 少額Live → 本番Live`の順番を守る。前段階の証拠、人の承認、停止・復旧条件がない場合は次へ進まない。[REQ-GATE-001][REQ-GATE-002]

| 段階 | 条件 | 現在 |
|---|---|---|
| Backtest | 固定入力、Replay、Golden、証拠 | 固定範囲で確認済み |
| Shadow | 長期データ、監視、停止、復旧 | 未承認 |
| Paper | Risk、OMS、Broker Adapter、模擬注文、運用日数 | 未承認 |
| 少額Live | 資金、証拠金、実Cost、Human Gate | 未承認 |
| 本番Live | 継続監視、最終Checklist、採用判断 | 未承認 |

利益性、最大DD、1Nリスク、volatilityは目標・比較基準であり、利益保証や投資助言ではない。[REQ-RISK-001][REQ-RISK-002][REQ-RISK-003][REQ-RISK-005]

## 7. Q1〜Q30 / OD-01〜OD-08の現在状態

旧IDは履歴として残し、現在のREQ、実装済み範囲、未確定・将来を分ける。[REQ-QA-001]

| 旧ID | 現行REQ | 現在の意味・状態 |
|---|---|---|
| Q1 | `REQ-STR-001` | variant比較。固定範囲検証あり |
| Q2 | `REQ-CTX-003` | 対象市場は未確定 |
| Q3 | `REQ-CTX-004` | 初期3〜5市場、拡大は将来 |
| Q4 | `REQ-STR-002` | Long/Short、固定範囲確認済み |
| Q5 | `REQ-GATE-004` | 資金制約はLive許可ではない |
| Q6 | `REQ-OPS-004` | 費用目標、実績未確定 |
| Q7 | `REQ-EXE-003` | IBKR候補、接続未承認 |
| Q8 | `REQ-RISK-001` | DD15%は基準、保証ではない |
| Q9 | `REQ-RISK-002` | 1N 1%は比較基準、未確定 |
| Q10 | `REQ-RISK-003` | volatility参考基準、未決定 |
| Q11 | `REQ-STR-003` | 段階的Strategy比較 |
| Q12 | `REQ-STR-004` | System 1勝ちブレイク、固定範囲 |
| Q13 | `REQ-STR-005` | intradayとclose-confirmedを分離 |
| Q14 | `REQ-STR-006` | ピラミッディングvariant、範囲限定 |
| Q15 | `REQ-STR-007` | Stop/Whipsaw、実市場未確定 |
| Q16 | `REQ-RISK-005` | Unit値はPaper前に決定 |
| Q17 | `REQ-RISK-006` | StrategyとRisk/OMSを分離 |
| Q18 | `REQ-STR-008` | Unit比較基準を保持 |
| Q19 | `REQ-DATA-007` | Roll/Calendar、`UNK-P3-05/07` |
| Q20 | `REQ-DATA-008` | M1正本、上位足を決定生成 |
| Q21 | `REQ-EXE-001` | LEAN PoC候補、最終未決定 |
| Q22 | `REQ-OPS-001` | Cloud実行は将来・未承認 |
| Q23 | `REQ-OPS-002` | 設定版/hash追跡、固定範囲実装 |
| Q24 | `REQ-GATE-001` | 段階移行、将来Gate |
| Q25 | `REQ-OPS-003` | 停止・接続・Heartbeat監視、将来計画 |
| Q26 | `REQ-RISK-007` | 異常時新規注文停止、Core固定範囲 |
| Q27 | `REQ-OPS-005` | Push/Heartbeat未確定 |
| Q28 | `REQ-OPS-006` | Secret未承認 |
| Q29 | `REQ-QA-001` | 共通Core・固定証拠、確認済み |
| Q30 | `REQ-GATE-002` | 最終Checklist、人の承認、未承認 |

| 旧OD | 現行REQ | 決定状態 |
|---|---|---|
| OD-01 | `REQ-CTX-003` | 市場・データ確認後に決定 |
| OD-02 | `REQ-EXE-001` | LEAN主PoC候補、最終未決定 |
| OD-03 | `REQ-DATA-007` | 正式Calendar後に決定 |
| OD-04 | `REQ-RISK-002` | Paper前に決定 |
| OD-05 | `REQ-RISK-003` | Risk設計時に決定 |
| OD-06 | `REQ-OPS-001` | Cloud未承認 |
| OD-07 | `REQ-OPS-005` | 通知サービス未決定 |
| OD-08 | `REQ-GATE-003` | Paper/Live移行前に決定 |

## 8. Unknownと証拠

| ID | 内容 | 再開条件 | 状態 |
|---|---|---|---|
| `UNK-P3-01` | 長期データ、市場数、holdout | 市場・期間・Catalog・品質・split・hashを別Runで固定 | `APPROVED_DEFERRED_UNKNOWN` |
| `UNK-P3-05` | 実Cost、slippage、Gap | 市場別実値・感度分析・fixture | `APPROVED_DEFERRED_UNKNOWN` |
| `UNK-P3-07` | 正式Calendar継続追随 | 公式版・監視・欠損時停止・fixture | `APPROVED_DEFERRED_UNKNOWN` |
| `RQU-UNK-01` | 実ブラウザのMermaid文字配置 | RQU-08B/C | 部分解消、未PASS |

固定RunのPASSは、その固定範囲を示す証拠である。Unknown、長期利益、本番安全性をPASSへ広げない。[REQ-QA-001][REQ-GATE-003]

## 9. 用語ミニ辞典

| 正式語 | 中学生向けのたとえ | このシステムでの意味 |
|---|---|---|
| Database | 大きな本棚 | 記録を決めた場所に保存する仕組み |
| API | 部屋へ注文を運ぶウェイター | 別部品へ依頼し、返事を受け取る入口 |
| Adapter | 変換プラグ | 外部の違う形式をCore契約へ変換する境界 |
| Manifest | 封印付き持ち物リスト | 入力、設定、版、hashをまとめたもの |
| hash | デジタル指紋 | ファイルが変わっていないか確認する値 |
| Replay | 録画の再生 | 同じ市場データを同じ順番で流す処理 |
| Snapshot | ゲームのセーブデータ | 途中状態から同じ条件で再開する情報 |
| Fail-Closed | 分からない時の安全ブレーキ | 不整合・不明・未承認なら停止する設計 |
| Human Gate | 人が持つ鍵のゲート | 人が証拠を見て次の段階を承認する場所 |
| Unknown | まだ答えを書けない箱 | 証拠不足で未解消・未PASSの状態 |

## 10. 要求ID凡例

| 分類 | 要求ID |
|---|---|
| Context | `REQ-CTX-003`, `REQ-CTX-004` |
| Data | `REQ-DATA-001`, `REQ-DATA-002`, `REQ-DATA-003`, `REQ-DATA-004`, `REQ-DATA-005`, `REQ-DATA-006`, `REQ-DATA-007`, `REQ-DATA-008` |
| Strategy | `REQ-STR-001`, `REQ-STR-002`, `REQ-STR-003`, `REQ-STR-004`, `REQ-STR-005`, `REQ-STR-006`, `REQ-STR-007`, `REQ-STR-008`, `REQ-STR-009` |
| Backtest | `REQ-BT-001`, `REQ-BT-002`, `REQ-BT-003`, `REQ-BT-004`, `REQ-BT-005` |
| Engine / Adapter | `REQ-EXE-001`〜`REQ-EXE-003` |
| Risk | `REQ-RISK-001`, `REQ-RISK-002`, `REQ-RISK-003`, `REQ-RISK-005`, `REQ-RISK-006`, `REQ-RISK-007` |
| Operations | `REQ-OPS-001`, `REQ-OPS-002`, `REQ-OPS-003`, `REQ-OPS-004`, `REQ-OPS-005`, `REQ-OPS-006`, `REQ-OPS-007` |
| Quality | `REQ-QA-001`, `REQ-QA-002`, `REQ-QA-003`, `REQ-QA-004` |
| Gate | `REQ-GATE-001`, `REQ-GATE-002`, `REQ-GATE-003`, `REQ-GATE-004` |

## 11. 変更履歴と正本化条件

| 版 | 日付 | 内容 | 状態 |
|---|---|---|---|
| `candidate-0.1` | 2026-08-10 | RQU-05/06をC4 Level 1〜4と横断章へ統合 | 履歴候補 |
| `candidate-0.2` | 2026-08-10 | RQU-06R指摘、用語、Unknown、状態凡例を反映 | 履歴候補 |
| `candidate-0.3` | 2026-08-10 | RQU-08A〜C指摘、追跡リンク、Q/OD行単位表、可読性補足を反映 | RQU-H3承認待ち |

### 関連する正式成果物・追跡先

この候補は要件の全体像を示す。実装の細部と過去の判断は、次の正式成果物を開いて確認する。

- [P3-D04 Strategy実装詳細設計書](../../../doc/phase3/03_Strategy詳細設計/03_Strategy_Turtle実装詳細設計書.html)
- [P3-D05 Backtest/Experiment実装詳細設計書](../../../doc/phase3/04_Backtest詳細設計/04_Backtest_Experiment実装詳細設計書.html)
- [P3-D14 Phase 3完了判定・Phase 4移行承認書](../../../doc/phase3/10_完了判定/13_Phase3完了判定とPhase4移行承認書.html)
- [RQU-03 要件採否追跡マトリクス](../RQU-03_要件採否追跡マトリクス_2026-08-10.md)
- [RQU-04 C4章構成・用語辞書](../RQU-04_C4章構成図解仕様用語辞書_2026-08-10.md)
- [全Phase残課題・Blocked統合台帳](../../../doc/00_全Phase残課題Blocked統合台帳.html)

`REQ-DATA-005`と`REQ-DATA-006`の細かい意味は、この候補で勝手に再定義しない。採否、根拠、未確定状態はRQU-03を追跡先とする。[REQ-QA-001]

RQU-08A〜Cのレビュー、RQU-09Aの改訂、RQU-09Bの再レビューを完了し、RQU-H3が承認された後に、正式Markdown、正式HTML、`doc/index.html`を同じ版・基準日で更新する。[REQ-GATE-002]
