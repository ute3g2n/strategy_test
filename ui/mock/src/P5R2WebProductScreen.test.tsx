import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { axe } from 'vitest-axe'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { P5R2WebProductScreen } from './P5R2WebProductScreen'
import type { ScreenDefinition } from './ui'

const screen08: ScreenDefinition = {
  id: 'SCREEN-08',
  title: 'Backtest条件設定',
  navId: 'NAV-02',
  description: 'P5R2の条件設定',
  defaultState: 'REQUIRED',
  e2eId: 'P5R2-UI-01',
}

const catalog = {
  items: [{
    dataset_id: 'DATASET-SOURCE-BTCUSDT-1m',
    identity: { provider: 'LOCAL_FAKE', market: 'SPOT', symbol: 'BTCUSDT', source_timeframe: '1m', schema: 'ohlcv-v1' },
    symbol: 'BTCUSDT',
    source_timeframe: '1m',
    data_timeframe: '1m',
    coverage: { start: '2025-02-24T00:00:00Z', end: '2025-02-24T03:00:00Z' },
    quality: 'USABLE',
    usable: true,
    legacy: false,
    state: 'CURRENT',
    provenance: { source_job_id: 'JOB-SOURCE-001' },
  }],
  available_items: [],
  strategy_timeframes: ['15m', '30m', '1h', '4h', '1d'],
  source_timeframe: '1m',
}

const insufficient = {
  status: 'STOPPED',
  checks: [{ id: 'DATA_COVERAGE', status: 'FAIL', message: '必要な上位足DataがCatalogにありません。' }],
  failure: { code: 'DATA_INSUFFICIENT', message: '指定期間の指定時間足がありません。時間足を生成してください。', retryable: false },
  data_requirement: {
    symbol: 'BTCUSDT',
    timeframe: '30m',
    requested_range: { start: '2025-02-24T00:00:00Z', end: '2025-02-24T01:00:00Z' },
    source_timeframe: '1m',
  },
}

const response = (payload: unknown, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: async () => payload,
}) as Response

afterEach(() => {
  vi.unstubAllGlobals()
})

