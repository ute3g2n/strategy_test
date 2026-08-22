export const P5R2_STRATEGY_TIMEFRAMES = ['15m', '30m', '1h', '4h', '1d'] as const

export type P5R2StrategyTimeframe = (typeof P5R2_STRATEGY_TIMEFRAMES)[number]

export type P5R2Parameters = {
  entry_lookback: string
  exit_lookback: string
  initial_balance: string
  fee_bps: string
  slippage_bps: string
}

export type P5R2BacktestSpec = {
  symbol: 'BTCUSDT' | 'ETHUSDT'
  market: 'SPOT'
  timeframe: P5R2StrategyTimeframe
  timezone: 'UTC'
  calendar: 'CRYPTO_24_7_UTC'
  start: string
  end: string
  strategy: 'TURTLE_SYS1' | 'TURTLE_SYS2'
  parameters: P5R2Parameters
}

export type P5R2ApiFailure = {
  code: string
  message?: string
  retryable?: boolean
}

export type P5R2CatalogItem = {
  dataset_id: string
  identity: Record<string, unknown>
  provider?: string
  market?: string
  symbol?: string
  source_timeframe?: string
  data_timeframe?: string
  timeframe?: string
  period?: P5R2RequestedRange | null
  coverage?: P5R2RequestedRange | null
  quality?: string
  usable?: boolean
  legacy?: boolean
  provenance?: Record<string, unknown>
  state?: string
  promotion_state?: string
  recovery_mode?: string
}

export type P5R2CatalogResponse = {
  items: P5R2CatalogItem[]
  available_items: P5R2CatalogItem[]
  strategy_timeframes: string[]
  source_timeframe: string
}

export type P5R2RequestedRange = {
  start: string
  end: string
}

export type P5R2DataRequirement = {
  symbol: string
  timeframe: string
  requested_range: P5R2RequestedRange
  source_timeframe: '1m'
}

export type P5R2PreflightResponse = {
  status: 'PASS' | 'STOPPED'
  checks: Array<{ id: string; status: string; message: string }>
  normalized_spec?: P5R2BacktestSpec
  failure?: P5R2ApiFailure
  data_requirement?: P5R2DataRequirement
  data_set?: P5R2CatalogItem
}

export type P5R2RunOperation = {
  operation_id?: string
  status?: string
  reason?: string
  [key: string]: unknown
}

export type P5R2RunView = {
  run_id: string
  kind: string
  parent_id: string | null
  status: string
  progress: number
  total: number
  progress_percent: number
  started_at: string | null
  ended_at: string | null
  eta: string
  spec: {
    symbol?: string
    timeframe?: string
    strategy?: string
    start?: string
    end?: string
  }
  metrics: Record<string, string | number> | null
  provenance: Record<string, unknown>
  failure: P5R2ApiFailure | null
  checkpoint: Record<string, unknown> | null
  resume_count: number
  recovery_mode: string
  result_reference: string | null
  operation?: P5R2RunOperation
}

export type P5R2GenerationJob = {
  job_id: string | null
  job_type: string
  state: string
  reason?: string
  input?: {
    source_dataset_id?: string
    symbol?: string
    timeframes?: string[]
    requested_range?: P5R2RequestedRange
    request_id?: string
  }
  output?: Record<string, unknown> | null
  retry_of?: string | null
  orphan?: boolean
  external_io_performed?: boolean
  operation_token?: string
  owner_id?: string
  revision?: number
  accepted?: boolean
}

export type P5R2GenerationRequest = {
  source_dataset_id: string
  symbol: string
  timeframes: P5R2StrategyTimeframe[]
  requested_range: P5R2RequestedRange
  request_id: string
  reason: string
  retry_of: null
  external_io_allowed: false
}

type ApiErrorPayload = {
  error?: { code?: string; message?: string }
  reason?: string
}

const API_BASE = import.meta.env.VITE_P5R_API_BASE ?? 'http://127.0.0.1:8765'

export class P5R2ApiRequestError extends Error {
  readonly code: string

  constructor(code: string, message?: string) {
    super(message ?? code)
    this.name = 'P5R2ApiRequestError'
    this.code = code
  }
}

async function request<T>(path: string, init?: RequestInit, acceptedStatusCodes: number[] = []): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  })
  const payload = (await response.json()) as T & ApiErrorPayload
  if (!response.ok && !acceptedStatusCodes.includes(response.status)) {
    throw new P5R2ApiRequestError(payload.error?.code ?? payload.reason ?? `HTTP_${response.status}`, payload.error?.message)
  }
  return payload as T
}

const jsonBody = (body: unknown): RequestInit => ({ method: 'POST', body: JSON.stringify(body) })

export const p5r2Api = {
  catalog: () => request<P5R2CatalogResponse>('/api/p5r2/catalog'),
  preflight: (spec: P5R2BacktestSpec) => request<P5R2PreflightResponse>('/api/p5r2/backtest/preflight', jsonBody({ spec }), [422]),
  createRun: (spec: P5R2BacktestSpec) => request<P5R2RunView | P5R2PreflightResponse>('/api/p5r2/backtest/runs', jsonBody({ spec }), [422]),
  listRuns: () => request<{ items: P5R2RunView[] }>('/api/backtest/runs'),
  cancelRun: (runId: string) => request<P5R2RunView>(
    `/api/backtest/runs/${encodeURIComponent(runId)}/cancel`,
    jsonBody({
      reason: 'USER_REQUESTED_FROM_P5R2_UI',
      operation_token: `p5r2-ui-cancel-${runId}`,
      request_id: `p5r2-ui-cancel-request-${runId}`,
    }),
    [202],
  ),
  createTimeframeGenerationJob: (value: P5R2GenerationRequest) => request<P5R2GenerationJob>(
    '/api/p5r2/timeframe-generation-jobs',
    jsonBody(value),
    [422],
  ),
  getTimeframeGenerationJob: (jobId: string) => request<P5R2GenerationJob>(
    `/api/p5r2/timeframe-generation-jobs/${encodeURIComponent(jobId)}`,
  ),
  transitionTimeframeGenerationJob: (job: P5R2GenerationJob, action: 'advance' | 'cancel' | 'restart' | 'retry') => request<P5R2GenerationJob>(
    `/api/p5r2/timeframe-generation-jobs/${encodeURIComponent(job.job_id ?? '')}/${action}`,
    jsonBody({
      ...job,
      target_state: action === 'advance' ? 'RUNNING' : undefined,
    }),
    [409],
  ),
}

export const defaultP5R2BacktestSpec = (): P5R2BacktestSpec => ({
  symbol: 'BTCUSDT',
  market: 'SPOT',
  timeframe: '30m',
  timezone: 'UTC',
  calendar: 'CRYPTO_24_7_UTC',
  start: '2025-02-24T00:00:00Z',
  end: '2025-02-24T01:00:00Z',
  strategy: 'TURTLE_SYS1',
  parameters: {
    entry_lookback: '8',
    exit_lookback: '4',
    initial_balance: '100000',
    fee_bps: '1.0',
    slippage_bps: '2.0',
  },
})

export function isP5R2StrategyTimeframe(value: string | undefined): value is P5R2StrategyTimeframe {
  return value !== undefined && (P5R2_STRATEGY_TIMEFRAMES as readonly string[]).includes(value)
}
