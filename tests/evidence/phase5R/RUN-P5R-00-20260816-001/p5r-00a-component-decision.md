# P5R-00A AI部品再利用判定

## 判定

`P5R-COMP-01 = CREATE_REQUIRED`。手順書専用部品は作らない。既存の実装品質Orchestratorを再利用し、Web製品UIの実Application API接続だけを担う汎用Skill/Agentを最小追加する。

## 責務ごとの調査

| 責務 | 既存部品 | 再利用可否 | 判定理由と境界 |
|---|---|---|---|
| Python Backtest/Application | `AutoTradeProject_ImplementationQuality_Orchestrator_v0_1`、A110/A120/A130/A140/A150/A160、Python系Skill | REUSE | Core/ApplicationのPython実装と品質Gateを担当する。React/TypeScriptのUI責務は持たない。 |
| React/TypeScript実製品UI | A170、UI mock Skill | 不十分 | A170は固定Seedの匿名ダミーUI専用で、実Application API接続を責務にできない。実結果を生成しない境界も維持する必要がある。 |
| 固定UI構造・visual/a11y | A170、A171、`autotrade_skill_ui_mock_generation_v0_1`、visual/a11y Skill | REUSE | 既存画面の構造移行補助と、固定条件のvisual/a11yレビューに限定して使う。P5R実結果の証拠生成担当にはしない。 |
| Playwright操作・assert・PNG | `@playwright/test`、既存P4 spec、e2e-testing Skill | REUSE | P5R固有のPage Objectとcapture registryは実装側で作る。AI部品を専用新設しない。 |
| HTML手順書・画像採用・索引・追跡 | A80/A81、HTML writer/design-doc Skill | REUSE | 実画像の採用規則と追跡を文書側で統合する。手順書専用Agent/Skillは作らない。 |

## 追加部品

- `autotrade_skill_web_product_ui_implementation_v0_1`
- `AutoTrade_A172_WebProductUiEngineer_v0_1`
- 新しいOrchestratorは作らず、`AutoTradeProject_ImplementationQuality_Orchestrator_v0_1`へA172/Skillを登録する。

## 禁止する拡張

外部UI SDK、外部通信、Broker、Secret、認証・権限、実注文、実口座、実資金、Cloudを追加しない。A171の視覚・アクセシビリティレビュー、A80の手順書統合、A120のPython責務を奪わない。
