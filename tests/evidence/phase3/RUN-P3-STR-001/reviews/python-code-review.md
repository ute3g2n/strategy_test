# P3-06 Python / 取引安全レビュー

- 判定: APPROVE
- Critical: 0
- High: 0
- Medium: 0
- 対象: `src/autotrade/strategy/`、`tests/strategy/`、v1/v2/v3 fixture、`RUN-P3-STR-001`

## 確認したこと

- M30は実体の確定M1を連続30本確認できる場合だけ使う。不足・重複・逆行・M15由来・異常OHLCVは停止する。
- v2は当時の期待値を含む履歴証跡として保持し、実行時の安全な正本はv3とする。
- System 1、System 1の安全側55本版、System 2は設定で独立に選べる。勝ったSystem 1が勝手にSystem 2へ変わらない。
- 同時に閉じた複数時間足は、全Viewを更新してから一度だけ判断する。120通りの到着順で結果と状態が一致する。
- 古いCampaign通知は再適用しないが、新しい市場バーを捨てない。古い水位への巻き戻しや同じ水位で内容が違う通知は停止する。
- Entry/Addは正のstrategy unit hint、Exit/2N Stopは`FLAT / 0`のTargetPositionを返す。
- 時計、ネットワーク、Broker、engine SDK、Secret、外部I/Oへの依存はない。

やさしい説明: 30分足の材料を数えずに通す穴、古い連絡で新しい記録を戻す穴、同時に届く資料の順番で答えが変わる穴を、全部テストでふさいだ。危ない入力なら売買の合図を出さずに止まる。
