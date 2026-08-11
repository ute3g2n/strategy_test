import { useId, type ReactNode } from 'react'
import * as RadixDialog from '@radix-ui/react-dialog'

export type UiState =
  | 'NORMAL'
  | 'LOADING'
  | 'EMPTY'
  | 'REQUIRED'
  | 'WARNING'
  | 'STOPPED'
  | 'FAILED'
  | 'RECOVERY'
  | 'HUMAN-GATE'
  | 'UNAPPROVED'

export type ScreenId = `SCREEN-${string}`

export type ScreenDefinition = {
  id: ScreenId
  title: string
  navId: string
  description: string
  defaultState: UiState
  e2eId: string
}

export type NavGroup = {
  id: string
  label: string
  screens: ScreenDefinition[]
}

const screen = (
  id: ScreenId,
  title: string,
  navId: string,
  description: string,
  defaultState: UiState,
  e2eId: string,
): ScreenDefinition => ({ id, title, navId, description, defaultState, e2eId })

export const navGroups: NavGroup[] = [
  {
    id: 'NAV-01',
    label: 'ホーム',
    screens: [
      screen('SCREEN-01', 'システム状態・禁止事項', 'NAV-01', '認証不要、禁止事項、未承認項目を確認します。', 'UNAPPROVED', 'E2E-UI-001'),
      screen('SCREEN-02', 'ホーム／全体ダッシュボード', 'NAV-01', '全運用単位と最新の状態をまとめて確認します。', 'NORMAL', 'E2E-UI-070'),
      screen('SCREEN-17', '警告・障害・通知', 'NAV-01', '警告、停止理由、復旧手順を確認します。', 'WARNING', 'E2E-UI-071'),
    ],
  },
  {
    id: 'NAV-02',
    label: 'Backtest設定',
    screens: [screen('SCREEN-08', 'Backtest条件設定', 'NAV-02', '単一Runまたは網羅検証の条件を入力します。', 'REQUIRED', 'E2E-UI-030')],
  },
  {
    id: 'NAV-03',
    label: '網羅検証設定',
    screens: [screen('SCREEN-09', 'Backtest実行一覧・進捗', 'NAV-03', '待ち行列、進捗、取消、失敗理由を確認します。', 'LOADING', 'E2E-UI-033')],
  },
  {
    id: 'NAV-04',
    label: '結果・比較',
    screens: [
      screen('SCREEN-10', 'Backtest結果サマリー', 'NAV-04', '5指標と結果の概要を確認します。', 'NORMAL', 'E2E-UI-036'),
      screen('SCREEN-11', 'チャート・取引・Signal詳細', 'NAV-04', '資産曲線、取引、Signal、想定との差分を確認します。', 'NORMAL', 'E2E-UI-057'),
      screen('SCREEN-12', 'Run比較', 'NAV-04', '複数Runを比較し、運用者が判断します。', 'EMPTY', 'E2E-UI-038'),
    ],
  },
  {
    id: 'NAV-05',
    label: '運用単位',
    screens: [
      screen('SCREEN-03', '運用単位一覧', 'NAV-05', '銘柄×時間足×売買ルールの独立単位を確認します。', 'NORMAL', 'E2E-UI-006'),
      screen('SCREEN-04', '運用単位の作成・編集', 'NAV-05', '銘柄、時間足、Strategy、Risk、モードを設定します。', 'REQUIRED', 'E2E-UI-025'),
      screen('SCREEN-06', 'Strategy一覧', 'NAV-05', 'Turtle System 1/2と設定版を管理します。', 'NORMAL', 'E2E-UI-005'),
      screen('SCREEN-07', 'Strategy設定', 'NAV-05', '売買ルールの条件を検証して新版を作ります。', 'NORMAL', 'E2E-UI-021'),
    ],
  },
  {
    id: 'NAV-06',
    label: '銘柄・データ',
    screens: [screen('SCREEN-05', '市場データ・品質', 'NAV-06', '5候補、5時間足、データ品質、由来を確認します。', 'WARNING', 'E2E-UI-014')],
  },
  {
    id: 'NAV-07',
    label: 'Risk・注文',
    screens: [
      screen('SCREEN-15', 'Portfolio・Account・Risk', 'NAV-07', '総残高、証拠金、余力、Riskを確認します。', 'REQUIRED', 'E2E-UI-062'),
      screen('SCREEN-16', '注文・約定・Position', 'NAV-07', '仮想・模擬・実注文の区分と照合を確認します。', 'WARNING', 'E2E-UI-064'),
    ],
  },
  {
    id: 'NAV-08',
    label: '運用・昇格',
    screens: [
      screen('SCREEN-13', 'Forward／Shadowダッシュボード', 'NAV-08', 'ForwardとShadowの状態、停止、照合を確認します。', 'HUMAN-GATE', 'E2E-UI-051'),
      screen('SCREEN-14', 'Paper／Liveダッシュボード', 'NAV-08', 'Paper、Live候補、Liveの承認状態を確認します。', 'UNAPPROVED', 'E2E-UI-054'),
      screen('SCREEN-18', 'Human Gate・移行確認', 'NAV-08', '運用者が対象、Risk、証拠を確認する関門です。', 'HUMAN-GATE', 'E2E-UI-083'),
    ],
  },
  {
    id: 'NAV-09',
    label: 'ログ・操作記録',
    screens: [screen('SCREEN-19', '監査ログ・証跡', 'NAV-09', 'Run、設定版、操作、Gate、削除を検索します。', 'NORMAL', 'E2E-UI-081')],
  },
  {
    id: 'NAV-10',
    label: '設定・接続',
    screens: [
      screen('SCREEN-20', '接続先・Secret・通知設定', 'NAV-10', '接続状態とSecretの存在だけを確認します。', 'UNAPPROVED', 'E2E-UI-003'),
      screen('SCREEN-21', 'ヘルプ・用語説明', 'NAV-10', '専門用語と画面の意味を平易に確認します。', 'NORMAL', 'E2E-UI-002'),
    ],
  },
]

