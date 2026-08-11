import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { axe } from 'vitest-axe'
import { describe, expect, it } from 'vitest'
import App from './App'

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
  it('keeps exhaustive Backtest disabled until Risk is entered and then moves to progress', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByTestId('nav-SCREEN-08'))
    await user.click(screen.getByRole('tab', { name: '網羅検証' }))
    expect(screen.getByRole('button', { name: '開始' })).toBeDisabled()
    await user.type(screen.getByLabelText('Risk'), '1.0')
    expect(screen.getByRole('button', { name: '開始' })).toBeEnabled()
    await user.click(screen.getByRole('button', { name: '開始' }))
    expect(screen.getByTestId('screen-SCREEN-09')).toBeInTheDocument()
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
  it('does not expose Secret values and requires Risk for Human Gate', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByTestId('nav-SCREEN-20'))
    expect(screen.getByText(/値は非表示/)).toBeInTheDocument()
    expect(screen.getByText('未設定・未承認')).toBeInTheDocument()
    await user.click(screen.getByTestId('nav-SCREEN-18'))
    expect(screen.getByRole('button', { name: '移行を確認' })).toBeDisabled()
    await user.type(screen.getByLabelText('Risk'), '1.0')
    expect(screen.getByRole('button', { name: '移行を確認' })).toBeEnabled()
  })
})
