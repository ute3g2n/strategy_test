export type BacktestParameters = {
  entry_lookback: string
  exit_lookback: string
  initial_balance: string
  fee_bps: string
  slippage_bps: string
  force_fail?: boolean
}

export type BacktestSpec = {
  symbol: 'BTCUSDT' | 'ETHUSDT'
  market: 'SPOT'
  timeframe: '1m'
  timezone: 'UTC'
  calendar: 'CRYPTO_24_7_UTC'
  start: string
  end: string
  strategy: string
  parameters: BacktestParameters
  force_fail?: boolean
}

export type BacktestCheck = {
  id: string
  status: string
  message: string
}

export type PreflightResponse = {
  status: 'PASS' | 'STOPPED'
  checks: BacktestCheck[]
  normalized_spec?: BacktestSpec
  failure?: { code: string; message?: string; retryable?: boolean }
}

export type BacktestRow = Record<string, string | number | null | undefined>

export type RunView = {
  run_id: string
  kind: string
  parent_id: string | null
  status: 'QUEUED' | 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'CANCELLED' | string
  progress: number
  total: number
  progress_percent: number
  started_at: string | null
  ended_at: string | null
  eta: string
  spec: BacktestSpec
  metrics: Record<string, string | number> | null
  provenance: Record<string, string | number | Record<string, unknown>>
  failure: { code: string; message?: string; retryable?: boolean } | null
  checkpoint: Record<string, unknown> | null
  resume_count: number
  result_reference: string | null
}

export type SweepView = {
  sweep_id: string
  status: string
  total: number
  completed: number
  failed: number
  children: RunView[]
}

export type CsvJobView = {
  job_id: string
  run_id: string
  status: string
  progress: number
  download_url: string | null
  failure: { code: string; message?: string } | null
}

export type HoldoutView = {
  status: string
  period?: { start: string; end: string }
  row_count?: number
  reused_for_adjustment?: boolean
  failure?: { code: string; message?: string }
}

export type WalkForwardView = {
  status: string
  windows: Array<Record<string, unknown>>
  future_reference: boolean
  holdout_reused: boolean
}

type ApiErrorPayload = { error?: { code?: string; message?: string } }

const API_BASE = import.meta.env.VITE_P5R_API_BASE ?? 'http://127.0.0.1:8765'

async function request<T>(path: string, init?: RequestInit, acceptedStatusCodes: number[] = []): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  })
  const payload = (await response.json()) as T & ApiErrorPayload
  if (!response.ok && !acceptedStatusCodes.includes(response.status)) {
    const code = payload.error?.code ?? `HTTP_${response.status}`
    throw new Error(payload.error?.message ?? code)
  }
  return payload as T
}

const jsonBody = (body: unknown): RequestInit => ({
  method: 'POST',
  body: JSON.stringify(body),
})

export const backtestApi = {
  preflight: (spec: BacktestSpec) => request<PreflightResponse>('/api/backtest/preflight', jsonBody({ spec }), [422]),
  createRun: (spec: BacktestSpec) => request<RunView>('/api/backtest/runs', jsonBody({ spec })),
  getRun: (runId: string) => request<RunView>(`/api/backtest/runs/${encodeURIComponent(runId)}`),
  getRows: (runId: string) => request<{ items: BacktestRow[] }>(`/api/backtest/runs/${encodeURIComponent(runId)}/rows`),
  cancelRun: (runId: string) => request<RunView>(`/api/backtest/runs/${encodeURIComponent(runId)}/cancel`, jsonBody({ reason: 'USER_REQUESTED_FROM_UI' })),
  resumeRun: (runId: string) => request<RunView>(`/api/backtest/runs/${encodeURIComponent(runId)}/resume`, jsonBody({})),
  listRuns: () => request<{ items: RunView[] }>('/api/backtest/runs/history'),
  createSweep: (spec: BacktestSpec, candidates: Array<Record<string, string | boolean>>) => request<SweepView>('/api/backtest/sweeps', jsonBody({ spec, candidates })),
  getSweep: (sweepId: string) => request<SweepView>(`/api/backtest/sweeps/${encodeURIComponent(sweepId)}`),
  cancelSweep: (sweepId: string) => request<SweepView>(`/api/backtest/sweeps/${encodeURIComponent(sweepId)}/cancel`, jsonBody({})),
  compare: (leftRunId: string, rightRunId: string) => request<Record<string, unknown>>('/api/backtest/compare', jsonBody({ left_run_id: leftRunId, right_run_id: rightRunId })),
  createCsvJob: (runId: string) => request<CsvJobView>('/api/backtest/csv-jobs', jsonBody({ run_id: runId, columns: ['row_kind', 'decision_time_utc', 'symbol', 'signal', 'direction', 'price', 'fee', 'slippage', 'equity', 'reason'] })),
  getCsvJob: (jobId: string) => request<CsvJobView>(`/api/backtest/csv-jobs/${encodeURIComponent(jobId)}`),
  holdout: (phase: 'EARLY_ADJUSTMENT' | 'FINALIZED') => request<HoldoutView>('/api/backtest/holdout', jsonBody({ phase }), [409]),
  walkForward: (windows: Array<Record<string, string>>) => request<WalkForwardView>('/api/backtest/walk-forward', jsonBody({ windows })),
  downloadCsv: (jobId: string) => `${API_BASE}/api/backtest/csv-jobs/${encodeURIComponent(jobId)}/download`,
}

export const defaultBacktestSpec = (): BacktestSpec => ({
  symbol: 'BTCUSDT',
  market: 'SPOT',
  timeframe: '1m',
  timezone: 'UTC',
  calendar: 'CRYPTO_24_7_UTC',
  start: '2025-02-24T00:00:00Z',
  end: '2025-02-24T02:30:00Z',
  strategy: 'TURTLE_SYS1',
  parameters: {
    entry_lookback: '8',
    exit_lookback: '4',
    initial_balance: '100000',
    fee_bps: '1.0',
    slippage_bps: '2.0',
  },
})
