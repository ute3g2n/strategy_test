import type { ScreenId } from './ui'

export type P4ScreenScope = 'P4_TARGET' | 'P4_BOUNDARY_TARGET' | 'BOUNDARY_ONLY'

export type P4ScreenContract = {
  scope: P4ScreenScope
  apiIds: readonly string[]
  reasonId: string
  allowed: string
  prohibited: string
}

const boundaryOnly: P4ScreenContract = {
  scope: 'BOUNDARY_ONLY', apiIds: ['API-P4-001'], reasonId: 'P4_OUT_OF_SCOPE',
  allowed: '固定匿名情報、後続PhaseとHuman Gateの表示', prohibited: '外部接続、注文、実Risk、Secret、Paper／Liveの開始',
}

export const p4ScreenContracts: Record<ScreenId, P4ScreenContract> = {
  'SCREEN-01': { scope: 'P4_BOUNDARY_TARGET', apiIds: ['API-P4-001'], reasonId: 'P4_LOCAL_ONLY', allowed: 'Capabilityと禁止事項の表示、Help／Gateへの移動', prohibited: '外部I/O、実運用開始' },
  'SCREEN-02': { scope: 'P4_TARGET', apiIds: ['API-P4-001', 'API-P4-006', 'API-P4-009', 'API-P4-012'], reasonId: 'P4_FIXED_DUMMY', allowed: '検証済み集約viewの表示と画面遷移', prohibited: 'Jobの直接開始・取消' },
  'SCREEN-03': { scope: 'P4_TARGET', apiIds: ['API-P4-006', 'API-P4-007', 'API-P4-009', 'API-P4-012'], reasonId: 'P4_FIXED_DUMMY', allowed: '運用単位の匿名一覧表示', prohibited: '外部Data／実Mode変更' },
  'SCREEN-04': { scope: 'P4_TARGET', apiIds: ['API-P4-002', 'API-P4-003'], reasonId: 'P4_LOCAL_PRECHECK', allowed: '固定入力のPreflight表示', prohibited: 'Secret・絶対path・外部Dataの投入' },
  'SCREEN-05': boundaryOnly, 'SCREEN-06': boundaryOnly, 'SCREEN-07': boundaryOnly,
  'SCREEN-08': { scope: 'P4_TARGET', apiIds: ['API-P4-002', 'API-P4-003', 'API-P4-004'], reasonId: 'P4_LOCAL_PRECHECK', allowed: '固定dummyのSingle／Sweep条件とPreflight', prohibited: '未検証条件・実Riskでの開始' },
  'SCREEN-09': { scope: 'P4_TARGET', apiIds: ['API-P4-002', 'API-P4-005', 'API-P4-007', 'API-P4-008', 'API-P4-009', 'API-P4-010', 'API-P4-011', 'API-P4-012', 'API-P4-018'], reasonId: 'P4_RESULT_REFERENCE_ONLY', allowed: 'Run／Job／Queueの固定viewと許可済み操作表示', prohibited: 'stale revision・marker/hash不一致の成功表示' },
  'SCREEN-10': { scope: 'P4_TARGET', apiIds: ['API-P4-005', 'API-P4-006', 'API-P4-013', 'API-P4-014', 'API-P4-015', 'API-P4-016', 'API-P4-017', 'API-P4-018', 'API-P4-019'], reasonId: 'P4_RESULT_REFERENCE_ONLY', allowed: '結果要約とCSV／Evidence参照の表示', prohibited: 'result本文・file bytes・絶対pathの表示' },
  'SCREEN-11': { scope: 'P4_TARGET', apiIds: ['API-P4-013', 'API-P4-014', 'API-P4-018'], reasonId: 'P4_RESULT_REFERENCE_ONLY', allowed: '固定結果detailの表示', prohibited: '未検証resultの表示' },
  'SCREEN-12': { scope: 'P4_TARGET', apiIds: ['API-P4-005', 'API-P4-006', 'API-P4-013', 'API-P4-014', 'API-P4-015', 'API-P4-016', 'API-P4-017', 'API-P4-018', 'API-P4-019'], reasonId: 'P4_RESULT_REFERENCE_ONLY', allowed: '固定Run比較とEvidence参照', prohibited: '結果本文・外部export' },
  'SCREEN-13': boundaryOnly, 'SCREEN-14': boundaryOnly, 'SCREEN-15': boundaryOnly, 'SCREEN-16': boundaryOnly,
  'SCREEN-17': { scope: 'P4_BOUNDARY_TARGET', apiIds: ['API-P4-008', 'API-P4-009', 'API-P4-010', 'API-P4-011', 'API-P4-018'], reasonId: 'P4_FAILURE_FAIL_CLOSED', allowed: 'reason ID、停止・復旧条件、Evidence参照の表示', prohibited: '外部通知・force resume' },
  'SCREEN-18': { scope: 'P4_BOUNDARY_TARGET', apiIds: ['API-P4-001', 'API-P4-019'], reasonId: 'P4_H2_REQUIRED', allowed: 'P4-H2の対象・証拠・再開条件の表示', prohibited: '自動承認、Paper／Live移行' },
  'SCREEN-19': { scope: 'P4_TARGET', apiIds: ['API-P4-001', 'API-P4-005', 'API-P4-006', 'API-P4-008', 'API-P4-009', 'API-P4-013', 'API-P4-014', 'API-P4-015', 'API-P4-016', 'API-P4-017', 'API-P4-018', 'API-P4-019'], reasonId: 'P4_AUDIT_REFERENCE_ONLY', allowed: '固定Audit／Evidence参照の表示', prohibited: '削除、外部export、Secret表示' },
  'SCREEN-20': boundaryOnly,
  'SCREEN-21': { scope: 'P4_BOUNDARY_TARGET', apiIds: ['API-P4-001', 'API-P4-005', 'API-P4-008', 'API-P4-018', 'API-P4-019'], reasonId: 'P4_LOCAL_ONLY', allowed: '用語、P4境界、画面移動の説明', prohibited: '外部接続設定の変更' },
}
