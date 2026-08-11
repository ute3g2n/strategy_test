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
