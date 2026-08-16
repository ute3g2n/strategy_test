import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { HelpTip, MetricCard, StateAlert, StateBadge, type ScreenDefinition, type UiState } from './ui'
import {
  backtestApi,
  defaultBacktestSpec,
  type BacktestRow,
  type BacktestSpec,
  type CsvJobView,
  type HoldoutView,
  type PreflightResponse,
  type RecoveryReport,
  type RunView,
  type SweepView,
  type WalkForwardView,
} from './backtestApi'

type P5RBacktestScreenProps = {
  screen: ScreenDefinition
  demoState: UiState
  onStateChange: (state: UiState) => void
}

type TabId = 'single' | 'sweep' | 'history' | 'evaluation'

const stateIds: UiState[] = ['NORMAL', 'LOADING', 'EMPTY', 'REQUIRED', 'WARNING', 'STOPPED', 'FAILED', 'RECOVERY', 'HUMAN-GATE', 'UNAPPROVED']

const stateForRun = (run: RunView | null): UiState => {
  if (!run) return 'REQUIRED'
  if (run.status === 'RECOVERY_REQUIRED') return 'RECOVERY'
  if (run.status === 'SUCCEEDED') return 'NORMAL'
  if (run.status === 'FAILED') return 'FAILED'
  if (run.status === 'CANCELLED') return 'STOPPED'
  return 'LOADING'
}

const formatValue = (value: unknown, fallback = '—') => (value === null || value === undefined || value === '' ? fallback : String(value))

const toErrorMessage = (error: unknown) => (error instanceof Error ? error.message : 'ローカルAPIで予期しない失敗が起きました。')

const windows = [
  { id: 'W1', train_start: '2025-02-24T00:00:00Z', train_end: '2025-02-24T00:30:00Z', validation_end: '2025-02-24T01:00:00Z', evaluation_end: '2025-02-24T01:30:00Z' },
  { id: 'W2', train_start: '2025-02-24T00:00:00Z', train_end: '2025-02-24T01:00:00Z', validation_end: '2025-02-24T01:30:00Z', evaluation_end: '2025-02-24T02:00:00Z' },
  { id: 'W3', train_start: '2025-02-24T00:30:00Z', train_end: '2025-02-24T01:30:00Z', validation_end: '2025-02-24T02:00:00Z', evaluation_end: '2025-02-24T02:30:00Z' },
]

function P5RStateControls({ demoState, onStateChange }: { demoState: UiState; onStateChange: (state: UiState) => void }) {
  return (
    <section className="panel-card" aria-labelledby="p5r-state-title">
      <div className="section-heading"><div><p className="card-kicker">共通状態</p><h3 id="p5r-state-title">画面の状態を確認</h3></div><StateBadge state={demoState} compact /></div>
      <p className="muted">これは表示状態の確認です。Backtestの実Run状態は上のApplication APIの値を表示します。</p>
      <div className="state-switcher" aria-label="状態切替">
        {stateIds.map((state) => <button className={demoState === state ? 'state-choice active' : 'state-choice'} type="button" key={state} onClick={() => onStateChange(state)}>{state}</button>)}
      </div>
    </section>
  )
}

function CheckList({ preflight }: { preflight: PreflightResponse | null }) {
  if (!preflight) return <p className="muted">まだPreflightを実行していません。開始前に入力・範囲・UTC・品質・先読みを確認します。</p>
  return (
    <div className="check-list" data-testid="p5r-preflight-result">
      {preflight.checks.map((check) => <div key={check.id}><StateBadge state={check.status === 'PASS' ? 'NORMAL' : 'FAILED'} compact /> <strong>{check.id}</strong> — {check.message}</div>)}
      {preflight.failure && <p className="inline-notice" role="alert">停止理由: {preflight.failure.code}</p>}
    </div>
  )
}

