import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { axe } from 'vitest-axe'
import { describe, expect, it } from 'vitest'
import App from './App'
import { p4ScreenContracts } from './p4Contract'

describe('RQU-UI-03 component pilot', () => {
  it('renders deterministic mock data and required controls', () => {
    render(<App />)

    expect(screen.getByTestId('pilot-screen')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '自動トレードUI基盤 Smoke' })).toBeInTheDocument()
    expect(screen.getByRole('rowheader', { name: 'MCL' })).toBeInTheDocument()
    expect(screen.getByLabelText('銘柄')).toHaveValue('MCL')
    expect(screen.getByLabelText('時間足')).toHaveValue('D1')
  })

  it('opens and closes the Base UI dialog with keyboard-friendly controls', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: 'Base UI Dialogを開く' }))
    expect(screen.getByRole('dialog', { name: 'Base UIの確認' })).toBeInTheDocument()

    await user.click(screen.getAllByRole('button', { name: '閉じる' })[0])
    expect(screen.queryByRole('dialog', { name: 'Base UIの確認' })).not.toBeInTheDocument()
  })

  it('submits the required form without external I/O', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: '確認する' }))
    expect(screen.getByText('入力内容を確認しました。')).toBeInTheDocument()
  })

  it('has no automated axe violations in the initial state', async () => {
    const { container } = render(<App />)
    const results = await axe(container)
    expect(results.violations).toEqual([])
  })
})

describe('RQU-UI-07 common UI skeleton', () => {
  it('renders all 21 navigation targets and changes the active screen', async () => {
    const user = userEvent.setup()
    render(<App />)

    expect(screen.getAllByTestId(/nav-SCREEN-/)).toHaveLength(21)
    await user.click(screen.getByTestId('nav-SCREEN-21'))
    expect(screen.getByTestId('screen-SCREEN-21')).toBeInTheDocument()
    expect(screen.getAllByRole('heading', { name: 'ヘルプ・用語説明' }).length).toBeGreaterThanOrEqual(2)
  })

  it('binds every screen to the fixed P4 contract and keeps out-of-scope screens fail-closed', async () => {
    const user = userEvent.setup()
    render(<App />)
    for (const [screenId, contract] of Object.entries(p4ScreenContracts)) {
      await user.click(screen.getByTestId(`nav-${screenId}`))
      const strip = screen.getByTestId(`p4-contract-${screenId}`)
      expect(strip).toHaveAttribute('data-p4-scope', contract.scope)
      expect(strip).toHaveAttribute('data-api-p4-ids', contract.apiIds.join(','))
      expect(strip).toHaveAttribute('data-reason-id', contract.reasonId)
    }
    await user.click(screen.getByTestId('nav-SCREEN-14'))
    expect(screen.getByTestId('screen-SCREEN-14')).toHaveAttribute('data-reason-id', 'P4_OUT_OF_SCOPE')
    expect(screen.getByText('P4では実行できません')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '移行を確認' })).not.toBeInTheDocument()
  })

  it('opens the safety stop confirmation and exposes the stopped state after confirmation', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: '全体Kill Switch' }))
    expect(screen.getByRole('dialog', { name: '全体Kill Switchを実行しますか？' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '停止する' }))
    expect(screen.getByText('全体Kill Switchが有効です')).toBeInTheDocument()
    expect(screen.getAllByTestId('state-STOPPED').length).toBeGreaterThan(0)
  })
})

describe('RQU-UI-08 core operation journeys', () => {
  it('exposes the real P5R Backtest tabs and fail-closed start condition', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByTestId('nav-SCREEN-08'))
    expect(screen.getByRole('tab', { name: 'Single Run' })).toBeInTheDocument()
    await user.click(screen.getByRole('tab', { name: 'Sweep' }))
    expect(screen.getByRole('button', { name: 'Sweep開始' })).toBeEnabled()
    await user.click(screen.getByRole('tab', { name: 'Single Run' }))
    expect(screen.getByRole('button', { name: 'Single Run開始' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Preflight実行' })).toBeEnabled()
  })

  it('prevents a duplicate operation unit and saves a distinct combination', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByTestId('nav-SCREEN-04'))
    await user.type(screen.getByLabelText('運用単位Risk'), '1.0')
    expect(screen.getByRole('button', { name: '保存' })).toBeDisabled()
    await user.selectOptions(screen.getByLabelText('銘柄'), 'M6A')
    expect(screen.getByRole('button', { name: '保存' })).toBeEnabled()
    await user.click(screen.getByRole('button', { name: '保存' }))
    expect(screen.getByTestId('screen-SCREEN-03')).toBeInTheDocument()
  })
})

describe('RQU-UI-09 safety and connection journeys', () => {
  it('keeps Secret and Human Gate screens fail-closed in the P4 boundary', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByTestId('nav-SCREEN-20'))
    expect(screen.getByTestId('screen-SCREEN-20')).toHaveAttribute('data-reason-id', 'P4_OUT_OF_SCOPE')
    expect(screen.getByText('P4では実行できません')).toBeInTheDocument()
    await user.click(screen.getByTestId('nav-SCREEN-18'))
    expect(screen.getByTestId('screen-SCREEN-18')).toHaveAttribute('data-reason-id', 'P4_H2_REQUIRED')
    expect(screen.queryByRole('button', { name: '移行を確認' })).not.toBeInTheDocument()
  })
})
