CodeX（OpenAI CodeX CLI や IDE 拡張など）の基盤上で利用可能なサブエージェント（Sub-agents）やスキル（Skills / Customs Workflows）に絞り、React + Vite でのフロントエンド実装・画面モック作成において世の中で超人気・高評価を得ているものを厳選して解説します。

CodeX では、環境構築コマンドの自動実行、ファイルの差分適用、マルチファイルコンテキストの読み込みが得意なため、これらを補強・拡張するツールやシステムプロンプト構成が定番化しています。

---

## 1. 超人気のフロントエンド用「Skill / Prompt Custom Instructions」

CodeX の動作精度（コンポーネント分割、TypeScriptの型定義、Tailwindの命名規則など）を劇的に向上させるための、世の中で最もシェアの高いスキル指示ルールです。

### ① `shadcn-ui-builder` スキル

* **概要**: CodeX に `shadcn/ui`（Radix UI + Tailwind）コンポーネントを自動生成・導入させるためのスキルセット。
* **役割**: 単に JSX を出力するだけでなく、CodeX に `npx shadcn-ui@latest add [component]` などの CLI コマンドを自律実行させ、依存関係のインストールから `src/components/ui` への自動配置までを完結させます。
* **画面モックでの強み**: 「モダンなダッシュボードのモックを作って」と指示するだけで、ボタン、ダイアログ、テーブルなどの UI 部品を自前で作らず `shadcn` を使って一気に組み上げます。

### ② `mock-data-generator` (Faker.js 連携スキル)

* **概要**: リアリティのある画面モックを作るため、仮データ（ユーザー一覧、売上データ、取引履歴など）を自動生成するスキル。
* **役割**: `faker` ライブラリを用いたダミーデータ生成コードや Zustand 状態保持ストア（`useMockStore`）を同時に構築させます。
* **効果**: 静的な見た目だけでなく、フィルター操作やページネーションが**実際に手元で動くインタラクティブな画面モック**が一瞬で完成します。

### ③ `vite-component-structure` (アトミック／フィーチャー分割スキル)

* **概要**: CodeX が巨大な1ファイルにコードをまとめがちな癖を防ぎ、Vite のベストプラクティスに沿ったファイル構成に強制分割させるスキル。
* **ルール内容**:
```markdown
- src/features/[feature-name]/components/ に画面専用モックを配置
- src/components/ui/ に共通パーツを配置
- 各コンポーネントは TypeScript (strict) + Props 型定義を必須とする

```



---

## 2. CodeX と連携して動作する「サブエージェント／プラグイン」

CodeX のエコシステム内で、フロントエンド開発者から圧倒的な支持を集めている外部連携（MCP / Sub-agent）ツールです。

### ① v0-to-CodeX Sub-Agent (v0 / Shadcn 連携エージェント)

* **概要**: Vercel の v0 で生成したプロトタイプコードを、CodeX 経由で直接ローカルの Vite プロジェクトに整形導入するサブエージェント。
* **動作フロー**:
1. ブラウザ側（v0）でデザインモックを作成。
2. CodeX のサブエージェントに URL やコンポーネントコードを渡す。
3. サブエージェントが自律的に Vite の依存関係（`package.json`）をチェックし、足りない Tailwind プラグインやアイコン（`lucide-react`）を自動インストールしてプロジェクトに組み込む。



### ② Playwright Visual Regression Agent (視覚的モック検証エージェント)

* **概要**: CodeX が生成した Vite アプリ（`http://localhost:5173`）を裏でブラウザ駆動し、見た目の崩れやレスポンシブデザインを自動検証・自己修復するエージェント。
* **役割**: 画面モック作成時、モバイル（スマホ）表示とデスクトップ表示のレイアウト崩れを自動検出して、Tailwind のブレークポイント（`md:`, `lg:` など）を修正させます。

---

## 3. 実践：CodeX 用の推奨 `Skill` 定義コード

CodeX の設定ファイル（`.codex/rules` やシステムプロンプト設定など）に登録して使われている、人気のスキル定義文（React + Vite モック作成用）です。

```markdown
# Role: Front-End Mock Engineer (Vite + React)

## Capabilities & Skills:
1. **UI Stack**: Standardize on React, TypeScript, Tailwind CSS, and Lucide Icons.
2. **Component Library**: Prefer `shadcn/ui` patterns for primitives (Buttons, Cards, Dialogs, Inputs).
3. **State & Mocking**:
   - Use Zustand for glabal UI state.
   - Inject rich, realistic mock data using hardcoded mock files in `src/mocks/`.
4. **Vite Execution**:
   - If a new package is required (e.g. `lucide-react`, `clsx`), issue the shell command `npm install <package>`.
   - Ensure `vite.config.ts` path aliases (`@/`) are properly handled.

## Mock Creation Rule:
When asked to create a screen mock:
1. Generate the type definition first in `src/types/`.
2. Generate mock data in `src/mocks/`.
3. Create composable UI elements in `src/components/`.
4. Assemble the full screen mock inside `src/pages/` or `src/features/`.

```

---