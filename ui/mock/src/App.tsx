import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { Button as BaseButton, Dialog as BaseDialog } from '@base-ui/react'
import { allScreens, ConfirmDialog, EmptyState, ErrorState, HelpTip, MetricCard, navGroups, ProgressBar, seedData, StateAlert, StateBadge, type ScreenDefinition, type UiState } from './ui'
import { p4ScreenContracts, type P4ScreenContract } from './p4Contract'
import { P5RBacktestScreen } from './P5RBacktestScreen'
import './App.css'

function BaseDialogPilot() {
  const [open, setOpen] = useState(false)

  return (
    <BaseDialog.Root open={open} onOpenChange={setOpen}>
      <BaseDialog.Trigger render={<BaseButton className="primary-button" />}>
        Base UI Dialogを開く
      </BaseDialog.Trigger>
      <BaseDialog.Portal>
        <BaseDialog.Backdrop className="dialog-backdrop" />
        <BaseDialog.Popup className="dialog-popup" aria-label="Base UI Dialog">
          <BaseDialog.Title>Base UIの確認</BaseDialog.Title>
          <BaseDialog.Description>キーボードで閉じるボタンへ移動できるかを確認します。</BaseDialog.Description>
          <BaseDialog.Close render={<button className="secondary-button" type="button" />}>閉じる</BaseDialog.Close>
        </BaseDialog.Popup>
      </BaseDialog.Portal>
    </BaseDialog.Root>
  )
}

