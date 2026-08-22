import { useEffect, useMemo, useState } from 'react'
import { ConfirmDialog, EmptyState, ErrorState, HelpTip, ProgressBar, StateAlert, StateBadge, type ScreenDefinition, type UiState } from './ui'
import {
  defaultP5R2BacktestSpec,
  isP5R2StrategyTimeframe,
  P5R2_STRATEGY_TIMEFRAMES,
  p5r2Api,
  type P5R2BacktestSpec,
  type P5R2CatalogItem,
  type P5R2CatalogResponse,
  type P5R2DataRequirement,
  type P5R2GenerationJob,
  type P5R2RequestedRange,
  type P5R2RunView,
  type P5R2StrategyTimeframe,
} from './p5r2Api'

type P5R2WebProductScreenProps = {
  screen: ScreenDefinition
  onOpenLegacy: () => void
}

type GenerationForm = {
  symbol: string
  sourceDatasetId: string
  timeframes: P5R2StrategyTimeframe[]
  range: P5R2RequestedRange
}

const isCancellable = (status: string) => status === 'QUEUED' || status === 'RUNNING'

const uiStateForRun = (run: P5R2RunView): UiState => {
  if (run.status === 'SUCCEEDED') return 'NORMAL'
  if (isCancellable(run.status)) return 'LOADING'
  if (run.status === 'CANCELLED') return 'STOPPED'
  if (run.status === 'RECOVERY_REQUIRED') return 'RECOVERY'
  if (run.status === 'FAILED') return 'FAILED'
  return 'WARNING'
}

const uiStateForJob = (job: P5R2GenerationJob | null): UiState => {
  if (!job) return 'EMPTY'
  if (job.state === 'STAGED' || job.state === 'QUEUED' || job.state === 'RUNNING') return 'LOADING'
  if (job.state === 'CANCELLED' || job.state === 'REJECTED') return 'STOPPED'
  if (job.state === 'RECOVERY_REQUIRED') return 'RECOVERY'
  if (job.state === 'FAILED') return 'FAILED'
  return 'WARNING'
}

function text(value: unknown, fallback = '—') {
  return typeof value === 'string' && value.length > 0 ? value : fallback
}

function rangeFor(item: P5R2CatalogItem | undefined): P5R2RequestedRange | null {
  const candidate = item?.coverage ?? item?.period
  if (!candidate || typeof candidate.start !== 'string' || typeof candidate.end !== 'string') return null
  return { start: candidate.start, end: candidate.end }
}

function sourceCandidates(catalog: P5R2CatalogResponse | null, symbol: string) {
  return (catalog?.items ?? []).filter((item) => (
    item.symbol === symbol
    && item.source_timeframe === '1m'
    && item.usable === true
    && item.legacy !== true
    && item.state !== 'RECOVERY_REQUIRED'
  ))
}

function cancellationReason(run: P5R2RunView) {
  if (isCancellable(run.status)) return '取消できます。処理中は同じRunへの二重操作を防ぎます。'
  if (run.status === 'CANCELLED') return 'すでに取消済みです。'
  if (run.status === 'SUCCEEDED') return '完了済みのRunは取消できません。結果表示はDELETE-G1未承認のため削除できません。'
  if (run.status === 'RECOVERY_REQUIRED') return '復旧確認が必要なため取消操作は受け付けません。'
  return '現在のRun状態では取消できません。'
}

