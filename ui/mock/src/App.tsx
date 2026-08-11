import { useMemo, useState } from 'react'
import { Button as BaseButton, Dialog as BaseDialog } from '@base-ui/react'
import * as RadixDialog from '@radix-ui/react-dialog'
import { faker } from '@faker-js/faker'
import './App.css'

type Quote = {
  symbol: string
  timeframe: string
  price: number
  change: number
}

function createQuote(): Quote {
  faker.seed(20260811)
  return {
    symbol: 'MCL',
    timeframe: 'D1',
    price: Number(faker.finance.amount({ min: 65, max: 85, dec: 2 })),
    change: Number(faker.finance.amount({ min: -2, max: 2, dec: 2 })),
  }
}

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
          <BaseDialog.Description>
            キーボードで閉じるボタンへ移動できるかを確認します。
          </BaseDialog.Description>
          <BaseDialog.Close render={<button className="secondary-button" />}>
            閉じる
          </BaseDialog.Close>
        </BaseDialog.Popup>
      </BaseDialog.Portal>
    </BaseDialog.Root>
  )
}

function RadixDialogPilot() {
  return (
    <RadixDialog.Root>
      <RadixDialog.Trigger asChild>
        <button className="secondary-button" type="button">
          Radix Dialogを開く
        </button>
      </RadixDialog.Trigger>
      <RadixDialog.Portal>
        <RadixDialog.Overlay className="dialog-backdrop" />
        <RadixDialog.Content className="dialog-popup" aria-describedby="radix-description">
          <RadixDialog.Title>Radixの確認</RadixDialog.Title>
          <RadixDialog.Description id="radix-description">
            Escキー、フォーカス移動、閉じる操作を確認します。
          </RadixDialog.Description>
          <RadixDialog.Close asChild>
            <button className="secondary-button" type="button">
              閉じる
            </button>
          </RadixDialog.Close>
        </RadixDialog.Content>
      </RadixDialog.Portal>
    </RadixDialog.Root>
  )
}

function App() {
  const quote = useMemo(createQuote, [])
  const [submitted, setSubmitted] = useState(false)

  return (
    <main className="pilot-shell" data-testid="pilot-screen">
      <header className="pilot-header">
        <div>
          <p className="eyebrow">RQU-UI-03 / UI component pilot</p>
          <h1>自動トレードUI基盤 Smoke</h1>
          <p className="lead">
            固定Seedの匿名データで、Base UIとRadixのDialog、Form、Table、Buttonを比較します。
          </p>
        </div>
        <span className="status-chip" role="status">未接続・モック</span>
      </header>

      <section className="pilot-grid" aria-label="UI部品パイロット">
        <article className="pilot-card">
          <div className="card-heading">
            <div>
              <p className="card-kicker">固定Seedデータ</p>
              <h2>市場データの表示</h2>
            </div>
            <span className="state-badge">NORMAL</span>
          </div>
          <table className="quote-table">
            <caption>匿名の固定データによる相場表示</caption>
            <thead>
              <tr>
                <th scope="col">銘柄</th>
                <th scope="col">時間足</th>
                <th scope="col">価格</th>
                <th scope="col">変化</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th scope="row">{quote.symbol}</th>
                <td>{quote.timeframe}</td>
                <td>{quote.price.toFixed(2)}</td>
                <td className={quote.change >= 0 ? 'positive' : 'negative'}>
                  {quote.change >= 0 ? '+' : ''}{quote.change.toFixed(2)}%
                </td>
              </tr>
            </tbody>
          </table>
        </article>

        <article className="pilot-card">
          <div className="card-heading">
            <div>
              <p className="card-kicker">Base UI / Radix</p>
              <h2>Dialog・Focus確認</h2>
            </div>
            <span className="state-badge">PILOT</span>
          </div>
          <p className="muted">同じ操作を2つの基礎部品で比較します。</p>
          <div className="button-row">
            <BaseDialogPilot />
            <RadixDialogPilot />
          </div>
        </article>

        <article className="pilot-card">
          <div className="card-heading">
            <div>
              <p className="card-kicker">Form</p>
              <h2>運用単位の入力</h2>
            </div>
            <span className="state-badge">REQUIRED</span>
          </div>
          <form
            className="pilot-form"
            onSubmit={(event) => {
              event.preventDefault()
              setSubmitted(true)
            }}
          >
            <label htmlFor="symbol">銘柄</label>
            <input id="symbol" name="symbol" defaultValue="MCL" required />
            <label htmlFor="timeframe">時間足</label>
            <select id="timeframe" name="timeframe" defaultValue="D1">
              <option>D1</option>
              <option>H4</option>
              <option>H1</option>
              <option>M30</option>
              <option>M15</option>
            </select>
            <button className="primary-button" type="submit">確認する</button>
            {submitted && <p className="success-message" role="status">入力内容を確認しました。</p>}
          </form>
        </article>
      </section>

      <footer className="pilot-footer">
        <span>固定Seed: 20260811</span>
        <span>外部通信: なし</span>
        <span>実注文: なし</span>
      </footer>
    </main>
  )
}

export default App