function UnitTable() {
  return (
    <div className="table-scroll" tabIndex={0}>
      <table className="data-table">
        <caption>固定Seed {seedData.seed} の匿名ダミー運用単位</caption>
        <thead>
          <tr><th scope="col">銘柄</th><th scope="col">単位ID</th><th scope="col">足</th><th scope="col">ルール</th><th scope="col">モード</th><th scope="col">状態</th><th scope="col">Signal</th><th scope="col">Position</th><th scope="col">警告</th></tr>
        </thead>
        <tbody>
          {seedData.units.map((unit) => (
            <tr key={unit.id} data-testid={`unit-${unit.id}`}>
              <th scope="row">{unit.symbol}</th>
              <td>{unit.id}</td><td>{unit.timeframe}</td><td>{unit.rule}</td><td>{unit.mode}</td>
              <td><StateBadge state={unit.state} compact /></td><td>{unit.signal}</td><td>{unit.position}</td><td>{unit.warning}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function HomeScreen({ onKill, demoState, onStateChange }: { onKill: () => void; demoState: UiState; onStateChange: (state: UiState) => void }) {
  const [submitted, setSubmitted] = useState(false)
  const [autoupdate, setAutoupdate] = useState(true)
  const [interval, setInterval] = useState('30')

  return (
    <div className="screen-stack" data-testid="screen-SCREEN-02">
      <section className="welcome-panel">
        <div>
          <p className="eyebrow">RQU-UI-07 / SCREEN-02 / E2E-UI-070</p>
          <h2>自動トレードUI基盤 Smoke</h2>
          <p className="lead">運用者が全インスタンスの状態を確認し、次の操作を選べる共通ホームです。</p>
        </div>
        <div className="welcome-actions">
          <StateBadge state="NORMAL" />
          <button className="danger-button" type="button" onClick={onKill}>全体Kill Switch</button>
        </div>
      </section>

      <section className="metric-grid" aria-label="全体指標">
        <MetricCard label="総残高（例）" value="¥1,250,000" detail="固定ダミー・未接続" />
        <MetricCard label="稼働単位" value="5" detail="初期目安3〜5" tone="positive" />
        <MetricCard label="警告" value="2" detail="Heartbeat / 未承認" tone="warning" />
        <MetricCard label="最新更新" value={seedData.asOf} detail="手動／自動を選択" />
      </section>

      <section className="panel-card" aria-labelledby="unit-list-title">
        <div className="section-heading"><div><p className="card-kicker">全インスタンス</p><h3 id="unit-list-title">運用単位の現在状況</h3></div><StateBadge state="NORMAL" compact /></div>
        <UnitTable />
      </section>

      <section className="two-column-grid">
        <article className="panel-card">
          <div className="section-heading"><div><p className="card-kicker">更新Controls</p><h3>最新データを更新</h3></div><StateBadge state="NORMAL" compact /></div>
          <div className="update-controls">
            <button className="secondary-button" type="button" data-testid="manual-refresh">手動更新</button>
            <label className="switch-label"><input type="checkbox" checked={autoupdate} onChange={(event) => setAutoupdate(event.target.checked)} /> 自動更新</label>
            <label htmlFor="refresh-interval">間隔[s]</label>
            <input id="refresh-interval" className="small-input" type="number" min="1" value={interval} onChange={(event) => setInterval(event.target.value)} />
          </div>
          <p className="muted">最終更新: {seedData.asOf}。SwitchがOFFでも手動更新できます。</p>
        </article>
        <article className="panel-card">
          <div className="section-heading"><div><p className="card-kicker">固定ダミー</p><h3>銘柄・時間足の対象</h3></div><StateBadge state="UNAPPROVED" compact /></div>
          <div className="tag-list" aria-label="初期候補">
            {seedData.symbols.map((symbol) => <span className="tag" key={symbol}>{symbol}</span>)}
          </div>
          <p className="muted">取引対象足: {seedData.timeframes.join(' / ')}。実シンボル・契約条件は未承認です。</p>
        </article>
      </section>

      <section className="panel-card pilot-card" aria-labelledby="component-pilot-title">
        <div className="section-heading"><div><p className="card-kicker">Design System / RQU-UI-03継承</p><h3 id="component-pilot-title">Dialog・Form・Focusの共通部品</h3></div><StateBadge state="REQUIRED" compact /></div>
        <div className="button-row"><BaseDialogPilot /></div>
        <form className="pilot-form" onSubmit={(event) => { event.preventDefault(); setSubmitted(true) }}>
          <label htmlFor="symbol">銘柄</label><input id="symbol" name="symbol" defaultValue="MCL" required />
          <label htmlFor="timeframe">時間足</label>
          <select id="timeframe" name="timeframe" defaultValue="D1"><option>D1</option><option>H4</option><option>H1</option><option>M30</option><option>M15</option></select>
          <button className="primary-button" type="submit">確認する</button>
          {submitted && <p className="success-message" role="status">入力内容を確認しました。</p>}
        </form>
        <HelpTip title="この部品の確認ポイント">label、focus、DialogのEscape、取消、色以外の状態文字が共通ルールです。</HelpTip>
      </section>
      <CoreStateControls demoState={demoState} onStateChange={onStateChange} />
    </div>
  )
}

const coreScreenIds: ScreenDefinition['id'][] = ['SCREEN-03', 'SCREEN-04', 'SCREEN-08', 'SCREEN-09', 'SCREEN-10', 'SCREEN-11', 'SCREEN-12']
const p4BoundaryScreenIds: ScreenDefinition['id'][] = ['SCREEN-01', 'SCREEN-18', 'SCREEN-21']
const boundaryOnlyScreenIds: ScreenDefinition['id'][] = ['SCREEN-05', 'SCREEN-06', 'SCREEN-07', 'SCREEN-13', 'SCREEN-14', 'SCREEN-15', 'SCREEN-16', 'SCREEN-20']

function P4ContractStrip({ screenId, contract }: { screenId: ScreenDefinition['id']; contract: P4ScreenContract }) {
  return <section className="p4-contract-strip" aria-label={`${screenId} P4 API契約`} data-testid={`p4-contract-${screenId}`} data-p4-scope={contract.scope} data-api-p4-ids={contract.apiIds.join(',')} data-reason-id={contract.reasonId}><strong>P4 UI契約: {contract.scope}</strong><span>API: {contract.apiIds.join(' / ')}</span><span>Reason: {contract.reasonId}</span><span>許可: {contract.allowed}</span><span>禁止: {contract.prohibited}</span></section>
}

function P4BoundaryScreen({ screen, contract, demoState, onStateChange }: { screen: ScreenDefinition; contract: P4ScreenContract; demoState: UiState; onStateChange: (state: UiState) => void }) {
  const isBoundaryOnly = contract.scope === 'BOUNDARY_ONLY'
  const state = isBoundaryOnly ? 'UNAPPROVED' : demoState
  return <div className="screen-stack" data-testid={`screen-${screen.id}`} data-p4-scope={contract.scope} data-reason-id={contract.reasonId}><section className="welcome-panel compact-panel"><div><p className="eyebrow">{screen.navId} / {screen.id} / {screen.e2eId}</p><h2>{screen.title}</h2><p className="lead">{screen.description}</p></div><StateBadge state={state} /></section><StateAlert state={state} title={isBoundaryOnly ? 'P4では実行できません' : undefined}>Reason ID: {contract.reasonId}。{contract.prohibited}</StateAlert><section className="panel-card"><h3>許可される表示</h3><p>{contract.allowed}</p><p className="muted">API binding: {contract.apiIds.join(' / ')}。固定匿名ダミーだけを表示し、P4-H2または後続Phaseの承認なしに状態変更を行いません。</p></section>{!isBoundaryOnly && <CoreStateControls demoState={demoState} onStateChange={onStateChange} />}</div>
}

function CoreStateControls({ demoState, onStateChange }: { demoState: UiState; onStateChange: (state: UiState) => void }) {
  const states: UiState[] = ['NORMAL', 'LOADING', 'EMPTY', 'REQUIRED', 'WARNING', 'STOPPED', 'FAILED', 'RECOVERY', 'HUMAN-GATE', 'UNAPPROVED']
  return (
    <section className="panel-card" aria-labelledby="core-state-title">
      <div className="section-heading"><div><p className="card-kicker">共通状態</p><h3 id="core-state-title">主要画面の状態を確認</h3></div><StateBadge state={demoState} compact /></div>
      <StateAlert state={demoState}>{stateLabels(demoState)}。画面ごとの開始条件・停止理由・次の操作を文字で確認できます。</StateAlert>
      <div className="state-switcher" aria-label="状態切替">
        {states.map((state) => <button className={demoState === state ? 'state-choice active' : 'state-choice'} type="button" key={state} onClick={() => onStateChange(state)}>{state}</button>)}
      </div>
    </section>
  )
}

function CoreScreen({ screen, demoState, onStateChange, onNavigate }: { screen: ScreenDefinition; demoState: UiState; onStateChange: (state: UiState) => void; onNavigate: (id: ScreenDefinition['id']) => void }) {
  const [tab, setTab] = useState<'single' | 'exhaustive'>('single')
  const [symbol, setSymbol] = useState('MCL')
  const [timeframe, setTimeframe] = useState('D1')
  const [strategy, setStrategy] = useState('Turtle System 1')
  const [risk, setRisk] = useState('')
  const [configFile, setConfigFile] = useState('未選択')
  const [parameterBounds, setParameterBounds] = useState({ entryLower: '20', entryUpper: '60', entryStep: '5', atrLower: '1.0', atrUpper: '3.0', atrStep: '0.5' })
  const [notice, setNotice] = useState('')
  const [runStarted, setRunStarted] = useState(false)
  const [unitRisk, setUnitRisk] = useState('')
  const [unitMode, setUnitMode] = useState('Backtest')
  const [unitNotice, setUnitNotice] = useState('')
  const [strategyEnabled, setStrategyEnabled] = useState<Record<string, boolean>>({ 'Turtle System 1': true, 'Turtle System 2': true })
  const [hiddenRuns, setHiddenRuns] = useState<string[]>([])
  const [selectedRuns, setSelectedRuns] = useState<string[]>(['RUN-20260811-001', 'RUN-20260811-002'])
  const [dangerAction, setDangerAction] = useState<null | 'stop' | 'delete-run' | 'delete-unit'>(null)
  const [dangerTarget, setDangerTarget] = useState('')
  const [strategyNotice, setStrategyNotice] = useState('')
  const [runAction, setRunAction] = useState<null | { kind: 'cancel' | 'rerun'; id: string }>(null)
  const [unitAction, setUnitAction] = useState<null | { kind: 'pause' | 'resume'; id: string }>(null)
  const [strategyAction, setStrategyAction] = useState<null | { kind: 'toggle' | 'save' | 'rollback'; name?: string }>(null)
  const [strategyReason, setStrategyReason] = useState('')

  const singleRunDisabled = risk.trim() === '' || demoState === 'UNAPPROVED' || demoState === 'STOPPED'
  const valueCount = (lower: string, upper: string, step: string) => {
    const low = Number(lower)
    const high = Number(upper)
    const increment = Number(step)
    if (!Number.isFinite(low) || !Number.isFinite(high) || !Number.isFinite(increment) || increment <= 0 || high < low) return 0
    return Math.floor((high - low) / increment + 1e-9) + 1
  }
  const exhaustiveCount = valueCount(parameterBounds.entryLower, parameterBounds.entryUpper, parameterBounds.entryStep) * valueCount(parameterBounds.atrLower, parameterBounds.atrUpper, parameterBounds.atrStep)
  const runRows = [
    { id: 'RUN-20260811-001', kind: '単一Run', status: '成功', progress: 100, elapsed: '00:01:12', estimate: '完了', result: '結果あり' },
    { id: 'RUN-20260811-002', kind: '網羅検証', status: '実行中', progress: 64, elapsed: '00:02:10', estimate: '残り00:01:14', result: '途中' },
    { id: 'RUN-20260811-003', kind: '単一Run', status: '一部失敗', progress: 100, elapsed: '00:00:48', estimate: '完了', result: '警告あり' },
  ]
  const resultRows = [
    { id: 'RUN-20260811-001', symbol: 'MCL', timeframe: 'D1', pnl: '+¥82,400', drawdown: '-¥21,500', trades: '18', winRate: '55.6%', balance: '¥1,332,400' },
    { id: 'RUN-20260811-004', symbol: 'M6A', timeframe: 'H4', pnl: '+¥61,200', drawdown: '-¥18,300', trades: '22', winRate: '50.0%', balance: '¥1,311,200' },
    { id: 'RUN-20260811-005', symbol: 'MZW', timeframe: 'M15', pnl: '-¥12,800', drawdown: '-¥34,100', trades: '41', winRate: '41.5%', balance: '¥1,237,200' },
  ]

  const formField = (label: string, control: ReactNode) => <label className="field-label"><span>{label}</span>{control}</label>

  const renderBacktest = () => (
    <>
      <div className="tab-list" role="tablist" aria-label="Backtest種別">
        <button className={tab === 'single' ? 'tab-button active' : 'tab-button'} type="button" role="tab" aria-selected={tab === 'single'} onClick={() => setTab('single')}>単一Run</button>
        <button className={tab === 'exhaustive' ? 'tab-button active' : 'tab-button'} type="button" role="tab" aria-selected={tab === 'exhaustive'} onClick={() => setTab('exhaustive')}>網羅検証</button>
      </div>
      <div className="two-column-grid">
        <section className="sub-panel" aria-labelledby="backtest-condition-title">
          <div className="section-heading"><div><p className="card-kicker">条件入力</p><h3 id="backtest-condition-title">{tab === 'single' ? '1つの条件で実行' : '全パラメータ組合せを検証'}</h3></div><StateBadge state={risk ? 'NORMAL' : 'REQUIRED'} compact /></div>
          <div className="field-grid">
            {formField('銘柄', <select value={symbol} onChange={(event) => setSymbol(event.target.value)}>{seedData.symbols.map((item) => <option key={item}>{item}</option>)}</select>)}
            {formField('時間足', <select value={timeframe} onChange={(event) => setTimeframe(event.target.value)}>{seedData.timeframes.map((item) => <option key={item}>{item}</option>)}</select>)}
            {formField('売買ルール', <select value={strategy} onChange={(event) => setStrategy(event.target.value)}><option>Turtle System 1</option><option>Turtle System 2</option></select>)}
            {formField('期間', <input type="text" defaultValue="2020-01-01〜2026-08-10" aria-label="期間" />)}
            {formField('Risk', <input type="number" min="0" step="0.1" value={risk} onChange={(event) => setRisk(event.target.value)} placeholder="入力必須" aria-label="Risk" />)}
            {formField('コスト', <input type="text" defaultValue="固定ダミー" aria-label="コスト" />)}
          </div>
          <div className="button-row">
            <button className="secondary-button" type="button" onClick={() => { setConfigFile('backtest-config.example.json'); setNotice('設定ファイルを読み込みました（表示用・外部読込なし）。') }}>設定ファイル読込</button>
            <label className="secondary-button file-button"><span>設定JSONを選択</span><input type="file" accept=".json,application/json" aria-label="設定JSONを選択" onChange={(event) => { const file = event.target.files?.[0]; if (file) { setConfigFile(file.name); setNotice(`${file.name}を読み込み候補として表示しました（内容の検査は後続実装）。`) } }} /></label>
            <span className="small-label">{configFile}</span>
          </div>
        </section>
        <section className="sub-panel" aria-labelledby="backtest-check-title">
          <div className="section-heading"><div><p className="card-kicker">開始前確認</p><h3 id="backtest-check-title">条件と組合せ数</h3></div><StateBadge state={singleRunDisabled ? 'REQUIRED' : 'NORMAL'} compact /></div>
          {tab === 'single' ? <ul className="check-list"><li>対象: {symbol} / {timeframe} / {strategy}</li><li>Risk: {risk || '未入力（開始不可）'}</li><li>データ品質: 固定ダミーは確認済み</li></ul> : <><div className="table-scroll"><table className="compact-table"><caption>変更するパラメータの下限・上限・ステップ</caption><thead><tr><th>パラメータ</th><th>下限</th><th>上限</th><th>ステップ</th></tr></thead><tbody><tr><th>Entry期間</th><td><input aria-label="Entry期間 下限" value={parameterBounds.entryLower} onChange={(event) => setParameterBounds((current) => ({ ...current, entryLower: event.target.value }))} /></td><td><input aria-label="Entry期間 上限" value={parameterBounds.entryUpper} onChange={(event) => setParameterBounds((current) => ({ ...current, entryUpper: event.target.value }))} /></td><td><input aria-label="Entry期間 ステップ" value={parameterBounds.entryStep} onChange={(event) => setParameterBounds((current) => ({ ...current, entryStep: event.target.value }))} /></td></tr><tr><th>ATR係数</th><td><input aria-label="ATR係数 下限" value={parameterBounds.atrLower} onChange={(event) => setParameterBounds((current) => ({ ...current, atrLower: event.target.value }))} /></td><td><input aria-label="ATR係数 上限" value={parameterBounds.atrUpper} onChange={(event) => setParameterBounds((current) => ({ ...current, atrUpper: event.target.value }))} /></td><td><input aria-label="ATR係数 ステップ" value={parameterBounds.atrStep} onChange={(event) => setParameterBounds((current) => ({ ...current, atrStep: event.target.value }))} /></td></tr></tbody></table></div><p className="muted">組合せ数: <strong>{exhaustiveCount}</strong>件。下限・上限・ステップの組合せを全て確認してから実行します。</p></>}
          <div className="button-row"><button className="secondary-button" type="button" onClick={() => { if (!risk) { setNotice('Riskが未入力のため、開始できません。'); onStateChange('REQUIRED') } else { setNotice('事前検証が完了しました（固定ダミー）。'); onStateChange('NORMAL') } }}>事前検証</button><button className="primary-button" type="button" disabled={singleRunDisabled} onClick={() => { setRunStarted(true); setNotice(tab === 'single' ? '単一Runを待ち行列へ追加しました。' : `${exhaustiveCount}件の網羅検証を待ち行列へ追加しました。`); onStateChange('LOADING'); onNavigate('SCREEN-09') }}>開始</button></div>
          {runStarted && <p className="success-message" role="status">実行一覧へ移動しました。</p>}
          {notice && <p className="inline-notice" role="status">{notice}</p>}
        </section>
      </div>
      <HelpTip title="単一Runと網羅検証の違い">単一Runは1つのパラメータセットだけを実行します。網羅検証は各パラメータの下限・上限・ステップから全組合せを作り、5指標を表で比較します。</HelpTip>
    </>
  )

  const renderRunList = () => (
    <>
      <div className="section-heading"><div><p className="card-kicker">待ち行列</p><h3>単一Run・網羅検証の進捗</h3></div><button className="secondary-button" type="button" onClick={() => onNavigate('SCREEN-08')}>条件設定へ戻る</button></div>
      <div className="run-list">{runRows.filter((row) => !hiddenRuns.includes(row.id)).map((row) => <article className="run-card" key={row.id} data-testid={`run-${row.id}`}><div className="section-heading"><div><strong>{row.id}</strong><p className="muted">{row.kind} / {row.status} / 経過 {row.elapsed} / {row.estimate}</p></div><StateBadge state={row.status === '成功' ? 'NORMAL' : row.status === '実行中' ? 'LOADING' : 'WARNING'} compact /></div><ProgressBar value={row.progress} label={`${row.id} 進捗`} /><div className="button-row"><button className="secondary-button" type="button" onClick={() => setRunAction({ kind: 'cancel', id: row.id })} disabled={row.status === '成功'}>取消</button><button className="secondary-button" type="button" onClick={() => setRunAction({ kind: 'rerun', id: row.id })}>再実行</button><button className="primary-button" type="button" onClick={() => onNavigate('SCREEN-10')} disabled={row.status === '実行中'}>結果</button><button className="secondary-button" type="button" onClick={() => setNotice(`${row.id}のCSV出力を非同期で受付しました。`)}>CSV出力</button><button className="secondary-button" type="button" onClick={() => setHiddenRuns((current) => [...current, row.id])}>通常一覧から隠す</button></div></article>)}</div>
      {notice && <p className="inline-notice" role="status">{notice}</p>}
      <HelpTip title="停止・再実行">実行中は進捗と残り見積を表示します。取消・再実行は確認を経て操作記録へ残す想定です。実際のWorkerは接続していません。</HelpTip>
      <ConfirmDialog open={runAction !== null} onOpenChange={(open) => !open && setRunAction(null)} title={runAction?.kind === 'cancel' ? `${runAction.id}を取消しますか？` : `${runAction?.id ?? 'Run'}を再実行しますか？`} description="対象Run、理由、時刻を操作記録へ残してから処理を受付します。実Workerは未接続です。" confirmLabel={runAction?.kind === 'cancel' ? '取消を記録' : '再実行を記録'} cancelLabel="取消" danger={runAction?.kind === 'cancel'} onConfirm={() => { if (runAction) setNotice(`${runAction.id}の${runAction.kind === 'cancel' ? '取消' : '再実行'}を操作記録へ残しました。`); setRunAction(null) }} />
    </>
  )

  const renderUnitList = () => (
    <>
      <div className="section-heading"><div><p className="card-kicker">独立インスタンス</p><h3>銘柄×時間足×売買ルール</h3></div><button className="primary-button" type="button" onClick={() => onNavigate('SCREEN-04')}>新規作成</button></div>
      <div className="table-scroll"><table className="data-table unit-table"><caption>同じ銘柄×時間足の重複は開始不可</caption><thead><tr><th>単位ID</th><th>銘柄</th><th>時間足</th><th>ルール</th><th>モード</th><th>状態</th><th>最終更新</th><th>操作</th></tr></thead><tbody>{seedData.units.map((unit) => <tr key={unit.id}><th scope="row">{unit.id}</th><td>{unit.symbol}</td><td>{unit.timeframe}</td><td>{unit.rule}</td><td>{unit.mode}</td><td><StateBadge state={unit.state} compact /></td><td>{seedData.asOf}</td><td><div className="button-row compact-buttons"><button className="secondary-button" type="button" onClick={() => setUnitAction({ kind: unit.state === 'STOPPED' ? 'resume' : 'pause', id: unit.id })}>{unit.state === 'STOPPED' ? '再開' : '一時停止'}</button><button className="secondary-button" type="button" onClick={() => { setDangerAction('delete-unit'); setDangerTarget(unit.id) }}>削除</button></div></td></tr>)}<tr className="blocked-row"><th scope="row">候補（重複）</th><td>MCL</td><td>D1</td><td>Turtle System 1</td><td>Live候補</td><td><StateBadge state="WARNING" compact /></td><td>開始不可</td><td>既存UNIT-001と重複</td></tr></tbody></table></div>
      {unitNotice && <p className="inline-notice" role="status">{unitNotice}</p>}
      <HelpTip title="同時運用の単位">異なる銘柄×時間足の組合せは独立インスタンスとして同時に動かせます。同じ組合せを別ルールで重ねる場合は開始不可です。</HelpTip>
      <ConfirmDialog open={dangerAction === 'delete-unit'} onOpenChange={(open) => !open && setDangerAction(null)} title={`${dangerTarget}を削除しますか？`} description="通常一覧から隠し、操作記録へ残す表示用確認です。実データは削除しません。" confirmLabel="削除する" cancelLabel="取消" danger onConfirm={() => { setUnitNotice(`${dangerTarget}を削除対象として記録しました。`); setDangerAction(null) }} />
      <ConfirmDialog open={unitAction !== null} onOpenChange={(open) => !open && setUnitAction(null)} title={unitAction?.kind === 'pause' ? `${unitAction.id}を一時停止しますか？` : `${unitAction?.id ?? '運用単位'}を再開しますか？`} description="対象、理由、時刻を操作記録へ残してから状態を変更します。照合が必要な場合は再開できません。" confirmLabel={unitAction?.kind === 'pause' ? '一時停止を記録' : '再開を記録'} cancelLabel="取消" danger={unitAction?.kind === 'pause'} onConfirm={() => { if (unitAction) setUnitNotice(`${unitAction.id}を${unitAction.kind === 'pause' ? '一時停止' : '再開'}対象として記録しました。`); setUnitAction(null) }} />
    </>
  )

  const renderUnitForm = () => {
    const duplicate = seedData.units.some((unit) => unit.symbol === symbol && unit.timeframe === timeframe)
    const cannotSave = !unitRisk || duplicate || demoState === 'UNAPPROVED'
    return <>
      <div className="section-heading"><div><p className="card-kicker">運用単位の作成・編集</p><h3>1単位の設定</h3></div><StateBadge state={cannotSave ? 'REQUIRED' : 'NORMAL'} compact /></div>
      <div className="field-grid two-column-fields">
        {formField('Asset Class', <select defaultValue="先物"><option>先物</option><option>株式</option><option>FX</option><option>暗号資産</option></select>)}
        {formField('銘柄', <select value={symbol} onChange={(event) => setSymbol(event.target.value)}>{seedData.symbols.map((item) => <option key={item}>{item}</option>)}</select>)}
        {formField('時間足', <select value={timeframe} onChange={(event) => setTimeframe(event.target.value)}>{seedData.timeframes.map((item) => <option key={item}>{item}</option>)}</select>)}
        {formField('Strategy', <select value={strategy} onChange={(event) => setStrategy(event.target.value)}><option>Turtle System 1</option><option>Turtle System 2</option></select>)}
        {formField('モード', <select value={unitMode} onChange={(event) => setUnitMode(event.target.value)}><option>Backtest</option><option>Forward</option><option>Shadow</option><option>Paper</option><option>Live候補</option><option>Live</option></select>)}
        {formField('Risk', <input type="number" min="0" step="0.1" value={unitRisk} onChange={(event) => setUnitRisk(event.target.value)} placeholder="入力必須" aria-label="運用単位Risk" />)}
      </div>
      {duplicate && <StateAlert state="WARNING">同じ銘柄×時間足の運用単位が既に存在するため、売買ルールが異なっても開始できません。</StateAlert>}
      {!unitRisk && <StateAlert state="REQUIRED">Risk未入力のため、すべてのモードで開始できません。値の範囲・整合性検査はこのモックでは行いません。</StateAlert>}
      <div className="button-row"><button className="secondary-button" type="button" onClick={() => setUnitNotice(cannotSave ? '入力不足または重複のため、事前検証を完了できません。' : '事前検証が完了しました。')}>事前検証</button><button className="primary-button" type="button" disabled={cannotSave} onClick={() => { setUnitNotice('運用単位を保存しました。開始は承認状態を確認してから行います。'); onNavigate('SCREEN-03') }}>保存</button><button className="secondary-button" type="button" onClick={() => onNavigate('SCREEN-03')}>取消</button></div>
      {unitNotice && <p className="inline-notice" role="status">{unitNotice}</p>}
    </>
  }

  const renderStrategyList = () => (
    <>
      <div className="section-heading"><div><p className="card-kicker">Strategy一覧</p><h3>Turtle System 1 / 2 と設定版</h3></div><button className="primary-button" type="button" onClick={() => onNavigate('SCREEN-07')}>新規／新版</button></div>
      <label className="field-label"><span>操作理由（有効化・無効化・保存・ロールバック共通）</span><input value={strategyReason} onChange={(event) => setStrategyReason(event.target.value)} placeholder="理由を入力すると操作できます" /></label>
      <div className="table-scroll"><table className="data-table"><caption>有効化・無効化は理由を表示して記録する</caption><thead><tr><th>Strategy</th><th>版</th><th>hash</th><th>Long/Short</th><th>利用単位数</th><th>状態</th><th>操作</th></tr></thead><tbody>{['Turtle System 1', 'Turtle System 2'].map((name, index) => <tr key={name}><th scope="row">{name}</th><td>v1.{index + 1}</td><td>sha256-demo-{index + 1}</td><td>Long / Short</td><td>{index + 2}</td><td><StateBadge state={strategyEnabled[name] ? 'NORMAL' : 'STOPPED'} compact /></td><td><div className="button-row compact-buttons"><button className="secondary-button" type="button" disabled={!strategyReason.trim()} onClick={() => setStrategyAction({ kind: 'toggle', name })}>{strategyEnabled[name] ? '無効化' : '有効化'}</button><button className="secondary-button" type="button" onClick={() => setStrategyNotice(`${name}を比較対象へ追加しました。`)}>比較</button></div></td></tr>)}</tbody></table></div>
      {strategyNotice && <p className="inline-notice" role="status">{strategyNotice}</p>}
      <HelpTip title="設定版の扱い">稼働中の設定を上書きせず、保存時は新版を作成します。実行中単位への反映はHuman Gateで確認します。</HelpTip>
      <ConfirmDialog open={strategyAction !== null} onOpenChange={(open) => !open && setStrategyAction(null)} title={strategyAction?.kind === 'toggle' ? `${strategyAction.name ?? 'Strategy'}の状態を変更しますか？` : strategyAction?.kind === 'save' ? '設定版を保存しますか？' : '設定版をロールバックしますか？'} description={`理由: ${strategyReason || '未入力'}。対象、理由、時刻を操作記録へ残してから反映します。`} confirmLabel="確認して記録" cancelLabel="取消" danger={strategyAction?.kind === 'toggle' && strategyAction.name === 'Turtle System 1' && strategyEnabled['Turtle System 1']} onConfirm={() => { if (strategyAction?.kind === 'toggle' && strategyAction.name) setStrategyEnabled((current) => ({ ...current, [strategyAction.name as string]: !current[strategyAction.name as string] })); setStrategyNotice(`${strategyAction?.kind === 'rollback' ? 'ロールバック' : strategyAction?.kind === 'save' ? '設定版保存' : '有効化・無効化'}を操作記録へ残しました。`); setStrategyAction(null) }} />
    </>
  )

  const renderStrategyForm = () => (
    <>
      <div className="two-column-grid"><section className="sub-panel"><div className="section-heading"><div><p className="card-kicker">条件</p><h3>売買ルールの設定</h3></div><StateBadge state={demoState} compact /></div><div className="field-grid">{formField('variant', <select defaultValue="System 1"><option>System 1</option><option>System 2</option><option>設定版（複製）</option></select>)}{formField('Entry', <input defaultValue="20日高値／安値" aria-label="Entry" />)}{formField('Stop', <input defaultValue="2N" aria-label="Stop" />)}{formField('Exit', <input defaultValue="10日安値／高値" aria-label="Exit" />)}{formField('Long/Short', <select defaultValue="Long / Short"><option>Long / Short</option><option>Longのみ</option><option>Shortのみ</option></select>)}</div></section><section className="sub-panel"><div className="section-heading"><div><p className="card-kicker">差分</p><h3>保存前の確認</h3></div><StateBadge state="HUMAN-GATE" compact /></div><ul className="check-list"><li>既存版: Turtle System 1 v1.1</li><li>変更: Entry / Stop / Exit</li><li>保存: 設定版 v1.2 を新規作成</li><li>稼働中単位へ即時反映しない</li></ul></section></div>
      <label className="field-label"><span>操作理由（保存・ロールバック）</span><input value={strategyReason} onChange={(event) => setStrategyReason(event.target.value)} placeholder="理由を入力すると操作できます" /></label>
      <div className="button-row"><button className="secondary-button" type="button" onClick={() => setStrategyNotice('設定値を検証しました（固定ルール）。')}>検証</button><button className="primary-button" type="button" disabled={!strategyReason.trim()} onClick={() => setStrategyAction({ kind: 'save' })}>保存して新版</button><button className="secondary-button" type="button" onClick={() => setStrategyNotice('差分表示を開きました。')}>差分</button><button className="secondary-button" type="button" disabled={!strategyReason.trim()} onClick={() => setStrategyAction({ kind: 'rollback' })}>ロールバック</button><button className="secondary-button" type="button" onClick={() => onNavigate('SCREEN-06')}>取消</button></div>
      {strategyNotice && <p className="inline-notice" role="status">{strategyNotice}</p>}
      <ConfirmDialog open={strategyAction !== null} onOpenChange={(open) => !open && setStrategyAction(null)} title={strategyAction?.kind === 'save' ? '設定版を保存しますか？' : '設定版をロールバックしますか？'} description={`理由: ${strategyReason || '未入力'}。対象、理由、時刻を操作記録へ残してから反映します。`} confirmLabel="確認して記録" cancelLabel="取消" danger={strategyAction?.kind === 'rollback'} onConfirm={() => { setStrategyNotice(`${strategyAction?.kind === 'rollback' ? 'ロールバック' : '設定版保存'}を操作記録へ残しました。`); setStrategyAction(null) }} />
    </>
  )

  const renderResultSummary = () => (
    <>
      <div className="section-heading"><div><p className="card-kicker">単一Run結果</p><h3>RUN-20260811-001 / MCL × D1</h3></div><StateBadge state="NORMAL" compact /></div>
      <div className="metric-grid five-metrics"><MetricCard label="総損益" value="+¥82,400" detail="期間: 2020-01-01〜2026-08-10" tone="positive" /><MetricCard label="最大の落ち込み" value="-¥21,500" detail="固定ダミー" tone="warning" /><MetricCard label="取引回数" value="18" detail="Long 10 / Short 8" /><MetricCard label="勝率" value="55.6%" detail="10勝8敗" /><MetricCard label="総残高" value="¥1,332,400" detail="開始残高 ¥1,250,000" tone="positive" /></div>
      <div className="chart-placeholder" role="img" aria-label="資産曲線の固定ダミー"><span>資産曲線（固定ダミー）</span><div className="chart-line"><i /><i /><i /><i /><i /><i /><i /></div></div>
      <div className="button-row"><button className="primary-button" type="button" onClick={() => onNavigate('SCREEN-11')}>チャート・取引詳細</button><button className="secondary-button" type="button" onClick={() => onNavigate('SCREEN-12')}>比較</button><button className="secondary-button" type="button" onClick={() => setNotice('同じ条件のRunを新しく受付しました。')}>再Run</button><button className="secondary-button" type="button" onClick={() => setNotice('CSV出力を非同期で受付しました。')}>CSV出力</button><button className="secondary-button" type="button" onClick={() => setHiddenRuns((current) => [...current, 'RUN-20260811-001'])}>通常一覧から隠す</button><button className="danger-button" type="button" onClick={() => { setDangerAction('delete-run'); setDangerTarget('RUN-20260811-001') }}>削除</button></div>
      {notice && <p className="inline-notice" role="status">{notice}</p>}
      <ConfirmDialog open={dangerAction === 'delete-run'} onOpenChange={(open) => !open && setDangerAction(null)} title={`${dangerTarget}を削除しますか？`} description="通常一覧から隠し、内部の操作記録は保持する表示用確認です。" confirmLabel="削除する" cancelLabel="取消" danger onConfirm={() => { setHiddenRuns((current) => [...current, dangerTarget]); setNotice(`${dangerTarget}を削除対象として記録しました。`); setDangerAction(null) }} />
    </>
  )

  const renderDetail = () => (
    <>
      <div className="section-heading"><div><p className="card-kicker">チャート・取引・Signal</p><h3>想定と実績の差分を確認</h3></div><button className="secondary-button" type="button" onClick={() => onNavigate('SCREEN-10')}>結果へ戻る</button></div>
      <div className="filter-row"><label>銘柄<select defaultValue="MCL"><option>MCL</option><option>M6A</option><option>MZC</option><option>MZS</option><option>MZW</option></select></label><label>時間足<select defaultValue="D1"><option>D1</option><option>H4</option><option>H1</option><option>M30</option><option>M15</option></select></label><label>表示<select defaultValue="全て"><option>全て</option><option>Long</option><option>Short</option></select></label></div>
      <div className="chart-placeholder" role="img" aria-label="資産曲線とSignalの固定ダミー"><span>資産曲線＋Entry/Exit Signal（固定ダミー）</span><div className="chart-line tall"><i /><i /><i /><i /><i /><i /><i /><i /></div></div>
      <StateAlert state="WARNING">Signalの想定／実績に1件の差分があります。詳細を開いて停止・再計算の要否を運用者が判断します。</StateAlert>
      <div className="table-scroll"><table className="data-table"><caption>取引詳細</caption><thead><tr><th>日時</th><th>方向</th><th>数量</th><th>価格</th><th>Signal</th><th>差分</th></tr></thead><tbody><tr><th>2026-03-02 09:00</th><td>Long</td><td>1</td><td>72.40</td><td>Entry</td><td>なし</td></tr><tr><th>2026-04-15 09:00</th><td>Short</td><td>1</td><td>69.10</td><td>Exit</td><td>想定より1足遅れ</td></tr></tbody></table></div>
    </>
  )

  const renderComparison = () => (
    <>
      <div className="section-heading"><div><p className="card-kicker">Run比較</p><h3>複数Runの指標と条件差</h3></div><StateBadge state={selectedRuns.length >= 2 ? 'NORMAL' : 'REQUIRED'} compact /></div>
      <div className="button-row"><button className="secondary-button" type="button" onClick={() => setSelectedRuns((current) => current.length >= 3 ? current.slice(0, 2) : [...current, 'RUN-20260811-005'])}>比較対象追加</button><button className="secondary-button" type="button" onClick={() => setNotice('総損益の降順に並べ替えました。最良自動選択は行いません。')}>並替</button><button className="secondary-button" type="button" onClick={() => setNotice('比較レポートを生成しました（固定ダミー）。')}>レポート</button><button className="primary-button" type="button" onClick={() => onNavigate('SCREEN-08')}>再Run</button></div>
      <div className="table-scroll"><table className="data-table comparison-table"><caption>選択中 {selectedRuns.length}件。未承認Runは状態を表示して判断を委ねます。</caption><thead><tr><th>対象</th><th>総損益</th><th>最大の落ち込み</th><th>取引回数</th><th>勝率</th><th>総残高</th><th>設定hash</th></tr></thead><tbody>{resultRows.map((row) => <tr key={row.id}><th scope="row">{row.id}<br /><span className="muted">{row.symbol} / {row.timeframe}</span></th><td>{row.pnl}</td><td>{row.drawdown}</td><td>{row.trades}</td><td>{row.winRate}</td><td>{row.balance}</td><td>hash-{row.id.slice(-3)}</td></tr>)}</tbody></table></div>
      {notice && <p className="inline-notice" role="status">{notice}</p>}
      <HelpTip title="比較の判断">この画面は条件と5指標を並べるだけです。システムが最良Runを自動選択したり、Live昇格を自動承認したりしません。</HelpTip>
    </>
  )

  const body = screen.id === 'SCREEN-08' ? renderBacktest() : screen.id === 'SCREEN-09' ? renderRunList() : screen.id === 'SCREEN-03' ? renderUnitList() : screen.id === 'SCREEN-04' ? renderUnitForm() : screen.id === 'SCREEN-06' ? renderStrategyList() : screen.id === 'SCREEN-07' ? renderStrategyForm() : screen.id === 'SCREEN-10' ? renderResultSummary() : screen.id === 'SCREEN-11' ? renderDetail() : renderComparison()

  return (
    <div className="screen-stack" data-testid={`screen-${screen.id}`}>
      <section className="welcome-panel compact-panel"><div><p className="eyebrow">{screen.navId} / {screen.id} / {screen.e2eId}</p><h2>{screen.title}</h2><p className="lead">{screen.description}</p></div><StateBadge state={demoState} /></section>
      {body}
      <CoreStateControls demoState={demoState} onStateChange={onStateChange} />
    </div>
  )
}

const safetyScreenIds: ScreenDefinition['id'][] = ['SCREEN-01', 'SCREEN-05', 'SCREEN-13', 'SCREEN-14', 'SCREEN-15', 'SCREEN-16', 'SCREEN-17', 'SCREEN-18', 'SCREEN-19', 'SCREEN-20', 'SCREEN-21']

function SafetyScreen({ screen, demoState, onStateChange, onNavigate }: { screen: ScreenDefinition; demoState: UiState; onStateChange: (state: UiState) => void; onNavigate: (id: ScreenDefinition['id']) => void }) {
  const [notice, setNotice] = useState('')
  const [riskValue, setRiskValue] = useState('')
  const [autoApproval, setAutoApproval] = useState(false)
  const [gateMode, setGateMode] = useState<'確認と取消' | 'スキップ（自動承認）'>('確認と取消')
  const [gateConfirm, setGateConfirm] = useState(false)
  const [dangerAction, setDangerAction] = useState<null | 'stop' | 'delete-log'>(null)
  const [hiddenLogs, setHiddenLogs] = useState<string[]>([])
  const [warningRows, setWarningRows] = useState(['WARN-001', 'WARN-002'])

  const renderSystem = () => <>
    <div className="metric-grid four-metrics"><MetricCard label="対応Asset Class" value="4種類" detail="先物・株式・FX・暗号資産" /><MetricCard label="初期候補" value="5銘柄" detail="MCL / M6A / MZC / MZS / MZW" /><MetricCard label="取引対象足" value="5種類" detail="D1 / H4 / H1 / M30 / M15" /><MetricCard label="外部接続" value="未承認" detail="Broker・実データなし" tone="warning" /></div>
    <StateAlert state="UNAPPROVED">認証は不要ですが、安全確認・未承認項目の確認は必要です。実シンボル、契約条件、Broker接続が未承認のため、実運用開始ボタンは無効です。</StateAlert>
    <section className="sub-panel"><div className="section-heading"><div><p className="card-kicker">禁止事項</p><h3>このモックで実行しないこと</h3></div><button className="secondary-button" type="button" onClick={() => setNotice('状態を更新しました（固定ダミー）。')}>状態を更新</button></div><ul className="check-list"><li>実Broker・実市場データ・Secretへ接続しない</li><li>実注文・Paper注文・Live注文を送信しない</li><li>後続GateのRisk・契約条件・性能値を推測で確定しない</li></ul><div className="button-row"><button className="primary-button" type="button" disabled title="未承認のため開始できません">実運用を開始（未承認）</button><button className="secondary-button" type="button" onClick={() => onNavigate('SCREEN-18')}>Human Gateを確認</button></div>{notice && <p className="inline-notice" role="status">{notice}</p>}</section>
  </>

  const renderData = () => <>
    <div className="section-heading"><div><p className="card-kicker">市場データ品質</p><h3>最終時刻・欠落・版情報</h3></div><StateBadge state="WARNING" compact /></div>
    <div className="table-scroll"><table className="data-table"><caption>固定Seedの品質例。Calendar/Roll版は未確定。</caption><thead><tr><th>銘柄</th><th>時間足</th><th>最終時刻</th><th>欠落</th><th>重複</th><th>時刻逆行</th><th>状態</th><th>操作</th></tr></thead><tbody>{seedData.symbols.slice(0, 5).map((symbol, index) => <tr key={symbol}><th scope="row">{symbol}</th><td>{seedData.timeframes[index]}</td><td>{seedData.asOf}</td><td>{index === 1 ? '3本' : '0'}</td><td>0</td><td>0</td><td><StateBadge state={index === 1 ? 'WARNING' : 'NORMAL'} compact /></td><td><div className="button-row compact-buttons"><button className="secondary-button" type="button" onClick={() => setNotice(`${symbol}を再取得対象として受付しました。`)}>再取得</button><button className="secondary-button" type="button" onClick={() => setNotice(`${symbol}を再処理対象として受付しました。`)}>再処理</button></div></td></tr>)}</tbody></table></div>
    <div className="button-row"><button className="secondary-button" type="button" onClick={() => setNotice('固定ダミーのデータ検証を開始しました。')}>取得</button><button className="secondary-button" type="button" onClick={() => setNotice('インポート受付を表示しました（外部読込なし）。')}>インポート</button><button className="secondary-button" type="button" onClick={() => setNotice('自動更新はUI上の表示だけです。')}>自動更新</button></div>
    <StateAlert state="WARNING">欠落がある対象はBacktest・Forward・Paper・Live候補の開始前に停止理由を確認します。Calendar版・Roll版は未確定です。</StateAlert>
    {notice && <p className="inline-notice" role="status">{notice}</p>}
  </>

  const renderForward = () => <>
    <div className="two-column-grid"><section className="sub-panel"><div className="section-heading"><div><p className="card-kicker">Forward</p><h3>実データでの確認段階</h3></div><StateBadge state="HUMAN-GATE" compact /></div><p className="muted">最新データ時刻、Signal、Position、停止理由を確認します。実データには接続していません。</p><div className="button-row"><button className="danger-button" type="button" onClick={() => setDangerAction('stop')}>停止</button><button className="secondary-button" type="button" onClick={() => setNotice('Forwardの照合を受付しました。')}>照合</button></div></section><section className="sub-panel"><div className="section-heading"><div><p className="card-kicker">Shadow</p><h3>注文を送らない影運用</h3></div><StateBadge state="WARNING" compact /></div><p className="muted">仮想Signalと実データの差分を確認し、注文は常に停止します。</p><div className="button-row"><button className="secondary-button" type="button" onClick={() => setNotice('Shadowの差分を表示しました。')}>差分確認</button><button className="danger-button" type="button" onClick={() => setDangerAction('stop')}>停止</button></div></section></div><StateAlert state="RECOVERY">データ・注文・Positionの照合が終わるまで再開できません。手動再開はHuman Gateで確認します。</StateAlert>{notice && <p className="inline-notice" role="status">{notice}</p>}
  </>

  const renderPaperLive = () => <>
    <div className="two-column-grid"><section className="sub-panel"><div className="section-heading"><div><p className="card-kicker">Paper</p><h3>模擬注文</h3></div><StateBadge state="UNAPPROVED" compact /></div><p className="muted">Paperは実注文を送らず、注文・約定・Positionの流れだけを確認します。</p><button className="primary-button" type="button" disabled title="未承認のため開始できません">Paperを開始（未承認）</button></section><section className="sub-panel"><div className="section-heading"><div><p className="card-kicker">Live候補／Live</p><h3>昇格状態</h3></div><StateBadge state="HUMAN-GATE" compact /></div><p className="muted">Live候補は表示のみ。Live自動承認はHuman Gateの確認モードとして扱います。</p><div className="button-row"><button className="secondary-button" type="button" onClick={() => onNavigate('SCREEN-18')}>移行確認</button><button className="danger-button" type="button" onClick={() => setDangerAction('stop')}>停止</button></div></section></div><label className="switch-label"><input type="checkbox" checked={autoApproval} onChange={(event) => { const enabled = event.target.checked; setAutoApproval(enabled); setGateMode(enabled ? 'スキップ（自動承認）' : '確認と取消'); setNotice(enabled ? 'Live自動承認モードをHuman Gateの自動承認モードとして選択しました。' : 'Live自動承認モードをOFFにしました。') }} /> Live自動承認モード</label><HelpTip title="再起動後の安全境界">再起動後は自動承認をOFFに戻します。未承認のLive候補を自動で実注文へ進めません。</HelpTip>{notice && <p className="inline-notice" role="status">{notice}</p>}
  </>

  const renderPortfolio = () => <>
    <div className="metric-grid four-metrics"><MetricCard label="総残高（例）" value="¥1,250,000" detail="固定ダミー" /><MetricCard label="証拠金" value="¥320,000" detail="表示例" /><MetricCard label="余力" value="¥930,000" detail="表示例" tone="positive" /><MetricCard label="Risk設定" value={riskValue || '未入力'} detail="上限は設定画面から設定" tone={riskValue ? 'positive' : 'warning'} /></div>
    <section className="sub-panel"><div className="section-heading"><div><p className="card-kicker">Risk</p><h3>開始前の入力</h3></div><StateBadge state={riskValue ? 'NORMAL' : 'REQUIRED'} compact /></div><div className="field-grid"><label className="field-label"><span>Risk値</span><input type="number" min="0" step="0.1" value={riskValue} onChange={(event) => setRiskValue(event.target.value)} placeholder="未入力では開始不可" /></label><label className="field-label"><span>上限</span><input type="text" defaultValue="設定画面で設定" readOnly /></label></div><p className="muted">Risk値の範囲・整合性はこのUIでは検査しません。未入力だけを開始不可条件として扱います。</p><div className="button-row"><button className="primary-button" type="button" disabled={!riskValue} onClick={() => setNotice('Risk入力を確認しました。実注文には進みません。')}>開始条件を確認</button><button className="secondary-button" type="button" onClick={() => setNotice('Risk設定画面への導線を表示しました。')}>設定画面へ</button></div></section>{notice && <p className="inline-notice" role="status">{notice}</p>}
  </>

  const renderOrders = () => <>
    <StateAlert state="WARNING">Broker側の状態との差異は固定例です。差異が解消するまで新規注文を停止し、照合を優先します。</StateAlert><div className="table-scroll"><table className="data-table"><caption>注文・約定・Position（匿名固定）</caption><thead><tr><th>注文ID</th><th>単位</th><th>方向</th><th>数量</th><th>状態</th><th>Position</th><th>操作</th></tr></thead><tbody><tr><th>ORD-001</th><td>UNIT-001</td><td>Long</td><td>1</td><td><StateBadge state="WARNING" compact /></td><td>Long 1</td><td><button className="danger-button" type="button" onClick={() => setNotice('ORD-001の取消確認を表示しました。')}>取消</button></td></tr><tr><th>ORD-002</th><td>UNIT-003</td><td>Short</td><td>1</td><td><StateBadge state="NORMAL" compact /></td><td>0</td><td><button className="secondary-button" type="button" onClick={() => setNotice('ORD-002の約定詳細を表示しました。')}>詳細</button></td></tr></tbody></table></div><div className="button-row"><button className="secondary-button" type="button" onClick={() => setNotice('Position照合を受付しました。')}>照合</button><button className="danger-button" type="button" onClick={() => setDangerAction('stop')}>新規注文を停止</button></div>{notice && <p className="inline-notice" role="status">{notice}</p>}
  </>

  const renderWarnings = () => <>
    <div className="section-heading"><div><p className="card-kicker">警告・障害・通知</p><h3>影響と次の操作</h3></div><StateBadge state={warningRows.length ? 'WARNING' : 'NORMAL'} compact /></div><div className="run-list">{warningRows.map((id) => <article className="run-card" key={id}><div className="section-heading"><div><strong>{id}</strong><p className="muted">対象: {id === 'WARN-001' ? 'UNIT-002 Heartbeat' : '市場データ M6A/H4'} / 発生時刻 {seedData.asOf}</p></div><StateBadge state="WARNING" compact /></div><p className="muted">影響: 新規Signalを保留。次操作: 再試行、停止、復旧照合。</p><div className="button-row"><button className="secondary-button" type="button" onClick={() => setWarningRows((current) => current.filter((item) => item !== id))}>対応済み</button><button className="secondary-button" type="button" onClick={() => setNotice(`${id}の再試行を受付しました。`)}>再試行</button><button className="danger-button" type="button" onClick={() => setDangerAction('stop')}>停止</button><button className="secondary-button" type="button" onClick={() => onNavigate('SCREEN-18')}>復旧照合</button></div></article>)}</div>{!warningRows.length && <EmptyState title="未対応の警告はありません" actionLabel="通常状態へ戻す" onAction={() => setWarningRows(['WARN-001'])} />}{notice && <p className="inline-notice" role="status">{notice}</p>}
  </>

  const renderGate = () => {
    const ready = riskValue.trim() !== ''
    return <>
      <StateAlert state="HUMAN-GATE">対象、設定版、Risk、影響、端末、時刻を運用者が確認してから移行します。</StateAlert><section className="sub-panel"><div className="section-heading"><div><p className="card-kicker">確認モード</p><h3>Live移行の承認方法</h3></div><StateBadge state={ready ? 'NORMAL' : 'REQUIRED'} compact /></div><div className="radio-row"><label><input type="radio" name="gate-mode" checked={gateMode === '確認と取消'} onChange={() => { setGateMode('確認と取消'); setAutoApproval(false) }} /> 確認と取消</label><label><input type="radio" name="gate-mode" checked={gateMode === 'スキップ（自動承認）'} onChange={() => { setGateMode('スキップ（自動承認）'); setAutoApproval(true) }} /> スキップ（自動承認）</label></div><div className="field-grid"><label className="field-label"><span>対象</span><input value="UNIT-001 / MCL / D1" readOnly /></label><label className="field-label"><span>設定版</span><input value="Turtle System 1 v1.1" readOnly /></label><label className="field-label"><span>Risk</span><input type="number" value={riskValue} onChange={(event) => setRiskValue(event.target.value)} placeholder="入力必須" /></label><label className="field-label"><span>端末・時刻</span><input value="自PC / 固定Seed時刻" readOnly /></label></div><p className="muted">現在のモード: {gateMode}。自動承認を選択しても、運用者のHuman Gate記録を残し、実注文送信は行いません。</p><div className="button-row"><button className="primary-button" type="button" disabled={!ready} onClick={() => setGateConfirm(true)}>移行を確認</button><button className="secondary-button" type="button" onClick={() => { setNotice('Human Gateを取消しました。'); onStateChange('UNAPPROVED') }}>取消</button></div></section>{notice && <p className="inline-notice" role="status">{notice}</p>}<ConfirmDialog open={gateConfirm} onOpenChange={setGateConfirm} title="Live移行を確認しますか？" description={`モード: ${gateMode}。対象・設定版・Riskを確認し、Human Gateの結果を操作記録へ残します。実注文は未接続です。`} confirmLabel="確認して記録" cancelLabel="取消" onConfirm={() => { setNotice(`Human Gate（${gateMode}）の確認結果を操作記録へ残しました。Live実行は未接続です。`); setGateConfirm(false); onStateChange('NORMAL') }} />
    </>
  }

  const renderAudit = () => {
    const rows = [{ id: 'AUDIT-001', action: 'Backtest開始', target: 'RUN-20260811-001' }, { id: 'AUDIT-002', action: 'Human Gate取消', target: 'UNIT-001' }, { id: 'AUDIT-003', action: '設定版保存', target: 'Turtle System 1 v1.2' }].filter((row) => !hiddenLogs.includes(row.id))
    return <><div className="filter-row"><label>対象<input placeholder="Run / Unit / Strategy" /></label><label>操作<select defaultValue="全て"><option>全て</option><option>開始</option><option>停止</option><option>削除</option></select></label><label>期間<input value={seedData.asOf} readOnly /></label></div><div className="table-scroll"><table className="data-table"><caption>Run、設定版、操作、Gate、削除の記録</caption><thead><tr><th>記録ID</th><th>時刻</th><th>操作</th><th>対象</th><th>端末</th><th>操作</th></tr></thead><tbody>{rows.map((row) => <tr key={row.id}><th>{row.id}</th><td>{seedData.asOf}</td><td>{row.action}</td><td>{row.target}</td><td>自PC</td><td><button className="secondary-button" type="button" onClick={() => setHiddenLogs((current) => [...current, row.id])}>通常一覧から隠す</button><button className="danger-button" type="button" onClick={() => setDangerAction('delete-log')}>削除</button></td></tr>)}</tbody></table></div><div className="button-row"><button className="secondary-button" type="button" onClick={() => setNotice('操作記録をCSV出力対象として受付しました。')}>出力</button><button className="secondary-button" type="button" onClick={() => setNotice('バックアップ状態: 内部保存済み（復元実証は未実施）。')}>バックアップ状態</button></div>{notice && <p className="inline-notice" role="status">{notice}</p>}<ConfirmDialog open={dangerAction === 'delete-log'} onOpenChange={(open) => !open && setDangerAction(null)} title="操作記録を削除しますか？" description="通常一覧から隠す操作と区別して確認します。実装時の監査要件は後続で確定します。" confirmLabel="削除する" cancelLabel="取消" danger onConfirm={() => { setNotice('操作記録の削除要求を記録しました。'); setDangerAction(null) }} /></>
  }

  const renderConnection = () => <><div className="two-column-grid"><section className="sub-panel"><div className="section-heading"><div><p className="card-kicker">接続先</p><h3>外部接続の状態</h3></div><StateBadge state="UNAPPROVED" compact /></div><dl className="definition-list"><div><dt>Broker</dt><dd>未設定・未承認</dd></div><div><dt>市場データ</dt><dd>固定ダミーのみ</dd></div><div><dt>Secret</dt><dd>存在のみ表示。値は非表示</dd></div><div><dt>保存場所</dt><dd>設定画面で確認する（値は表示しない）</dd></div></dl><button className="secondary-button" type="button" onClick={() => setNotice('接続確認を表示しました。未承認のため外部へ接続しません。')}>接続確認</button></section><section className="sub-panel"><div className="section-heading"><div><p className="card-kicker">通知</p><h3>通知設定</h3></div><StateBadge state="NORMAL" compact /></div><label className="switch-label"><input type="checkbox" defaultChecked /> 重要警告を画面に表示</label><label className="switch-label"><input type="checkbox" /> 音・外部通知（未接続）</label><p className="muted">通知先、Secret、外部送信は未設定です。</p></section></div>{notice && <p className="inline-notice" role="status">{notice}</p>}</>

  const renderHelp = () => <><section className="sub-panel"><div className="section-heading"><div><p className="card-kicker">用語</p><h3>画面を読むための説明</h3></div><StateBadge state="NORMAL" compact /></div><dl className="definition-list"><div><dt>運用単位</dt><dd>銘柄×時間足×売買ルールで分かれた独立インスタンスです。</dd></div><div><dt>網羅検証</dt><dd>各パラメータの下限・上限・ステップで全組合せを試すBacktestです。</dd></div><div><dt>Human Gate</dt><dd>運用者が対象・Risk・影響・証拠を確認する関門です。</dd></div><div><dt>Kill Switch</dt><dd>新規Signal・注文を止め、照合が終わるまで再開を止める安全操作です。</dd></div><div><dt>Paper / Live</dt><dd>Paperは模擬、Liveは実運用候補。未承認状態では開始できません。</dd></div></dl></section><div className="button-row"><button className="secondary-button" type="button" onClick={() => onNavigate('SCREEN-02')}>ホームへ戻る</button><button className="secondary-button" type="button" onClick={() => onNavigate('SCREEN-08')}>Backtest条件へ</button><button className="secondary-button" type="button" onClick={() => onNavigate('SCREEN-18')}>Human Gateへ</button></div></>

  const body = screen.id === 'SCREEN-01' ? renderSystem() : screen.id === 'SCREEN-05' ? renderData() : screen.id === 'SCREEN-13' ? renderForward() : screen.id === 'SCREEN-14' ? renderPaperLive() : screen.id === 'SCREEN-15' ? renderPortfolio() : screen.id === 'SCREEN-16' ? renderOrders() : screen.id === 'SCREEN-17' ? renderWarnings() : screen.id === 'SCREEN-18' ? renderGate() : screen.id === 'SCREEN-19' ? renderAudit() : screen.id === 'SCREEN-20' ? renderConnection() : renderHelp()

  return (
    <div className="screen-stack" data-testid={`screen-${screen.id}`} data-reason-id={p4ScreenContracts[screen.id].scope === 'P4_BOUNDARY_TARGET' ? p4ScreenContracts[screen.id].reasonId : undefined}>
      <section className="welcome-panel compact-panel"><div><p className="eyebrow">{screen.navId} / {screen.id} / {screen.e2eId}</p><h2>{screen.title}</h2><p className="lead">{screen.description}</p></div><StateBadge state={demoState} /></section>
      {body}
      <CoreStateControls demoState={demoState} onStateChange={onStateChange} />
      <ConfirmDialog open={dangerAction === 'stop'} onOpenChange={(open) => !open && setDangerAction(null)} title="安全停止を実行しますか？" description="新規Signal・注文を停止し、データ・注文・Positionの照合が終わるまで再開できません。" confirmLabel="停止する" cancelLabel="取消" danger onConfirm={() => { setNotice('安全停止を操作記録へ残しました。'); setDangerAction(null); onStateChange('STOPPED') }} />
    </div>
  )
}

function ScreenPlaceholder({ screen, demoState, onStateChange }: { screen: ScreenDefinition; demoState: UiState; onStateChange: (state: UiState) => void }) {
  const [progress, setProgress] = useState(48)
  const [error, setError] = useState(false)

  const body = () => {
    if (error || demoState === 'FAILED') return <ErrorState detail="固定ダミー処理の失敗状態です。実外部へは接続していません。" />
    if (demoState === 'LOADING') return <ProgressBar value={progress} label="固定ダミー処理の進捗" />
    if (demoState === 'EMPTY') return <EmptyState title="この条件のデータはありません" actionLabel="通常状態へ戻す" onAction={() => onStateChange('NORMAL')} />
    return <div className="placeholder-content"><MetricCard label="対象画面" value={screen.id} detail={screen.e2eId} /><MetricCard label="固定データ" value="未接続" detail="実Broker・実注文なし" /><p>{screen.description}</p><HelpTip title="操作の意味">このcandidateは画面遷移と状態を確認するモックです。後続Gateの実値はここで確定しません。</HelpTip></div>
  }

  return (
    <div className="screen-stack" data-testid={`screen-${screen.id}`}>
      <section className="welcome-panel compact-panel"><div><p className="eyebrow">{screen.navId} / {screen.id} / {screen.e2eId}</p><h2>{screen.title}</h2><p className="lead">{screen.description}</p></div><StateBadge state={demoState} /></section>
      <StateAlert state={demoState}>{stateLabels(demoState)}。理由、影響、次の操作を文字で確認できます。</StateAlert>
      <section className="panel-card"><div className="section-heading"><div><p className="card-kicker">共通状態デモ</p><h3>状態を切り替えて確認</h3></div><button className="secondary-button" type="button" onClick={() => setError(false)}>エラー表示を解除</button></div><div className="state-switcher">{(['NORMAL','LOADING','EMPTY','REQUIRED','WARNING','STOPPED','FAILED','RECOVERY','HUMAN-GATE','UNAPPROVED'] as UiState[]).map((state) => <button className={demoState === state ? 'state-choice active' : 'state-choice'} type="button" key={state} onClick={() => { setError(state === 'FAILED'); onStateChange(state) }}>{state}</button>)}</div>{demoState === 'LOADING' && <div className="button-row"><button className="secondary-button" type="button" onClick={() => setProgress((value) => Math.min(100, value + 12))}>進捗を進める</button></div>}</section>
      <section className="panel-card"><div className="section-heading"><div><p className="card-kicker">画面内容</p><h3>{screen.title}の共通骨格</h3></div><StateBadge state={demoState} compact /></div>{body()}</section>
    </div>
  )
}

const stateLabels = (state: UiState) => ({
  NORMAL: '通常状態', LOADING: '読込中', EMPTY: 'データなし', REQUIRED: '入力が必要', WARNING: '警告状態', STOPPED: '停止状態', FAILED: '失敗状態', RECOVERY: '復旧確認中', 'HUMAN-GATE': '運用者確認待ち', UNAPPROVED: '未承認状態',
}[state])

function App() {
  const [activeScreenId, setActiveScreenId] = useState<ScreenDefinition['id']>('SCREEN-02')
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [killOpen, setKillOpen] = useState(false)
  const [killed, setKilled] = useState(false)
  const [demoState, setDemoState] = useState<UiState>('NORMAL')
  const activeScreen = useMemo(() => allScreens.find((item) => item.id === activeScreenId) ?? allScreens[0], [activeScreenId])

  useEffect(() => {
    document.querySelectorAll<HTMLElement>('.table-scroll').forEach((element) => {
      element.tabIndex = 0
      element.setAttribute('aria-label', '横スクロール可能な表')
    })
  }, [activeScreenId])

  const navigate = (screenId: ScreenDefinition['id']) => {
    setActiveScreenId(screenId)
    setDemoState(allScreens.find((item) => item.id === screenId)?.defaultState ?? 'NORMAL')
    setMobileNavOpen(false)
  }

  return (
    <div className="app-shell" data-testid="pilot-screen">
      <aside className={mobileNavOpen ? 'app-sidebar mobile-open' : 'app-sidebar'} aria-label="メインナビゲーション">
        <div className="brand-block"><span className="brand-mark" aria-hidden="true">AT</span><div><strong>AutoTrade</strong><span>UI Mock candidate</span></div></div>
        <div className="sidebar-note"><StateBadge state={killed ? 'STOPPED' : 'UNAPPROVED'} compact /><span>{killed ? '全体停止中' : '実外部未接続'}</span></div>
        <nav className="nav-groups">{navGroups.map((group) => <section className="nav-group" key={group.id}><p className="nav-group-label">{group.id} / {group.label}</p>{group.screens.map((screen) => <button className={screen.id === activeScreen.id ? 'nav-item active' : 'nav-item'} type="button" key={screen.id} onClick={() => navigate(screen.id)} data-testid={`nav-${screen.id}`}><span>{screen.title}</span><small>{screen.id.replace('SCREEN-', '#')}</small></button>)}</section>)}</nav>
        <footer className="sidebar-footer"><span>固定Seed {seedData.seed}</span><span>外部通信 なし</span><span>実注文 なし</span></footer>
      </aside>
      {mobileNavOpen && <button className="mobile-scrim" type="button" aria-label="メニューを閉じる" onClick={() => setMobileNavOpen(false)} />}

      <div className="app-main">
        <header className="topbar"><button className="menu-button" type="button" aria-label="メニューを開く" aria-expanded={mobileNavOpen} onClick={() => setMobileNavOpen(true)}>☰</button><div className="breadcrumb"><span>運用者</span><span aria-hidden="true">/</span><strong>{activeScreen.title}</strong></div><div className="topbar-actions"><StateBadge state={killed ? 'STOPPED' : 'UNAPPROVED'} compact /><span className="as-of">基準日時: {seedData.asOf}</span></div></header>
        <main className="app-content">
          <div className="content-heading"><div><p className="eyebrow">RQU-UI-07 / 固定Seed 20260811 / SCREEN-ID追跡</p><h1>{activeScreen.title}</h1></div><div className="content-heading-actions"><span className="small-label">モック状態</span><StateBadge state={killed ? 'STOPPED' : demoState} compact /></div></div>
          <P4ContractStrip screenId={activeScreen.id} contract={p4ScreenContracts[activeScreen.id]} />
          {killed && <StateAlert state="STOPPED" title="全体Kill Switchが有効です">新規Signal・注文は停止しています。データ・注文・Positionの照合が終わるまで再開できません。</StateAlert>}
          {activeScreen.id === 'SCREEN-02' ? <HomeScreen onKill={() => setKillOpen(true)} demoState={demoState} onStateChange={setDemoState} /> : activeScreen.id === 'SCREEN-08' ? <P5RBacktestScreen screen={activeScreen} demoState={demoState} onStateChange={setDemoState} /> : coreScreenIds.includes(activeScreen.id) ? <CoreScreen screen={activeScreen} demoState={demoState} onStateChange={setDemoState} onNavigate={navigate} /> : p4BoundaryScreenIds.includes(activeScreen.id) || boundaryOnlyScreenIds.includes(activeScreen.id) ? <P4BoundaryScreen screen={activeScreen} contract={p4ScreenContracts[activeScreen.id]} demoState={demoState} onStateChange={setDemoState} /> : safetyScreenIds.includes(activeScreen.id) ? <SafetyScreen screen={activeScreen} demoState={demoState} onStateChange={setDemoState} onNavigate={navigate} /> : <ScreenPlaceholder screen={activeScreen} demoState={demoState} onStateChange={setDemoState} />}
        </main>
      </div>
      <ConfirmDialog open={killOpen} onOpenChange={setKillOpen} title="全体Kill Switchを実行しますか？" description="全運用単位の新規Signal・注文を停止します。解除には照合と運用者の確認が必要です。" confirmLabel="停止する" cancelLabel="取消" danger onConfirm={() => { setKilled(true); setKillOpen(false); setDemoState('STOPPED') }} />
    </div>
  )
}

export default App