function installApiMock(runs: unknown[] = []) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input)
    if (url.endsWith('/api/p5r2/catalog')) return response(catalog)
    if (url.endsWith('/api/backtest/runs')) return response({ items: runs })
    if (url.endsWith('/api/p5r2/backtest/preflight')) return response(insufficient, 422)
    if (url.endsWith('/api/p5r2/timeframe-generation-jobs')) {
      expect(init?.method).toBe('POST')
      return response({ job_id: 'JOB-TIMEFRAME_GENERATION-UI-001', job_type: 'TIMEFRAME_GENERATION', state: 'STAGED', reason: 'TIMEFRAME_GENERATION_VALIDATION_REQUIRED', external_io_performed: false })
    }
    if (url.endsWith('/api/p5r2/result-artifacts/delete')) {
      expect(init?.method).toBe('POST')
      return response({
        logical_artifact_id: 'RESULT-OWNER-RUN-UI-001',
        artifact_kind: 'RESULT',
        accepted: true,
        deleted: true,
        status: 'RESULT_DELETED',
        artifact_state: 'DELETED',
        physical_io_performed: true,
      })
    }
    return response({ ok: false, error: { code: 'NOT_FOUND' } }, 404)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('P5R2 Web Product UI', () => {
  it('uses only the five strategy timeframes and sends the missing-data journey to the local generation API', async () => {
    const user = userEvent.setup()
    const fetchMock = installApiMock()
    render(<P5R2WebProductScreen screen={screen08} onOpenLegacy={() => undefined} />)

    await waitFor(() => expect(screen.getByTestId('p5r2-catalog-table')).toBeInTheDocument())
    const timeframeSelect = screen.getByLabelText('戦略時間足')
    expect(timeframeSelect).toHaveTextContent('15m')
    expect(timeframeSelect).toHaveTextContent('30m')
    expect(timeframeSelect).toHaveTextContent('1h')
    expect(timeframeSelect).toHaveTextContent('4h')
    expect(timeframeSelect).toHaveTextContent('1d')
    expect(timeframeSelect).not.toHaveTextContent('1m')

    await user.click(screen.getByRole('button', { name: '時間足生成画面を開く' }))
    expect(screen.getByTestId('p5r2-generation-form')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: '事前確認' }))
    const dialog = await screen.findByRole('dialog', { name: '指定期間の時間足Dataが不足しています' })
    expect(dialog).toHaveTextContent('BTCUSDT / 30m')
    await user.click(screen.getByRole('button', { name: '時間足を生成する' }))

    expect(screen.getByTestId('p5r2-generation-form')).toBeInTheDocument()
    expect(screen.getByLabelText('生成開始日時（UTC）')).toHaveAttribute('type', 'datetime-local')
    expect(screen.getByLabelText('生成終了日時（UTC）')).toHaveAttribute('type', 'datetime-local')
    expect(screen.getByLabelText('生成開始日時（UTC）')).toHaveValue('2025-02-24T00:00')
    expect(screen.getByLabelText('生成終了日時（UTC）')).toHaveValue('2025-02-24T03:00')
    expect(screen.getByRole('checkbox', { name: '30m' })).toBeChecked()
    await user.click(screen.getByRole('button', { name: '時間足を生成する' }))

    await waitFor(() => expect(screen.getAllByText('JOB-TIMEFRAME_GENERATION-UI-001', { exact: false }).length).toBeGreaterThan(0))
    const generationCall = fetchMock.mock.calls.find(([url]) => String(url).endsWith('/api/p5r2/timeframe-generation-jobs'))
    expect(generationCall).toBeDefined()
    const body = JSON.parse(String(generationCall?.[1]?.body)) as Record<string, unknown>
    expect(body).toMatchObject({
      source_dataset_id: 'DATASET-SOURCE-BTCUSDT-1m',
      symbol: 'BTCUSDT',
      timeframes: ['30m'],
      external_io_allowed: false,
    })
    expect(body).not.toHaveProperty('source_dataset')
  })

  it('serializes P5R2 condition datetime pickers as UTC and blocks a reversed range', async () => {
    const user = userEvent.setup()
    const fetchMock = installApiMock()
    render(<P5R2WebProductScreen screen={screen08} onOpenLegacy={() => undefined} />)

    await waitFor(() => expect(screen.getByTestId('p5r2-catalog-table')).toBeInTheDocument())
    const start = screen.getByLabelText('開始日時（UTC）')
    const end = screen.getByLabelText('終了日時（UTC）')
    expect(start).toHaveAttribute('type', 'datetime-local')
    expect(end).toHaveAttribute('type', 'datetime-local')

    await user.click(screen.getByRole('button', { name: '事前確認' }))
    const preflightCalls = () => fetchMock.mock.calls.filter(([url]) => String(url).endsWith('/api/p5r2/backtest/preflight'))
    expect(preflightCalls()).toHaveLength(1)
    const validBody = JSON.parse(String(preflightCalls()[0]?.[1]?.body)) as { spec: { start: string; end: string } }
    expect(validBody.spec.start).toBe('2025-02-24T00:00:00Z')
    expect(validBody.spec.end).toBe('2025-02-24T01:00:00Z')
    await user.click(screen.getByRole('button', { name: '取消' }))

    fireEvent.change(start, { target: { value: '2025-02-24T02:00' } })
    await user.click(screen.getByRole('button', { name: '事前確認' }))
    expect(preflightCalls()).toHaveLength(1)
    expect(screen.getByText('開始日時は終了日時より前にしてください。')).toBeVisible()
  })

  it('does not create a generation job when the selected range exceeds source coverage', async () => {
    const user = userEvent.setup()
    const fetchMock = installApiMock()
    render(<P5R2WebProductScreen screen={screen08} onOpenLegacy={() => undefined} />)

    await waitFor(() => expect(screen.getByTestId('p5r2-catalog-table')).toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: '時間足生成画面を開く' }))
    const end = screen.getByLabelText('生成終了日時（UTC）')
    fireEvent.change(end, { target: { value: '2025-02-24T04:00' } })
    await user.click(screen.getByRole('button', { name: '時間足を生成する' }))

    expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith('/api/p5r2/timeframe-generation-jobs'))).toBe(false)
    expect(screen.getAllByText('生成期間は、現在利用可能な1m sourceの範囲内で指定してください。').length).toBeGreaterThan(0)
  })

  it('shows the approved bounded DELETE-G1 boundary and has no automated axe violations in the actual-result screen shell', async () => {
    installApiMock()
    const resultScreen: ScreenDefinition = { ...screen08, id: 'SCREEN-10', title: 'Backtest結果サマリー' }
    const { container } = render(<P5R2WebProductScreen screen={resultScreen} onOpenLegacy={() => undefined} />)

    await waitFor(() => expect(screen.getByTestId('p5r2-delete-gate')).toBeInTheDocument())
    expect(screen.getByText('結果表示の削除は承認済み範囲で実行できます')).toBeInTheDocument()
    expect(screen.getByText(/削除対象のRunカードで確認ダイアログ/)).toBeInTheDocument()
    const results = await axe(container)
    expect(results.violations).toEqual([])
  })

  it('requires confirmation before requesting deletion for a completed Run', async () => {
    const user = userEvent.setup()
    const fetchMock = installApiMock([{
      run_id: 'RUN-UI-001',
      kind: 'SINGLE_BACKTEST',
      parent_id: null,
      status: 'SUCCEEDED',
      progress: 10,
      total: 10,
      progress_percent: 100,
      started_at: '2026-08-23T00:00:00Z',
      ended_at: '2026-08-23T00:01:00Z',
      eta: '完了',
      spec: { symbol: 'BTCUSDT', timeframe: '30m', strategy: 'TURTLE_SYS1' },
      metrics: { total_pnl: '1.00' },
      provenance: {},
      failure: null,
      checkpoint: null,
      resume_count: 0,
      recovery_mode: 'NORMAL',
      result_deleted: false,
      result_reference: 'results/RUN-UI-001/result.json',
      result_publish_id: 'RESULT-OWNER-RUN-UI-001',
    }])
    const resultScreen: ScreenDefinition = { ...screen08, id: 'SCREEN-10', title: 'Backtest結果サマリー' }
    render(<P5R2WebProductScreen screen={resultScreen} onOpenLegacy={() => undefined} />)

    await waitFor(() => expect(screen.getByTestId('p5r2-run-RUN-UI-001')).toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: '結果表示を削除' }))
    const dialog = await screen.findByRole('dialog', { name: 'RUN-UI-001の表示を削除しますか？' })
    expect(dialog).toHaveTextContent('先にCSVをExportしてください')
    expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith('/api/p5r2/result-artifacts/delete'))).toBe(false)

    await user.click(screen.getByRole('button', { name: '結果表示を削除する' }))
    await waitFor(() => expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith('/api/p5r2/result-artifacts/delete'))).toBe(true))
    const deleteCall = fetchMock.mock.calls.find(([input]) => String(input).endsWith('/api/p5r2/result-artifacts/delete'))
    expect(JSON.parse(String(deleteCall?.[1]?.body))).toMatchObject({
      logical_artifact_id: 'RESULT-OWNER-RUN-UI-001',
      artifact_kind: 'RESULT',
      confirmation: true,
    })
    expect(await screen.findByText(/RUN-UI-001の結果表示を削除しました/)).toBeInTheDocument()
  })
})
