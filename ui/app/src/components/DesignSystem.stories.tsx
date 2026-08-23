import type { Meta, StoryObj } from '@storybook/react-vite'
import { EmptyState, ErrorState, HelpTip, LoadingState, ProgressBar, StateAlert, StateBadge, type UiState } from '../ui'

const meta = {
  title: 'RQU-UI-07/Design System',
  parameters: { layout: 'centered' },
  tags: ['autodocs'],
} satisfies Meta

export default meta
type Story = StoryObj<typeof meta>

export const StateBadges: Story = {
  render: () => <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, maxWidth: 620 }}>{(['NORMAL', 'LOADING', 'EMPTY', 'REQUIRED', 'WARNING', 'STOPPED', 'FAILED', 'RECOVERY', 'HUMAN-GATE', 'UNAPPROVED'] as UiState[]).map((state) => <StateBadge key={state} state={state} />)}</div>,
}

export const Alerts: Story = {
  render: () => <div style={{ display: 'grid', gap: 12, width: 540 }}><StateAlert state="WARNING" title="Heartbeatが遅れています">再試行回数と停止条件を確認してください。</StateAlert><StateAlert state="STOPPED" title="安全のため停止しています">照合完了まで再開できません。</StateAlert><StateAlert state="UNAPPROVED" title="未承認">実行に必要な証拠が揃っていません。</StateAlert></div>,
}

export const Progress: Story = {
  render: () => <div style={{ width: 520 }}><ProgressBar value={48} label="網羅検証の進捗（例）" /></div>,
}

export const PlaceholderStates: Story = {
  render: () => <div style={{ display: 'grid', gap: 12, width: 480 }}><LoadingState /><EmptyState actionLabel="準備画面へ" onAction={() => undefined} /><ErrorState /></div>,
}

export const Help: Story = {
  render: () => <div style={{ width: 480 }}><HelpTip title="Human Gateとは？">認証ではなく、運用者が対象と影響を確認して進む安全上の関門です。</HelpTip></div>,
}