function RunStatusCard({ run, onCancel, onResume, onDetails }: { run: RunView; onCancel: () => void; onResume: () => void; onDetails: () => void }) {
  const terminal = ['SUCCEEDED', 'FAILED', 'CANCELLED'].includes(run.status)
  return (
    <section className="panel-card" data-testid="p5r-run-status" aria-live="polite">
      <div className="section-heading"><div><p className="card-kicker">実Run</p><h3>{run.run_id}</h3></div><StateBadge state={stateForRun(run)} compact /></div>
      <div className="run-progress-grid">
        <div><span className="small-label">状態</span><strong>{run.status}</strong></div>
        <div><span className="small-label">進捗</span><strong>{run.progress_percent}% ({run.progress}/{run.total || '—'} Bar)</strong></div>
        <div><span className="small-label">ETA</span><strong>{run.eta}</strong></div>
        <div><span className="small-label">再開回数</span><strong>{run.resume_count}</strong></div>
      </div>
      <div className="progress-track" aria-label={`Backtest進捗 ${run.progress_percent}%`} role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={run.progress_percent}><span style={{ width: `${run.progress_percent}%` }} /></div>
      {run.failure && <p className="inline-notice" role="alert">停止理由: {run.failure.code}</p>}
      <div className="button-row compact-buttons">
        {['QUEUED', 'RUNNING'].includes(run.status) && <button className="danger-button" type="button" onClick={onCancel}>取消</button>}
        {run.status === 'CANCELLED' && run.checkpoint && <button className="primary-button" type="button" onClick={onResume}>チェックポイントから再開</button>}
        {terminal && run.status === 'SUCCEEDED' && <button className="secondary-button" type="button" onClick={onDetails}>結果・詳細を表示</button>}
      </div>
    </section>
  )
}

function Metrics({ run }: { run: RunView }) {
  const metrics = run.metrics ?? {}
  return (
    <section className="metric-grid five-metrics" aria-label="Backtestの5指標" data-testid="p5r-five-metrics">
      <MetricCard label="総損益" value={formatValue(metrics.total_pnl)} detail="Decimal / USDT" tone={String(metrics.total_pnl ?? '').startsWith('-') ? 'warning' : 'positive'} />
      <MetricCard label="最大ドローダウン" value={formatValue(metrics.maximum_drawdown)} detail="最大の落ち込み" tone="warning" />
      <MetricCard label="勝率" value={`${formatValue(metrics.win_rate, '0')}%`} detail="決済済み取引ベース" />
      <MetricCard label="取引回数" value={formatValue(metrics.trade_count, '0')} detail="Virtual Fill回数" />
      <MetricCard label="最終残高" value={formatValue(metrics.ending_balance)} detail="初期残高との差" tone="positive" />
    </section>
  )
}

function LedgerTable({ rows }: { rows: BacktestRow[] }) {
  return (
    <div className="table-scroll" data-testid="p5r-ledger-table">
      <table className="data-table">
        <caption>同じRunから得たSignal・Virtual Fill・残高Ledger</caption>
        <thead><tr><th scope="col">種類</th><th scope="col">時刻（UTC）</th><th scope="col">銘柄</th><th scope="col">Signal</th><th scope="col">方向</th><th scope="col">価格</th><th scope="col">残高／Equity</th><th scope="col">理由</th></tr></thead>
        <tbody>{rows.slice(0, 120).map((row, index) => <tr key={`${String(row.row_kind)}-${String(row.decision_time_utc)}-${index}`}><th scope="row">{formatValue(row.row_kind)}</th><td>{formatValue(row.decision_time_utc)}</td><td>{formatValue(row.symbol)}</td><td>{formatValue(row.signal)}</td><td>{formatValue(row.direction)}</td><td>{formatValue(row.price)}</td><td>{formatValue(row.equity ?? row.cash)}</td><td>{formatValue(row.reason ?? row.assumption)}</td></tr>)}</tbody>
      </table>
      {rows.length > 120 && <p className="muted">表示は先頭120行です。CSV出力で全行を取得できます。</p>}
    </div>
  )
}