export const allScreens = navGroups.flatMap((group) => group.screens)

export const stateLabels: Record<UiState, string> = {
  NORMAL: '通常',
  LOADING: '読込中',
  EMPTY: 'データなし',
  REQUIRED: '入力が必要',
  WARNING: '警告',
  STOPPED: '停止',
  FAILED: '失敗',
  RECOVERY: '復旧確認中',
  'HUMAN-GATE': '運用者確認待ち',
  UNAPPROVED: '未承認',
}

export const stateDescriptions: Record<UiState, string> = {
  NORMAL: '通常の操作を続けられます。',
  LOADING: '処理中です。進捗と取消可能かを確認してください。',
  EMPTY: '表示できるデータがありません。作成または条件を変えてください。',
  REQUIRED: '開始前に必要な入力があります。',
  WARNING: '影響と次の操作を確認してください。',
  STOPPED: '安全のため停止しています。再開条件を確認してください。',
  FAILED: '処理に失敗しました。理由と再試行可否を確認してください。',
  RECOVERY: 'データ・注文・Positionの照合が終わるまで再開できません。',
  'HUMAN-GATE': '運用者が対象と影響を確認して進む関門です。',
  UNAPPROVED: '必要な承認・実証が未完了です。実行できません。',
}

export type StateBadgeProps = { state: UiState; compact?: boolean }

export function StateBadge({ state, compact = false }: StateBadgeProps) {
  return (
    <span className={`state-badge state-${state.toLowerCase().replace('-', '-')}`} data-testid={`state-${state}`} role="status">
      <span className="state-dot" aria-hidden="true" />
      <span>{compact ? state : `${state} / ${stateLabels[state]}`}</span>
    </span>
  )
}

export function StateAlert({ state, title, children }: { state: UiState; title?: string; children?: ReactNode }) {
  return (
    <div className={`state-alert alert-${state.toLowerCase().replace('-', '-')}`} role={state === 'WARNING' || state === 'FAILED' ? 'alert' : 'status'}>
      <StateBadge state={state} compact />
      <div>
        <strong>{title ?? stateLabels[state]}</strong>
        <p>{children ?? stateDescriptions[state]}</p>
      </div>
    </div>
  )
}

export function MetricCard({ label, value, detail, tone = 'neutral' }: { label: string; value: string; detail: string; tone?: 'neutral' | 'positive' | 'warning' }) {
  return (
    <article className={`metric-card metric-${tone}`}>
      <p>{label}</p>
      <strong>{value}</strong>
      <span>{detail}</span>
    </article>
  )
}

