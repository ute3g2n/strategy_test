# RQU-UI-07 UI骨格・Design System実装記録

## 0. 実行情報

| 項目 | 内容 |
|---|---|
| Step | `RQU-UI-07` |
| Phase | `REQUIREMENTS_UI_UPDATE_2026_08_11` |
| 実行日 | 2026-08-11 |
| 入力 | `RQU-UI-05_情報設計・画面状態仕様記録_2026-08-11.md`、`RQU-UI_UIモック受入確認表_2026-08-11.md`、RQU-UI-06 candidate、`ui/mock/`既存Pilot |
| 目的 | 21画面・10ナビゲーション・10共通状態を、後続画面実装が再利用できる共通骨格として固定する |
| 判定 | `COMPLETED_WITH_OPEN_FINDINGS` |
| 外部I/O | なし。匿名固定ダミーのみ。Broker、実データ、Secret、実注文、外部AIは未接続 |
| 正式文書 | 正式要件HTML、編集用要件Markdown、正式UI HTML、`doc/index.html`は未変更 |

## 1. Findings first

| Finding ID | 重大度 | 状態 | 内容 | 次処理 |
|---|---|---|---|---|
| `RQU-UI-07-F-001` | Medium | Open | `npm run lint`は失敗していないが、`src/ui.tsx`の定数・共通関数エクスポートについてFast Refresh警告が5件出る | 共通部品の配置を整理するか、RQU-UI-13の品質整理で判断する |
| `RQU-UI-07-F-002` | Medium | Open | Storybook buildで500KB超のchunk警告が出る | UI本体の分割要否をRQU-UI-13で評価する。現時点で機能合否をPassにしない |
| `RQU-UI-07-F-003` | Low | Open | Vitestのaxe実行時にjsdomのCanvas未実装メッセージが出る | 実Chromiumのaxe検査をRQU-UI-11で実施し、jsdom警告と合否を分離する |
| `RQU-UI-07-F-004` | Medium | Deferred | 全21画面×10状態の視覚差分、キーボード順序、コントラストの完全検査は未実施 | RQU-UI-11のPC/スマホVisual・a11y検証で確認する |
| `RQU-UI-07-F-005` | Medium | Deferred | `shadcn` registry部品を追加する必要性は未確定 | RQU-UI-13で既存共通部品との比較後に判断する |

Open/Deferredは未確定事項であり、Passへ変更していない。

## 2. 実装した共通契約

### 2.1 ナビゲーションと画面ID

`ui/mock/src/ui.tsx`に`NAV-01`〜`NAV-10`と`SCREEN-01`〜`SCREEN-21`の定義を集約した。各画面はタイトル、説明、初期状態、`E2E-UI-*`、`data-testid=nav-SCREEN-xx`を持つ。`App.tsx`はこの定義から左ナビゲーションを生成するため、定義と表示の件数が分離しない。

| 確認 | 結果 |
|---|---|
| ナビゲーション大分類 | 10件 |
| 必須画面 | 21件 |
| 画面ごとの遷移ボタン | `nav-SCREEN-01`〜`nav-SCREEN-21` |
| PC表示 | 左サイドバーを常時表示 |
| スマホ表示 | メニューボタンで開くドロワー。画面選択後に自動で閉じる |
| 外部ルート | なし。画面状態をReact内で切り替える匿名モック |

### 2.2 共通状態

`NORMAL`、`LOADING`、`EMPTY`、`REQUIRED`、`WARNING`、`STOPPED`、`FAILED`、`RECOVERY`、`HUMAN-GATE`、`UNAPPROVED`を共通の`UiState`として定義した。状態バッジ、状態説明、警告、進捗、空データ、エラー、再確認の入口を共通部品で表示する。後続画面は状態を独自文字列で増やさず、この契約を使う。

### 2.3 共通部品

- `StateBadge`: 状態名、色、ドット、`data-testid=state-*`。
- `StateAlert`: 状態の意味と次の確認を表示。警告・失敗はARIA alert、それ以外はstatus。
- `MetricCard`: 固定指標のラベル、値、補足を表示。
- `ProgressBar`: 進捗率を0〜100へ丸め、数値とバーを併記。
- `LoadingState`、`EmptyState`、`ErrorState`: 読込中、データなし、失敗の共通表現。
- `HelpTip`: 操作の意味と未確定境界を折りたたみで説明。
- `ConfirmDialog`: Kill Switchなど危険操作の確認・取消・フォーカス移動を提供。

### 2.4 固定ダミーデータ