export function P5RBacktestScreen({ screen, demoState, onStateChange }: P5RBacktestScreenProps) {
  const [tab, setTab] = useState<TabId>('single')
  const [spec, setSpec] = useState<BacktestSpec>(() => defaultBacktestSpec())
  const [preflight, setPreflight] = useState<PreflightResponse | null>(null)
  const [activeRun, setActiveRun] = useState<RunView | null>(null)
  const [rows, setRows] = useState<BacktestRow[]>([])
  const [history, setHistory] = useState<RunView[]>([])
  const [recovery, setRecovery] = useState<RecoveryReport | null>(null)
  const [sweep, setSweep] = useState<SweepView | null>(null)
  const [selectedCompareRun, setSelectedCompareRun] = useState('')
  const [compareResult, setCompareResult] = useState<Record<string, unknown> | null>(null)
  const [csvJob, setCsvJob] = useState<CsvJobView | null>(null)
  const [holdout, setHoldout] = useState<HoldoutView | null>(null)
  const [walkForward, setWalkForward] = useState<WalkForwardView | null>(null)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [partialFailure, setPartialFailure] = useState(false)

  const selectedRun = useMemo(() => activeRun ?? history.find((run) => run.run_id === selectedCompareRun) ?? null, [activeRun, history, selectedCompareRun])

  const setParameter = (key: keyof BacktestSpec['parameters'], value: string) => setSpec((current) => ({ ...current, parameters: { ...current.parameters, [key]: value } }))
  const clearFeedback = () => { setError(''); setMessage('') }

  const refreshHistory = async () => {
    try {
      const [historyResult, recoveryResult] = await Promise.all([backtestApi.listRuns(), backtestApi.getRecovery()])
      setHistory(historyResult.items)
      setRecovery(recoveryResult)
    } catch (caught) {
      setError(toErrorMessage(caught))
    }
  }

  const runRequest = async <T,>(request: () => Promise<T>, onSuccess: (value: T) => void) => {
    clearFeedback()
    setBusy(true)
    try {
      onSuccess(await request())
    } catch (caught) {
      setError(toErrorMessage(caught))
    } finally {
      setBusy(false)
    }
  }

  const submitPreflight = async (event?: FormEvent) => {
    event?.preventDefault()
    await runRequest(() => backtestApi.preflight(spec), (result) => { setPreflight(result); setMessage(result.status === 'PASS' ? 'Preflight PASS。実Runを開始できます。' : 'Preflight STOPPED。停止理由を直してから再実行してください。') })
  }

  const submitSingle = async () => {
    await runRequest(() => backtestApi.createRun(spec), (run) => { setActiveRun(run); setSelectedCompareRun(run.run_id); setTab('single'); setMessage('Single Backtestを受付しました。進捗は自動更新されます。') })
  }

  const cancelRun = async () => {
    if (!activeRun) return
    await runRequest(() => backtestApi.cancelRun(activeRun.run_id), (run) => { setActiveRun(run); setMessage('取消を受付しました。チェックポイントが保存されれば再開できます。') })
  }

  const resumeRun = async () => {
    if (!activeRun) return
    await runRequest(() => backtestApi.resumeRun(activeRun.run_id), (run) => { setActiveRun(run); setMessage('チェックポイントから再開しました。') })
  }

  const loadDetails = async (runId: string) => {
    await runRequest(() => backtestApi.getRows(runId), (result) => { setRows(result.items); setMessage('結果Ledgerを読み込みました。') })
  }

  const submitSweep = async () => {
    const candidates: Array<Record<string, string | boolean>> = [
      { entry_lookback: spec.parameters.entry_lookback },
      { entry_lookback: String(Number(spec.parameters.entry_lookback) + 1) },
    ]
    if (partialFailure) candidates[1].force_fail = true
    await runRequest(() => backtestApi.createSweep(spec, candidates), (result) => { setSweep(result); setTab('sweep'); setMessage('Sweepを受付しました。候補ごとの結果を確認できます。') })
  }

  const submitCompare = async () => {
    if (!activeRun || !selectedCompareRun || activeRun.run_id === selectedCompareRun) {
      setError('比較には異なる2つのRunが必要です。履歴から比較対象を選択してください。')
      return
    }
    await runRequest(() => backtestApi.compare(activeRun.run_id, selectedCompareRun), (result) => { setCompareResult(result); setMessage('2つのRunを比較しました。最良Runの自動選択はしません。') })
  }

  const submitCsv = async () => {
    if (!selectedRun) return
    await runRequest(() => backtestApi.createCsvJob(selectedRun.run_id), (result) => { setCsvJob(result); setMessage('CSV生成Jobを受付しました。完了後にダウンロードできます。') })
  }

  const submitHoldout = async (phase: 'EARLY_ADJUSTMENT' | 'FINALIZED') => {
    await runRequest(() => backtestApi.holdout(phase), (result) => { setHoldout(result); setMessage(result.status === 'SUCCEEDED' ? 'Holdoutを確定後の評価として読み込みました。' : 'Holdoutは停止されました。') })
  }

  const submitWalkForward = async () => {
    await runRequest(() => backtestApi.walkForward(windows), (result) => { setWalkForward(result); setMessage('Walk-forwardの各窓を検証しました。') })
  }

  useEffect(() => {
    void refreshHistory()
  }, [])

  useEffect(() => {
    const runId = activeRun?.run_id
    const runStatus = activeRun?.status
    if (typeof runId !== 'string' || !['QUEUED', 'RUNNING'].includes(runStatus ?? '')) return
    const timer = window.setInterval(() => {
      void backtestApi.getRun(runId).then(setActiveRun).catch((caught: unknown) => setError(toErrorMessage(caught)))
    }, 100)
    return () => window.clearInterval(timer)
  }, [activeRun?.run_id, activeRun?.status])

  useEffect(() => {
    const jobId = csvJob?.job_id
    const jobStatus = csvJob?.status
    if (typeof jobId !== 'string' || !['QUEUED', 'RUNNING'].includes(jobStatus ?? '')) return
    const timer = window.setInterval(() => {
      void backtestApi.getCsvJob(jobId).then(setCsvJob).catch((caught: unknown) => setError(toErrorMessage(caught)))
    }, 100)
    return () => window.clearInterval(timer)
  }, [csvJob?.job_id, csvJob?.status])

  useEffect(() => {
    const sweepId = sweep?.sweep_id
    const sweepStatus = sweep?.status
    if (typeof sweepId !== 'string' || ['SUCCEEDED', 'PARTIAL_FAILED', 'CANCELLED'].includes(sweepStatus ?? '')) return
    const timer = window.setInterval(() => {
      void backtestApi.getSweep(sweepId).then(setSweep).catch((caught: unknown) => setError(toErrorMessage(caught)))
    }, 100)
    return () => window.clearInterval(timer)
  }, [sweep?.sweep_id, sweep?.status])

  useEffect(() => {
    if (activeRun?.status === 'SUCCEEDED') void refreshHistory()
  }, [activeRun?.status])

  const runForDisplay = selectedRun ?? activeRun

  return (
    <div className="screen-stack" data-testid={`screen-${screen.id}`} data-p5r-real-api="true" data-reason-id="P5R_APPLICATION_API">
      <section className="welcome-panel compact-panel"><div><p className="eyebrow">{screen.navId} / {screen.id} / {screen.e2eId}</p><h2>Backtest製品機能（P5R実API）</h2><p className="lead">P5で品質確認済みのローカル市場データだけを使い、条件確認から結果・証跡・CSV・評価までを実際に操作します。</p></div><StateBadge state={stateForRun(activeRun)} /></section>
      <StateAlert state="WARNING" title="この画面の安全境界">外部市場データ、Broker、Secret、実注文、Paper／Liveには接続しません。利益が出ることを保証する画面でもありません。</StateAlert>
      <section className="p5r-scope-strip" aria-label="P5Rの実行範囲"><strong>P5R実行範囲</strong><span>BTCUSDT / ETHUSDT</span><span>Spot / 1m / UTC</span><span>期間: 2025-02-24〜2026-08-01</span><span>Data: P5 local read-only</span></section>

      <div className="tab-list" role="tablist" aria-label="P5R Backtest機能">
        {([['single', 'Single Run'], ['sweep', 'Sweep'], ['history', '履歴・比較'], ['evaluation', 'Holdout・Walk-forward']] as const).map(([id, label]) => <button className={tab === id ? 'tab-button active' : 'tab-button'} type="button" role="tab" aria-selected={tab === id} key={id} data-testid={`p5r-tab-${id}`} onClick={() => { setTab(id); if (id === 'history') void refreshHistory() }}>{label}</button>)}
      </div>

      {tab === 'single' && <>
        <form className="two-column-grid" onSubmit={submitPreflight}>
          <section className="sub-panel" aria-labelledby="p5r-condition-title">
            <div className="section-heading"><div><p className="card-kicker">BT-MAN-01 / BT-MAN-02</p><h3 id="p5r-condition-title">Single Backtest条件</h3></div><StateBadge state={preflight?.status === 'PASS' ? 'NORMAL' : 'REQUIRED'} compact /></div>
            <div className="field-grid">
              <label className="field-label"><span>銘柄</span><select aria-label="Backtest銘柄" value={spec.symbol} onChange={(event) => setSpec((current) => ({ ...current, symbol: event.target.value as BacktestSpec['symbol'] }))}><option value="BTCUSDT">BTCUSDT</option><option value="ETHUSDT">ETHUSDT</option></select></label>
              <label className="field-label"><span>市場</span><input value="Spot" readOnly /></label>
              <label className="field-label"><span>時間足</span><input value="1m" readOnly /></label>
              <label className="field-label"><span>タイムゾーン</span><input value="UTC" readOnly /></label>
              <label className="field-label"><span>開始（UTC）</span><input aria-label="開始（UTC）" value={spec.start} onChange={(event) => setSpec((current) => ({ ...current, start: event.target.value }))} /></label>
              <label className="field-label"><span>終了（UTC）</span><input aria-label="終了（UTC）" value={spec.end} onChange={(event) => setSpec((current) => ({ ...current, end: event.target.value }))} /></label>
              <label className="field-label"><span>Strategy</span><select aria-label="Backtest Strategy" value={spec.strategy} onChange={(event) => setSpec((current) => ({ ...current, strategy: event.target.value }))}><option value="TURTLE_SYS1">TURTLE_SYS1</option><option value="TURTLE_SYS2">TURTLE_SYS2</option></select></label>
              <label className="field-label"><span>初期残高（USDT）</span><input aria-label="初期残高" value={spec.parameters.initial_balance} onChange={(event) => setParameter('initial_balance', event.target.value)} /></label>
              <label className="field-label"><span>Entry lookback</span><input aria-label="Entry lookback" value={spec.parameters.entry_lookback} onChange={(event) => setParameter('entry_lookback', event.target.value)} /></label>
              <label className="field-label"><span>Exit lookback</span><input aria-label="Exit lookback" value={spec.parameters.exit_lookback} onChange={(event) => setParameter('exit_lookback', event.target.value)} /></label>
              <label className="field-label"><span>Fee（bps）</span><input aria-label="Fee bps" value={spec.parameters.fee_bps} onChange={(event) => setParameter('fee_bps', event.target.value)} /></label>
              <label className="field-label"><span>Slippage（bps）</span><input aria-label="Slippage bps" value={spec.parameters.slippage_bps} onChange={(event) => setParameter('slippage_bps', event.target.value)} /></label>
            </div>
            <div className="button-row"><button className="secondary-button" type="submit" disabled={busy}>Preflight実行</button><button className="primary-button" type="button" disabled={busy || preflight?.status !== 'PASS'} onClick={() => void submitSingle()}>Single Run開始</button></div>
            <p className="muted">費用は手数料・Slippageの想定値です。市場で実際にその価格で約定することを意味しません。</p>
          </section>
          <section className="sub-panel" aria-labelledby="p5r-preflight-title"><div className="section-heading"><div><p className="card-kicker">停止条件</p><h3 id="p5r-preflight-title">開始前Preflight</h3></div><StateBadge state={preflight?.status === 'PASS' ? 'NORMAL' : 'REQUIRED'} compact /></div><CheckList preflight={preflight} /><p className="muted">品質PASSの既存ローカルDataだけを読み、P5R範囲外の銘柄・期間・単位は停止します。</p></section>
        </form>
        {activeRun && <RunStatusCard run={activeRun} onCancel={() => void cancelRun()} onResume={() => void resumeRun()} onDetails={() => void loadDetails(activeRun.run_id)} />}
        {activeRun?.status === 'SUCCEEDED' && <><Metrics run={activeRun} /><section className="panel-card"><div className="section-heading"><div><p className="card-kicker">BT-MAN-08 / BT-MAN-09</p><h3>結果Ledgerと由来</h3></div><button className="secondary-button" type="button" onClick={() => void loadDetails(activeRun.run_id)}>Detailsを読込</button></div><dl className="definition-list"><div><dt>Data由来</dt><dd>{formatValue(activeRun.provenance.source_mode)}</dd></div><div><dt>期間</dt><dd>{formatValue(activeRun.provenance.period_start_utc)} 〜 {formatValue(activeRun.provenance.period_end_utc)}</dd></div><div><dt>Data範囲</dt><dd>{formatValue(activeRun.provenance.fixture_scope)}</dd></div><div><dt>Core検証</dt><dd>{formatValue((activeRun.provenance.core_validation as Record<string, unknown> | undefined)?.status)}</dd></div><div><dt>利益の意味</dt><dd>{formatValue(activeRun.provenance.profitability_claim)}</dd></div></dl>{rows.length > 0 && <LedgerTable rows={rows} />}</section></>}
      </>}

      {tab === 'sweep' && <>
        <section className="two-column-grid"><section className="sub-panel"><div className="section-heading"><div><p className="card-kicker">BT-MAN-06 / BT-MAN-07</p><h3>候補条件と重複検査</h3></div><StateBadge state="NORMAL" compact /></div><p className="muted">現在のSingle条件を基準にEntry lookbackの2候補を作ります。最大200候補、重複は開始前に停止します。</p><dl className="definition-list"><div><dt>候補1</dt><dd>{spec.parameters.entry_lookback}</dd></div><div><dt>候補2</dt><dd>{Number(spec.parameters.entry_lookback) + 1}</dd></div></dl><label className="switch-label"><input type="checkbox" checked={partialFailure} onChange={(event) => setPartialFailure(event.target.checked)} /> 2番目の候補を意図的に失敗させる</label><div className="button-row"><button className="primary-button" type="button" onClick={() => void submitSweep()} disabled={busy}>Sweep開始</button>{sweep && <button className="danger-button" type="button" onClick={() => void runRequest(() => backtestApi.cancelSweep(sweep.sweep_id), (result) => { setSweep(result); setMessage('Sweepを取消しました。') })}>Sweep取消</button>}</div></section><section className="sub-panel"><div className="section-heading"><div><p className="card-kicker">親Job・子Run</p><h3>候補ごとの進捗</h3></div><StateBadge state={sweep?.status === 'PARTIAL_FAILED' ? 'WARNING' : sweep?.status === 'SUCCEEDED' ? 'NORMAL' : 'REQUIRED'} compact /></div>{sweep ? <><p className="muted">{sweep.sweep_id} / 状態: {sweep.status} / {sweep.completed}/{sweep.total}件完了 / 失敗 {sweep.failed}件</p><div className="run-list">{sweep.children.map((child) => <article className="run-card" key={child.run_id}><div className="section-heading"><strong>{child.run_id}</strong><StateBadge state={stateForRun(child)} compact /></div><p className="muted">Entry {child.spec.parameters.entry_lookback} / {child.status} / {child.failure?.code ?? '—'}</p></article>)}</div></> : <p className="muted">Sweepを開始すると、親Jobと子Runを表示します。</p>}</section></section>
      </>}

      {tab === 'history' && <>
        <section className="panel-card"><div className="section-heading"><div><p className="card-kicker">BT-MAN-10 / BT-MAN-11</p><h3>履歴・比較</h3></div><button className="secondary-button" type="button" onClick={() => void refreshHistory()}>履歴を更新</button></div>{recovery?.status === 'RECOVERY_REQUIRED' && <div className="inline-notice error-notice" role="alert" data-testid="p5r-recovery-warning">保存済み履歴の一部で復旧確認が必要です。該当Runは成功扱いにせず、原因を確認してから再実行してください（{recovery.issues.length}件の問題 / 復旧確認 {recovery.recovery_required_run_ids.length}件）。</div>}{recovery?.status === 'CLEAN' && <p className="muted" role="status" data-testid="p5r-recovery-clean">保存済み履歴を読み込みました（{recovery.restored_run_count}件）。</p>}<div className="table-scroll"><table className="data-table"><caption>このApplication APIで作成したRunの履歴</caption><thead><tr><th scope="col">選択</th><th scope="col">Run ID</th><th scope="col">条件</th><th scope="col">状態</th><th scope="col">進捗</th><th scope="col">操作</th></tr></thead><tbody>{history.map((run) => <tr key={run.run_id}><th scope="row"><input type="radio" name="compare-run" aria-label={`比較対象 ${run.run_id}`} checked={selectedCompareRun === run.run_id} onChange={() => setSelectedCompareRun(run.run_id)} /></th><td>{run.run_id}</td><td>{run.spec.symbol} / {run.spec.strategy} / {run.spec.start}〜{run.spec.end}</td><td><StateBadge state={stateForRun(run)} compact /></td><td>{run.progress_percent}%</td><td><button className="secondary-button" type="button" onClick={() => { setActiveRun(run); setSelectedCompareRun(run.run_id); void loadDetails(run.run_id) }}>結果を開く</button></td></tr>)}</tbody></table></div><div className="button-row"><button className="secondary-button" type="button" onClick={() => void submitCompare()}>選択Runと比較</button><button className="primary-button" type="button" disabled={!selectedRun || selectedRun.status !== 'SUCCEEDED'} onClick={() => void submitCsv()}>CSV生成</button></div>{compareResult && <div className="inline-notice" role="status">比較結果: comparable={String(compareResult.comparable)} / 理由={formatValue(compareResult.reason, 'なし')}</div>}{csvJob && <div className="inline-notice" role="status">CSV Job: {csvJob.status} / {csvJob.progress}% {csvJob.download_url && <a href={backtestApi.downloadCsv(csvJob.job_id)} download>CSVダウンロード</a>}</div>}</section>
        {runForDisplay?.status === 'SUCCEEDED' && <><Metrics run={runForDisplay} />{rows.length > 0 && <section className="panel-card"><LedgerTable rows={rows} /></section>}</>}
      </>}

      {tab === 'evaluation' && <>
        <section className="two-column-grid"><section className="sub-panel"><div className="section-heading"><div><p className="card-kicker">BT-MAN-13</p><h3>Holdout</h3></div><StateBadge state={holdout?.status === 'SUCCEEDED' ? 'NORMAL' : holdout?.status === 'STOPPED' ? 'STOPPED' : 'REQUIRED'} compact /></div><p className="muted">確定前のHoldoutは調整に使えません。確定後に一度だけ読み、調整へ再利用しません。</p><div className="button-row"><button className="secondary-button" type="button" onClick={() => void submitHoldout('EARLY_ADJUSTMENT')}>確定前を試す</button><button className="primary-button" type="button" onClick={() => void submitHoldout('FINALIZED')}>確定後に評価</button></div>{holdout && <p className="inline-notice" role={holdout.status === 'SUCCEEDED' ? 'status' : 'alert'}>{holdout.status} / {holdout.failure?.code ?? `${formatValue(holdout.row_count)} rows`}</p>}</section><section className="sub-panel"><div className="section-heading"><div><p className="card-kicker">BT-MAN-14 / BT-MAN-15</p><h3>Walk-forward</h3></div><StateBadge state={walkForward?.status === 'SUCCEEDED' ? 'NORMAL' : 'REQUIRED'} compact /></div><p className="muted">学習・検証・評価の時系列を分け、未来のDataを現在の条件決定に混ぜません。</p><div className="table-scroll"><table className="compact-table"><caption>固定ローカルfixtureでの3窓</caption><thead><tr><th>窓</th><th>学習終了</th><th>検証終了</th><th>評価終了</th></tr></thead><tbody>{windows.map((window) => <tr key={window.id}><th>{window.id}</th><td>{window.train_end}</td><td>{window.validation_end}</td><td>{window.evaluation_end}</td></tr>)}</tbody></table></div><button className="primary-button" type="button" onClick={() => void submitWalkForward()}>Walk-forward実行</button>{walkForward && <p className="inline-notice" role="status">{walkForward.status} / 窓 {walkForward.windows.length} / holdout再利用={String(walkForward.holdout_reused)}</p>}</section></section>
      </>}

      {(message || error) && <p className={error ? 'inline-notice error-notice' : 'inline-notice'} role={error ? 'alert' : 'status'}>{error || message}</p>}
      <HelpTip title="P5Rの完了条件">UI操作がApplication APIへ届き、Preflight、実Run、結果5指標、Ledger、取消／再開、Sweep、履歴／比較、CSV、Holdout、Walk-forwardの結果と停止理由を確認できること。実データの外部取得や実注文はP5Rの完了条件に含めません。</HelpTip>
      <P5RStateControls demoState={demoState} onStateChange={onStateChange} />
    </div>
  )
}
