import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { P5RBacktestScreen } from './P5RBacktestScreen'
import type { ScreenDefinition } from './ui'

const screen08: ScreenDefinition = {
  id: 'SCREEN-08',
  title: 'Backtest条件設定',
  navId: 'NAV-02',
  description: 'P5Rの旧Backtest条件',
  defaultState: 'REQUIRED',
  e2eId: 'P5R-UI-01',
}

const response = (payload: unknown, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: async () => payload,
}) as Response

function installApiMock() {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url.endsWith('/api/backtest/runs/history')) return response({ items: [] })
    if (url.endsWith('/api/backtest/recovery')) return response({ status: 'CLEAN', issues: [], recovery_required_run_ids: [], restored_run_count: 0 })
    if (url.endsWith('/api/backtest/preflight')) return response({ status: 'PASS', checks: [] })
    return response({ ok: false, error: { code: 'NOT_FOUND' } }, 404)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('P5R legacy Backtest datetime inputs', () => {
  it('uses UTC datetime pickers and preserves the existing API UTC payload', async () => {
    const user = userEvent.setup()
    const fetchMock = installApiMock()
    render(<P5RBacktestScreen screen={screen08} demoState="REQUIRED" onStateChange={() => undefined} />)

    const start = screen.getByLabelText('開始日時（UTC）')
    const end = screen.getByLabelText('終了日時（UTC）')
    expect(start).toHaveAttribute('type', 'datetime-local')
    expect(end).toHaveAttribute('type', 'datetime-local')
    expect(start).toHaveValue('2025-02-24T00:00')
    expect(end).toHaveValue('2025-02-24T02:30')

    fireEvent.change(start, { target: { value: '2025-02-24T01:00' } })
    await user.click(screen.getByRole('button', { name: 'Preflight実行' }))

    const preflightCalls = () => fetchMock.mock.calls.filter(([url]) => String(url).endsWith('/api/backtest/preflight'))
    await waitFor(() => expect(preflightCalls()).toHaveLength(1))
    const body = JSON.parse(String(preflightCalls()[0]?.[1]?.body)) as { spec: { start: string; end: string } }
    expect(body.spec.start).toBe('2025-02-24T01:00:00Z')
    expect(body.spec.end).toBe('2025-02-24T02:30:00Z')

    fireEvent.change(end, { target: { value: '2025-02-24T01:00' } })
    await user.click(screen.getByRole('button', { name: 'Preflight実行' }))
    expect(preflightCalls()).toHaveLength(1)
    expect(screen.getByText('開始日時は終了日時より前にしてください。')).toBeVisible()
  })
})