`seedData`のSeedを`20260811`、基準時刻を`2026-08-11 12:00 JST`に固定した。銘柄は`MCL/M6A/MZC/MZS/MZW`、取引足は`D1/H4/H1/M30/M15`とし、5つの運用単位を正常、警告、未承認、停止の例として表示する。値は説明用の匿名データであり、実シンボル・契約条件・実残高・実Signalを確定するものではない。

## 3. 画面骨格

### 3.1 ホーム（SCREEN-02）

既存Pilotの互換性を維持しつつ、全体指標、5単位の一覧、手動更新・自動更新、候補銘柄・時間足、Dialog/Form/Focusの部品確認を配置した。既存Smokeの`pilot-screen`、MCL行、Backtest対象入力、Base UI Dialogを維持している。

### 3.2 共通Placeholder（SCREEN-01、03〜21）

ナビゲーションから全画面を到達できる。画面ごとの説明、画面ID、E2E ID、現在状態、状態切替ボタン、状態別の進捗・空・失敗表示、HelpTipを同じ骨格で描画する。これは各画面の業務データ実装ではなく、RQU-UI-05で確定した操作・状態・導線を確認するための土台である。

### 3.3 安全操作

ホームの全体Kill Switchは確認Dialogを経由し、確認後は全体状態を`STOPPED`として表示する。実注文や外部停止APIは呼び出さない。Human Gate、Live候補、実接続の承認状態は`UNAPPROVED`または`HUMAN-GATE`の固定表示で表現する。

## 4. 実装ファイル

| ファイル | 変更内容 |
|---|---|
| `ui/mock/src/ui.tsx` | 画面・ナビ・状態・共通部品・固定Seedを追加 |
| `ui/mock/src/App.tsx` | 共通レイアウト、21画面導線、ホーム、状態切替、Kill確認を実装 |
| `ui/mock/src/App.css` | PC/スマホのサイドバー、ドロワー、カード、テーブル、状態、Dialog、focus表示を追加。モバイルでgridの最小幅が横へ溢れないよう`minmax(0, 1fr)`を適用 |
| `ui/mock/src/components/DesignSystem.stories.tsx` | 状態バッジ、警告、進捗、空・失敗、HelpTipのStorybookカタログを追加 |
| `ui/mock/src/App.test.tsx` | 21画面導線、Kill Switch停止状態のコンポーネントテストを追加 |
| `ui/mock/tests/smoke.spec.ts` | 21画面到達、PC/スマホのナビ、既存Dialog Smokeを追加・維持 |

## 5. 検証結果

| コマンド | 結果 | 証拠・補足 |
|---|---|---|
| `npm run test` | `PASS` | 6 tests。既存Pilot 4件＋RQU-UI-07 2件 |
| `npm run build` | `PASS` | TypeScript/Vite build成功 |
| `npm run build-storybook` | `PASS` | Design System storiesを含む静的build成功。chunk警告はOpen |
| `npm run lint` | `PASS_WITH_WARNINGS` | Fast Refresh警告5件のみ。エラー0 |
| `npm run test:e2e` | `PASS` | Chromium desktop/mobile合計5件Pass、mobile専用1件skip |
| 固定Seed確認 | `PASS` | Seed `20260811`、5候補、5時間足 |
| 外部接続確認 | `PASS` | 実Broker・実データ・Secret・実注文・外部API呼出しなし |
| 変更境界 | `PASS` | 正式要件HTML、正式UI HTML、Python、root packageは未変更 |

E2Eのskipはデスクトップでmobile専用シナリオを実行しないための条件分岐であり、失敗をPassへ置換したものではない。

## 6. 追跡・後続Step

RQU-UI-05の21画面、10状態、67ユースケース、40受入IDを後続画面実装へ引き渡した。RQU-UI-08は`NAV-01`〜`NAV-05`の中核画面をこの共通契約上へ実装し、RQU-UI-09以降は残りのナビ・運用状態・検証を追加する。RQU-UI-11でVisual/a11yを確認し、RQU-UI-13で品質・性能・部品のOpen Findingを再評価する。

Q-243の安全境界、初期候補、実行可能性、性能基準はUI上の表示と後続実証を分離したままである。UIの固定値は実証済み性能やLive承認を意味しない。

## 7. 変更履歴

| 版 | 日付 | 内容 |
|---|---|---|
| `v0.1` | 2026-08-11 | RQU-UI-07の共通骨格、状態、固定Seed、Storybook、component/E2E検証を記録。Open Findingを明示した。 |