function SourceCatalogTable({ catalog, jobStates }: { catalog: P5R2CatalogResponse; jobStates: Record<string, string> }) {
  if (catalog.items.length === 0) {
    return <EmptyState title="現在使用可能なヒストリカルDataはありません" />
  }
  return (
    <div className="table-scroll" data-testid="p5r2-catalog-table">
      <table className="data-table p5r2-catalog-table">
        <caption>Application APIのCatalog。実データの内容や絶対pathは表示しません。</caption>
        <thead>
          <tr><th scope="col">銘柄</th><th scope="col">時間足</th><th scope="col">期間</th><th scope="col">品質</th><th scope="col">利用可</th><th scope="col">旧Data</th><th scope="col">Job状態</th><th scope="col">由来</th></tr>
        </thead>
        <tbody>
          {catalog.items.map((item) => {
            const sourceJobId = item.provenance?.source_job_id
            const jobState = typeof sourceJobId === 'string' ? jobStates[sourceJobId] : undefined
            const range = rangeFor(item)
            return <tr key={item.dataset_id}>
              <th scope="row">{text(item.symbol)}</th>
              <td>{text(item.data_timeframe ?? item.timeframe)}</td>
              <td>{range ? `${range.start} 〜 ${range.end}` : '期間未登録'}</td>
              <td>{text(item.quality)}</td>
              <td>{item.usable === true ? '利用可能' : '利用不可'}</td>
              <td>{item.legacy === true ? '旧Data' : '現行'}</td>
              <td>{jobState ?? text(item.state, '未登録')}</td>
              <td>{text(sourceJobId, 'Catalog登録')}</td>
            </tr>
          })}
        </tbody>
      </table>
    </div>
  )
}

function RunStateCard({ run, onCancel, busy }: { run: P5R2RunView; onCancel: (run: P5R2RunView) => void; busy: boolean }) {
  const canCancel = isCancellable(run.status)
  return (
    <article className="run-card" data-testid={`p5r2-run-${run.run_id}`}>
      <div className="section-heading">
        <div><p className="card-kicker">Application API / {run.kind}</p><h3>{run.run_id}</h3></div>
        <StateBadge state={uiStateForRun(run)} compact />
      </div>
      <dl className="definition-list p5r2-run-definition">
        <div><dt>Run状態</dt><dd>{run.status}</dd></div>
        <div><dt>進捗</dt><dd>{run.progress_percent}% / {run.progress} of {run.total}</dd></div>
        <div><dt>条件</dt><dd>{text(run.spec.symbol)} / {text(run.spec.timeframe)} / {text(run.spec.strategy)}</dd></div>
        <div><dt>取消可否</dt><dd>{cancellationReason(run)}</dd></div>
        {run.failure && <div><dt>停止理由</dt><dd>{run.failure.code}: {text(run.failure.message, '詳細なし')}</dd></div>}
      </dl>
      <ProgressBar value={run.progress_percent} label={`${run.run_id} の進捗`} />
      <div className="button-row compact-buttons">
        <button className="secondary-button" type="button" disabled={!canCancel || busy} onClick={() => onCancel(run)}>{busy ? '取消処理中' : '取消'}</button>
      </div>
    </article>
  )
}

function ResultProtectionPanel() {
  return (
    <section className="panel-card" aria-labelledby="p5r2-delete-gate-title" data-testid="p5r2-delete-gate">
      <div className="section-heading"><div><p className="card-kicker">ResultArtifact 保護</p><h3 id="p5r2-delete-gate-title">結果表示の削除はまだ実行できません</h3></div><StateBadge state="UNAPPROVED" compact /></div>
      <p className="muted">DELETE-G1が未承認です。CSV、Historical Data、Run、Audit、Evidenceは保護され、物理削除は行いません。</p>
      <button className="danger-button" type="button" disabled aria-describedby="p5r2-delete-gate-reason">結果表示を削除（DELETE-G1未承認）</button>
      <p id="p5r2-delete-gate-reason" className="inline-notice error-notice" role="status">DELETE_GATE_REQUIRED。削除APIは呼び出していません。</p>
    </section>
  )
}

