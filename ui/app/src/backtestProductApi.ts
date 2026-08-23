export const BACKTEST_PRODUCT_STRATEGY_TIMEFRAMES = ['15m', '30m', '1h', '4h', '1d'] as const

export type BacktestProductStrategyTimeframe = (typeof BACKTEST_PRODUCT_STRATEGY_TIMEFRAMES)[number]

export type BacktestProductParameters = {
  entry_lookback: string
  exit_lookback: string
  initial_balance: string
  fee_bps: string
  slippage_bps: string
}

export type BacktestProductSpec = {
  symbol: 'BTCUSDT' | 'ETHUSDT'
  market: 'SPOT'
  timeframe: BacktestProductStrategyTimeframe
  timezone: 'UTC'
  calendar: 'CRYPTO_24_7_UTC'
  start: string
  end: string
  strategy: 'TURTLE_SYS1' | 'TURTLE_SYS2'
  parameters: BacktestProductParameters
}

export type BacktestProductApiFailure = {
  code: string
  message?: string
  retryable?: boolean
}

export type BacktestProductCatalogItem = {
  dataset_id: string
  identity: Record<string, unknown>
  provider?: string
  market?: string
  symbol?: string
  source_timeframe?: string
  data_timeframe?: string
  timeframe?: string
  period?: BacktestProductRequestedRange | null
  coverage?: BacktestProductRequestedRange | null
  quality?: string
  usable?: boolean
  legacy?: boolean
  provenance?: Record<string, unknown>
  state?: string
  promotion_state?: string
  recovery_mode?: string
}

export type BacktestProductCatalogResponse = {
  items: BacktestProductCatalogItem[]
  available_items: BacktestProductCatalogItem[]
  strategy_timeframes: string[]
  source_timeframe: string
}

export type BacktestProductRequestedRange = {
  start: string
  end: string
}

export type BacktestProductDataRequirement = {
  symbol: string
  timeframe: string
  requested_range: BacktestProductRequestedRange
  source_timeframe: '1m'
}

export type BacktestProductPreflightResponse = {
  status: 'PASS' | 'STOPPED'
  checks: Array<{ id: string; status: string; message: string }>
  normalized_spec?: BacktestProductSpec
  failure?: BacktestProductApiFailure
  data_requirement?: BacktestProductDataRequirement
  data_set?: BacktestProductCatalogItem
}

export type BacktestProductRunOperation = {
  operation_id?: string
  status?: string
  reason?: string
  [key: string]: unknown
}

export type BacktestProductRunView = {
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
  failure: BacktestProductApiFailure | null
  checkpoint: Record<string, unknown> | null
  resume_count: number
  recovery_mode: string
  result_deleted?: boolean
  result_deleted_at?: string | null
  result_reference: string | null
  result_publish_id?: string | null
  operation?: BacktestProductRunOperation
}

export type BacktestProductResultDeleteResponse = {
  logical_artifact_id: string
  artifact_kind: string
  accepted: boolean
  deleted: boolean
  status: string
  artifact_state: string
  error_code?: string | null
  reason?: string
  request_id?: string
  operation_token?: string
  audit_id?: string
  physical_io_performed?: boolean
  replayed?: boolean
}

export type BacktestProductGenerationJob = {
  job_id: string | null
  job_type: string
  state: string
  reason?: string
  input?: {
    source_dataset_id?: string
    symbol?: string
    timeframes?: string[]
    requested_range?: BacktestProductRequestedRange
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

export type BacktestProductGenerationRequest = {
  source_dataset_id: string
  symbol: string
  timeframes: BacktestProductStrategyTimeframe[]
  requested_range: BacktestProductRequestedRange
  request_id: string
  reason: string
  retry_of: null
  external_io_allowed: false
}

type ApiErrorPayload = {
  error?: { code?: string; message?: string }
  reason?: string
}

const API_BASE = import.meta.env.VITE_BACKTEST_API_BASE ?? 'http://127.0.0.1:8765'

export class BacktestProductApiRequestError extends Error {
  readonly code: string

  constructor(code: string, message?: string) {
    super(message ?? code)
    this.name = 'BacktestProductApiRequestError'
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
    throw new BacktestProductApiRequestError(payload.error?.code ?? payload.reason ?? `HTTP_${response.status}`, payload.error?.message)
  }
  return payload as T
}

const jsonBody = (body: unknown): RequestInit => ({ method: 'POST', body: JSON.stringify(body) })

export const backtestProductApi = {
  catalog: () => request<BacktestProductCatalogResponse>('/api/backtest-product/catalog'),
  preflight: (spec: BacktestProductSpec) => request<BacktestProductPreflightResponse>('/api/backtest-product/backtest/preflight', jsonBody({ spec }), [422]),
  createRun: (spec: BacktestProductSpec) => request<BacktestProductRunView | BacktestProductPreflightResponse>('/api/backtest-product/backtest/runs', jsonBody({ spec }), [422]),
  listRuns: () => request<{ items: BacktestProductRunView[] }>('/api/backtest/runs'),
  cancelRun: (runId: string) => request<BacktestProductRunView>(
    `/api/backtest/runs/${encodeURIComponent(runId)}/cancel`,
    jsonBody({
      reason: 'USER_REQUESTED_FROM_BACKTEST_UI',
      operation_token: `backtest-product-ui-cancel-${runId}`,
      request_id: `backtest-product-ui-cancel-request-${runId}`,
    }),
    [202],
  ),
  deleteResultArtifact: (runId: string) => request<BacktestProductResultDeleteResponse>(
    '/api/backtest-product/result-artifacts/delete',
    jsonBody({
      logical_artifact_id: `RESULT-OWNER-${runId}`,
      artifact_kind: 'RESULT',
      confirmation: true,
      operation_token: `backtest-product-ui-result-delete-${runId}`,
      request_id: `backtest-product-ui-result-delete-request-${runId}`,
      reason: 'operator requested result display removal from Backtest result screen',
    }),
    [409],
  ),
  createTimeframeGenerationJob: (value: BacktestProductGenerationRequest) => request<BacktestProductGenerationJob>(
    '/api/backtest-product/timeframe-generation-jobs',
    jsonBody(value),
    [422],
  ),
  getTimeframeGenerationJob: (jobId: string) => request<BacktestProductGenerationJob>(
    `/api/backtest-product/timeframe-generation-jobs/${encodeURIComponent(jobId)}`,
  ),
  transitionTimeframeGenerationJob: (job: BacktestProductGenerationJob, action: 'advance' | 'cancel' | 'restart' | 'retry') => request<BacktestProductGenerationJob>(
    `/api/backtest-product/timeframe-generation-jobs/${encodeURIComponent(job.job_id ?? '')}/${action}`,
    jsonBody({
      ...job,
      target_state: action === 'advance' ? 'RUNNING' : undefined,
    }),
    [409],
  ),
}

export const defaultBacktestProductSpec = (): BacktestProductSpec => ({
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

export function isSupportedStrategyTimeframe(value: string | undefined): value is BacktestProductStrategyTimeframe {
  return value !== undefined && (BACKTEST_PRODUCT_STRATEGY_TIMEFRAMES as readonly string[]).includes(value)
}