export function ProgressBar({ value, label }: { value: number; label: string }) {
  const safeValue = Math.max(0, Math.min(100, value))
  return (
    <div className="progress-wrap" aria-label={label}>
      <div className="progress-label"><span>{label}</span><strong>{safeValue}%</strong></div>
      <div className="progress-track"><span style={{ width: `${safeValue}%` }} /></div>
    </div>
  )
}

export function LoadingState({ label = '読み込んでいます' }: { label?: string }) {
  return <div className="placeholder-state"><span className="spinner" aria-hidden="true" /><strong>{label}</strong><span>画面を閉じても処理は安全に管理されます。</span></div>
}

export function EmptyState({ title = 'データがありません', actionLabel, onAction }: { title?: string; actionLabel?: string; onAction?: () => void }) {
  return (
    <div className="placeholder-state empty-state">
      <span className="empty-icon" aria-hidden="true">∅</span>
      <strong>{title}</strong>
      <span>条件を変えるか、準備画面から作成してください。</span>
      {actionLabel && onAction && <button className="secondary-button" type="button" onClick={onAction}>{actionLabel}</button>}
    </div>
  )
}

export function ErrorState({ title = '処理に失敗しました', detail = '原因と次の操作を確認してください。' }: { title?: string; detail?: string }) {
  return <div className="placeholder-state error-state"><span className="error-icon" aria-hidden="true">!</span><strong>{title}</strong><span>{detail}</span></div>
}

export function HelpTip({ title, children }: { title: string; children: ReactNode }) {
  const id = useId()
  return <details className="help-tip"><summary aria-controls={id}>{title}</summary><p id={id}>{children}</p></details>
}

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = '確認して進む',
  cancelLabel = '取消',
  onConfirm,
  danger = false,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description: string
  confirmLabel?: string
  cancelLabel?: string
  onConfirm: () => void
  danger?: boolean
}) {
  return (
    <RadixDialog.Root open={open} onOpenChange={onOpenChange}>
      <RadixDialog.Portal>
        <RadixDialog.Overlay className="dialog-backdrop" />
        <RadixDialog.Content className="dialog-popup" aria-describedby="confirm-dialog-description">
          <RadixDialog.Title>{title}</RadixDialog.Title>
          <RadixDialog.Description id="confirm-dialog-description">{description}</RadixDialog.Description>
          <div className="dialog-actions">
            <RadixDialog.Close asChild><button className="secondary-button" type="button">{cancelLabel}</button></RadixDialog.Close>
            <button className={danger ? 'danger-button' : 'primary-button'} type="button" onClick={onConfirm}>{confirmLabel}</button>
          </div>
        </RadixDialog.Content>
      </RadixDialog.Portal>
    </RadixDialog.Root>
  )
}

export const seedData = {
  seed: 20260811,
  asOf: '2026-08-11 12:00 JST',
  symbols: ['MCL', 'M6A', 'MZC', 'MZS', 'MZW'],
  timeframes: ['D1', 'H4', 'H1', 'M30', 'M15'],
  units: [
    { id: 'UNIT-001', symbol: 'MCL', timeframe: 'D1', rule: 'Turtle System 1', mode: 'Backtest', state: 'NORMAL' as UiState, signal: '待機', position: '0', warning: 'なし' },
    { id: 'UNIT-002', symbol: 'M6A', timeframe: 'H4', rule: 'Turtle System 2', mode: 'Shadow', state: 'WARNING' as UiState, signal: '確認待ち', position: 'Long 1', warning: 'Heartbeat 1分遅延' },
    { id: 'UNIT-003', symbol: 'MZC', timeframe: 'H1', rule: 'Turtle System 1', mode: 'Paper', state: 'UNAPPROVED' as UiState, signal: '未承認', position: '0', warning: '実シンボル未確認' },
    { id: 'UNIT-004', symbol: 'MZS', timeframe: 'M30', rule: 'Turtle System 2', mode: 'Forward', state: 'STOPPED' as UiState, signal: '停止', position: 'Short 1', warning: 'データ照合待ち' },
    { id: 'UNIT-005', symbol: 'MZW', timeframe: 'M15', rule: 'Turtle System 1', mode: 'Backtest', state: 'NORMAL' as UiState, signal: 'Entry候補', position: '0', warning: 'なし' },
  ],
}