export function P5R2WebProductScreen({ screen, onOpenLegacy }: P5R2WebProductScreenProps) {
  const [catalog, setCatalog] = useState<P5R2CatalogResponse | null>(null)
  const [jobStates, setJobStates] = useState<Record<string, string>>({})
  const [runs, setRuns] = useState<P5R2RunView[]>([])
  const [spec, setSpec] = useState<P5R2BacktestSpec>(defaultP5R2BacktestSpec)
  const [preflight, setPreflight] = useState<string>('まだ事前確認していません。')
  const [missingData, setMissingData] = useState<P5R2DataRequirement | null>(null)
  const [generation, setGeneration] = useState<GenerationForm | null>(null)
  const [generationJob, setGenerationJob] = useState<P5R2GenerationJob | null>(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [cancellingRunId, setCancellingRunId] = useState<string | null>(null)

  const p5r2Runs = useMemo(
    () => runs.filter((run) => isP5R2StrategyTimeframe(run.spec.timeframe)),
    [runs],
  )
  const generationSources = useMemo(
    () => sourceCandidates(catalog, generation?.symbol ?? spec.symbol),
    [catalog, generation?.symbol, spec.symbol],
  )
  const activeSource = generationSources.find((candidate) => candidate.dataset_id === generation?.sourceDatasetId) ?? generationSources[0]

  const refresh = async () => {
    setLoading(true)
    setError('')
    try {
      const [nextCatalog, nextRuns] = await Promise.all([p5r2Api.catalog(), p5r2Api.listRuns()])
      setCatalog(nextCatalog)
      setRuns(nextRuns.items)
      const sourceJobIds = nextCatalog.items
        .map((item) => item.provenance?.source_job_id)
        .filter((value): value is string => typeof value === 'string')
      const states = await Promise.all(sourceJobIds.map(async (jobId) => {
        try {
          const job = await p5r2Api.getTimeframeGenerationJob(jobId)
          return [jobId, job.state] as const
        } catch {
          return [jobId, '履歴未読込'] as const
        }
      }))
      setJobStates(Object.fromEntries(states))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Application APIへ接続できません。')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void refresh()
  }, [screen.id])

  const updateSpec = <Key extends keyof P5R2BacktestSpec>(key: Key, value: P5R2BacktestSpec[Key]) => {
    setSpec((current) => ({ ...current, [key]: value }))
    setPreflight('条件が変わりました。事前確認を実行してください。')
    setMessage('')
    setError('')
  }

  const openGenerationForSymbol = (symbol: string, initialTimeframe: P5R2StrategyTimeframe = '30m') => {
    const candidates = sourceCandidates(catalog, symbol)
    const candidate = candidates[0]
    const defaultRange = rangeFor(candidate)
    setGeneration({
      symbol,
      sourceDatasetId: candidate?.dataset_id ?? '',
      timeframes: [initialTimeframe],
      range: defaultRange ?? { start: '', end: '' },
    })
    setMissingData(null)
    setMessage(defaultRange
      ? '必要な時間足を生成する画面を開きました。現在利用可能な1m sourceの全期間を初期表示しています。'
      : '必要な時間足を生成する画面を開きました。現在利用可能な1m sourceがないため、期間の既定値は設定していません。')
  }

  const openGenerationFromRequirement = (requirement: P5R2DataRequirement) => {
    openGenerationForSymbol(
      requirement.symbol,
      isP5R2StrategyTimeframe(requirement.timeframe) ? requirement.timeframe : '30m',
    )
  }

  const submitPreflight = async () => {
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const response = await p5r2Api.preflight(spec)
      if (response.status === 'PASS') {
        setPreflight('PASS。現在利用可能な指定時間足Dataが確認できました。')
        setMessage('事前確認が完了しました。Backtestを開始できます。')
      } else {
        setPreflight(`STOPPED: ${response.failure?.code ?? 'PRECHECK_STOPPED'}`)
        if (response.failure?.code === 'DATA_INSUFFICIENT' && response.data_requirement) {
          setMissingData(response.data_requirement)
          setMessage('指定Dataが不足しています。生成確認を表示します。')
        } else {
          setError(response.failure?.message ?? response.failure?.code ?? '事前確認に失敗しました。')
        }
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : '事前確認に失敗しました。')
    } finally {
      setBusy(false)
    }
  }

  const submitRun = async () => {
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const response = await p5r2Api.createRun(spec)
      if ('run_id' in response) {
        setMessage(`${response.run_id}をApplication APIへ登録しました。`)
        await refresh()
      } else if (response.failure?.code === 'DATA_INSUFFICIENT' && response.data_requirement) {
        setMissingData(response.data_requirement)
        setPreflight('STOPPED: DATA_INSUFFICIENT')
      } else {
        setError(response.failure?.message ?? response.failure?.code ?? 'Runを開始できません。')
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Runを開始できません。')
    } finally {
      setBusy(false)
    }
  }

  const submitGeneration = async () => {
    if (!generation || !activeSource) {
      setError('生成元となる現在利用可能な1m sourceを選択してください。外部Dataの取得は開始しません。')
      return
    }
    if (!generation.range.start || !generation.range.end) {
      setError('生成する期間をUTCで入力してください。')
      return
    }
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const requestId = `p5r2-ui-generation-${activeSource.dataset_id}-${generation.timeframes.join('-')}-${generation.range.start.replace(/[^0-9]/g, '')}`
      const job = await p5r2Api.createTimeframeGenerationJob({
        source_dataset_id: activeSource.dataset_id,
        symbol: generation.symbol,
        timeframes: generation.timeframes,
        requested_range: generation.range,
        request_id: requestId,
        reason: 'USER_REQUESTED_FROM_P5R2_UI',
        retry_of: null,
        external_io_allowed: false,
      })
      setGenerationJob(job)
      if (job.state === 'STAGED') {
        setMessage(`${job.job_id}をローカル生成候補として登録しました。外部Data取得は行っていません。`)
      } else {
        setError(`時間足生成を受け付けませんでした: ${text(job.reason, '不明な理由')}`)
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : '時間足生成を開始できません。')
    } finally {
      setBusy(false)
    }
  }

  const transitionGeneration = async (action: 'advance' | 'cancel' | 'restart' | 'retry') => {
    if (!generationJob?.job_id) return
    setBusy(true)
    setError('')
    try {
      const nextJob = await p5r2Api.transitionTimeframeGenerationJob(generationJob, action)
      setGenerationJob(nextJob)
      setMessage(`${nextJob.job_id} の状態: ${nextJob.state} / ${text(nextJob.reason)}`)
      await refresh()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : '生成Jobを更新できません。')
    } finally {
      setBusy(false)
    }
  }

  const cancelRun = async (run: P5R2RunView) => {
    if (!isCancellable(run.status) || cancellingRunId) return
    setCancellingRunId(run.run_id)
    setError('')
    try {
      const response = await p5r2Api.cancelRun(run.run_id)
      setMessage(`${run.run_id} の取消要求: ${text(response.operation?.status, response.status)} / ${text(response.operation?.reason, 'Application APIで処理しました。')}`)
      await refresh()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Runの取消に失敗しました。')
    } finally {
      setCancellingRunId(null)
    }
  }

  const generationPanel = generation && (
    <section className="panel-card" aria-labelledby="p5r2-generation-title" data-testid="p5r2-generation-form">
      <div className="section-heading"><div><p className="card-kicker">時間足生成 / local-only</p><h3 id="p5r2-generation-title">指定時間足を生成する</h3></div><StateBadge state={uiStateForJob(generationJob)} compact /></div>
      <p className="muted">銘柄、複数の生成対象時間足、期間を選びます。元Dataは現在利用可能な1m sourceだけを使い、外部取得は行いません。</p>
      <div className="field-grid p5r2-field-grid">
        <label className="field-label" htmlFor="p5r2-generation-symbol"><span>生成する銘柄</span><select id="p5r2-generation-symbol" value={generation.symbol} onChange={(event) => setGeneration((current) => current && { ...current, symbol: event.target.value, sourceDatasetId: '' })}><option>BTCUSDT</option><option>ETHUSDT</option></select></label>
        <label className="field-label" htmlFor="p5r2-source-dataset"><span>元の1m source</span><select id="p5r2-source-dataset" value={activeSource?.dataset_id ?? ''} onChange={(event) => setGeneration((current) => current && { ...current, sourceDatasetId: event.target.value })}><option value="">選択してください</option>{generationSources.map((candidate) => <option value={candidate.dataset_id} key={candidate.dataset_id}>{candidate.dataset_id} / {rangeFor(candidate)?.start ?? '期間未登録'} 〜 {rangeFor(candidate)?.end ?? ''}</option>)}</select></label>
        <label className="field-label" htmlFor="p5r2-generation-start"><span>生成開始（UTC）</span><input id="p5r2-generation-start" value={generation.range.start} onChange={(event) => setGeneration((current) => current && { ...current, range: { ...current.range, start: event.target.value } })} placeholder="2025-02-24T00:00:00Z" /></label>
        <label className="field-label" htmlFor="p5r2-generation-end"><span>生成終了（UTC）</span><input id="p5r2-generation-end" value={generation.range.end} onChange={(event) => setGeneration((current) => current && { ...current, range: { ...current.range, end: event.target.value } })} placeholder="2025-02-24T01:00:00Z" /></label>
      </div>
      <fieldset className="p5r2-timeframe-checks"><legend>生成する時間足（複数選択可）</legend>{P5R2_STRATEGY_TIMEFRAMES.map((timeframe) => <label key={timeframe}><input type="checkbox" checked={generation.timeframes.includes(timeframe)} onChange={(event) => setGeneration((current) => {
        if (!current) return current
        const timeframes = event.target.checked ? [...current.timeframes, timeframe] : current.timeframes.filter((item) => item !== timeframe)
        return { ...current, timeframes }
      })} /> {timeframe}</label>)}</fieldset>
      {generationSources.length === 0 && <StateAlert state="REQUIRED" title="1m sourceが必要です">現在利用可能な1m sourceがないため、全期間の既定値は設定せず、生成要求も送信しません。</StateAlert>}
      <div className="button-row"><button className="primary-button" type="button" disabled={busy || generation.timeframes.length === 0 || !activeSource} onClick={() => void submitGeneration()}>時間足を生成する</button></div>
      {generationJob && <div className="p5r2-job-status" role="status"><strong>生成Job</strong><span>{generationJob.job_id ?? '未発行'} / {generationJob.state} / {text(generationJob.reason)}</span><div className="button-row compact-buttons">{generationJob.state === 'STAGED' && <button className="secondary-button" type="button" disabled={busy} onClick={() => void transitionGeneration('advance')}>生成を開始</button>}{['STAGED', 'QUEUED', 'RUNNING'].includes(generationJob.state) && <button className="secondary-button" type="button" disabled={busy} onClick={() => void transitionGeneration('cancel')}>生成を取消</button>}{generationJob.state === 'RECOVERY_REQUIRED' && <button className="secondary-button" type="button" disabled={busy} onClick={() => void transitionGeneration('restart')}>再開確認</button>}{generationJob.state === 'FAILED' && <button className="secondary-button" type="button" disabled={busy} onClick={() => void transitionGeneration('retry')}>再試行</button>}</div></div>}
    </section>
  )

  const conditionScreen = (
    <>
      <section className="p5r2-scope-strip" aria-label="P5R2 Web Product API契約" data-testid="p5r2-api-scope">
        <strong>P5R2 Web Product / 実Application API</strong><span>API: /api/p5r2/catalog・preflight・runs・timeframe-generation-jobs</span><span>戦略時間足: 15m / 30m / 1h / 4h / 1d</span><span>1m: source説明のみ</span>
      </section>
      <section className="two-column-grid">
        <section className="panel-card" aria-labelledby="p5r2-condition-title">
          <div className="section-heading"><div><p className="card-kicker">Single Backtest条件</p><h2 id="p5r2-condition-title">現在のCatalogを使って実行条件を確認</h2></div><StateBadge state={loading ? 'LOADING' : 'REQUIRED'} compact /></div>
          <div className="field-grid p5r2-field-grid">
            <label className="field-label" htmlFor="p5r2-symbol"><span>銘柄</span><select id="p5r2-symbol" value={spec.symbol} onChange={(event) => updateSpec('symbol', event.target.value as P5R2BacktestSpec['symbol'])}><option>BTCUSDT</option><option>ETHUSDT</option></select></label>
            <label className="field-label" htmlFor="p5r2-timeframe"><span>戦略時間足</span><select id="p5r2-timeframe" aria-label="戦略時間足" value={spec.timeframe} onChange={(event) => updateSpec('timeframe', event.target.value as P5R2StrategyTimeframe)}>{P5R2_STRATEGY_TIMEFRAMES.map((timeframe) => <option key={timeframe}>{timeframe}</option>)}</select></label>
            <label className="field-label" htmlFor="p5r2-start"><span>開始（UTC）</span><input id="p5r2-start" value={spec.start} onChange={(event) => updateSpec('start', event.target.value)} /></label>
            <label className="field-label" htmlFor="p5r2-end"><span>終了（UTC）</span><input id="p5r2-end" value={spec.end} onChange={(event) => updateSpec('end', event.target.value)} /></label>
            <label className="field-label" htmlFor="p5r2-strategy"><span>Backtest Strategy</span><select id="p5r2-strategy" value={spec.strategy} onChange={(event) => updateSpec('strategy', event.target.value as P5R2BacktestSpec['strategy'])}><option value="TURTLE_SYS1">TURTLE_SYS1</option><option value="TURTLE_SYS2">TURTLE_SYS2</option></select></label>
            <div className="field-label"><span>1m source</span><p className="p5r2-source-note">1mは生成元Dataの説明です。戦略時間足としては選択できません。</p></div>
          </div>
          <div className="button-row"><button className="secondary-button" type="button" disabled={busy} onClick={() => void submitPreflight()}>事前確認</button><button className="primary-button" type="button" disabled={busy} onClick={() => void submitRun()}>Single Backtest開始</button></div>
          <p className="inline-notice" role="status" data-testid="p5r2-preflight-status">{preflight}</p>
        </section>
        <section className="panel-card" aria-labelledby="p5r2-boundary-title">
          <div className="section-heading"><div><p className="card-kicker">外部Data境界</p><h2 id="p5r2-boundary-title">ヒストリカルData取得は停止中</h2></div><StateBadge state="UNAPPROVED" compact /></div>
          <p className="muted">P5R2-18 externalはHOST_LEVEL_ISOLATION_NOT_VERIFIEDです。Provider接続、Secret、費用、外部Data取得は行いません。</p>
          <button className="secondary-button" type="button" disabled aria-describedby="p5r2-download-reason">ヒストリカルDataをダウンロード（外部境界未検証）</button>
          <p id="p5r2-download-reason" className="inline-notice error-notice" role="status">HOST_LEVEL_ISOLATION_NOT_VERIFIED。download APIは呼び出していません。</p>
        </section>
      </section>
      <section className="panel-card" aria-labelledby="p5r2-catalog-title">
        <div className="section-heading"><div><p className="card-kicker">Data Catalog</p><h2 id="p5r2-catalog-title">現在使用可能なヒストリカルData</h2></div><div className="button-row compact-buttons"><button className="secondary-button" type="button" disabled={loading} onClick={() => void refresh()}>Catalogを更新</button><button className="secondary-button" type="button" onClick={() => openGenerationForSymbol(spec.symbol)}>時間足生成画面を開く</button></div></div>
        {catalog ? <SourceCatalogTable catalog={catalog} jobStates={jobStates} /> : loading ? <p className="muted">Application APIからCatalogを読み込んでいます。</p> : <ErrorState title="Catalogを読み込めません" detail="local Application APIの状態を確認してください。" />}
      </section>
      {generationPanel}
      <section className="panel-card p5r2-legacy-panel"><p className="muted">P5Rの旧1m画面は履歴確認だけのため、現在のP5R2機能とは分離しています。</p><button className="secondary-button" type="button" onClick={onOpenLegacy}>P5R旧履歴表示を開く</button></section>
    </>
  )

  const runScreen = (
    <>
      <section className="p5r2-scope-strip"><strong>実行一覧・進捗 / 実Application API</strong><span>Run state、進捗、取消可否・理由を同じAPI状態から表示</span></section>
      <section className="panel-card"><div className="section-heading"><div><p className="card-kicker">Backtest実行一覧・進捗</p><h2>現在のP5R2 Backtest Run</h2></div><button className="secondary-button" type="button" disabled={loading} onClick={() => void refresh()}>実行一覧を更新</button></div>{p5r2Runs.length > 0 ? <div className="run-list">{p5r2Runs.map((run) => <RunStateCard key={run.run_id} run={run} busy={cancellingRunId === run.run_id} onCancel={(candidate) => void cancelRun(candidate)} />)}</div> : <EmptyState title="P5R2のBacktest Runはありません" />}</section>
    </>
  )

  const resultScreen = (
    <>
      <section className="p5r2-scope-strip"><strong>Backtest結果サマリー / 実Application API</strong><span>Run state、取消可否・理由は実行一覧と同一</span></section>
      <section className="panel-card"><div className="section-heading"><div><p className="card-kicker">Backtest結果サマリー</p><h2>結果の表示対象</h2></div><button className="secondary-button" type="button" disabled={loading} onClick={() => void refresh()}>結果一覧を更新</button></div>{p5r2Runs.length > 0 ? <div className="run-list">{p5r2Runs.map((run) => <RunStateCard key={run.run_id} run={run} busy={cancellingRunId === run.run_id} onCancel={(candidate) => void cancelRun(candidate)} />)}</div> : <EmptyState title="表示できるP5R2結果はありません" />}</section>
      <ResultProtectionPanel />
    </>
  )

  return (
    <div className="screen-stack p5r2-web-product" data-testid={`screen-${screen.id}`} data-p5r2-real-api="true" data-reason-id="P5R2_APPLICATION_API">
      <section className="welcome-panel compact-panel"><div><p className="eyebrow">P5R2-19 / {screen.id} / 実Application API</p><h1>{screen.title}</h1><p className="lead">固定ダミーではなく、loopback-onlyのApplication APIから現在の状態を表示します。</p></div><StateBadge state={loading ? 'LOADING' : error ? 'FAILED' : 'NORMAL'} /></section>
      {error && <StateAlert state="FAILED" title="Application APIの応答を確認してください">{error}</StateAlert>}
      {message && <p className="inline-notice" role="status">{message}</p>}
      {screen.id === 'SCREEN-08' ? conditionScreen : screen.id === 'SCREEN-09' ? runScreen : resultScreen}
      <HelpTip title="この画面の安全境界">外部Dataの取得、Secret、Provider接続、費用、実削除、P6開始はこの画面から実行しません。Backtest計算はApplication APIの責務です。</HelpTip>
      <ConfirmDialog
        open={missingData !== null}
        onOpenChange={(open) => { if (!open) setMissingData(null) }}
        title="指定期間の時間足Dataが不足しています"
        description={missingData ? `${missingData.symbol} / ${missingData.timeframe} / ${missingData.requested_range.start} 〜 ${missingData.requested_range.end} のDataがありません。時間足生成画面へ移動しますか？` : ''}
        confirmLabel="時間足を生成する"
        cancelLabel="取消"
        onConfirm={() => { if (missingData) openGenerationFromRequirement(missingData) }}
      />
    </div>
  )
}
