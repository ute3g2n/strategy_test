import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { axe } from 'vitest-axe'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { p4ScreenContracts } from './p4Contract'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('RQU-UI-03 component pilot', () => {
  it('renders deterministic sample data and required controls', () => {
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
    for (const [screenId, contract] of Object.entries(p4ScreenContracts).filter(([screenId]) => !['SCREEN-08', 'SCREEN-09', 'SCREEN-10'].includes(screenId))) {
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
  it('exposes the current Backtest Web画面 condition screen with only supported strategy timeframes', async () => {
    const user = userEvent.setup()
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      const payload = url.endsWith('/api/backtest-product/catalog')
        ? { items: [], available_items: [], strategy_timeframes: ['15m', '30m', '1h', '4h', '1d'], source_timeframe: '1m' }
        : { items: [] }
      return { ok: true, status: 200, json: async () => payload } as Response
    }))
    render(<App />)

    await user.click(screen.getByTestId('nav-SCREEN-08'))
    expect(screen.getByTestId('screen-SCREEN-08')).toHaveAttribute('data-backtest-product-real-api', 'true')
    const timeframe = screen.getByLabelText('戦略時間足')
    expect(timeframe).toHaveTextContent('15m')
    expect(timeframe).toHaveTextContent('30m')
    expect(timeframe).toHaveTextContent('1h')
    expect(timeframe).toHaveTextContent('4h')
    expect(timeframe).toHaveTextContent('1d')
    expect(timeframe).not.toHaveTextContent('1m')
    expect(screen.getByRole('button', { name: '事前確認' })).toBeEnabled()
  })

  it('keeps the completed legacy 1m view behind the explicit legacy-history entry', async () => {
    const user = userEvent.setup()
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, status: 200, json: async () => ({ items: [], available_items: [], strategy_timeframes: ['15m', '30m', '1h', '4h', '1d'], source_timeframe: '1m' }) }) as Response))
    render(<App />)

    await user.click(screen.getByTestId('nav-SCREEN-08'))
    await user.click(screen.getByRole('button', { name: '旧Backtest履歴表示を開く' }))
    expect(screen.getByTestId('screen-SCREEN-08')).toHaveAttribute('data-legacy-backtest-real-api', 'true')
    expect(screen.getByRole('tab', { name: 'Single Run' })).toBeInTheDocument()
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
