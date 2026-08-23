import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { UtcDateTimePicker } from './UtcDateTimePicker'

describe('UtcDateTimePicker', () => {
  it('カレンダーと時刻を選べる標準日時入力としてUTC値を返す', () => {
    const onChange = vi.fn()
    render(
      <UtcDateTimePicker
        id="start"
        label="開始日時（UTC）"
        value="2025-02-24T00:00:00Z"
        onChange={onChange}
      />,
    )

    const input = screen.getByLabelText('開始日時（UTC）')
    expect(input).toHaveAttribute('type', 'datetime-local')
    expect(input).toHaveAttribute('step', '60')
    expect(input).toHaveValue('2025-02-24T00:00')

    fireEvent.change(input, { target: { value: '2025-02-24T02:30' } })
    expect(onChange).toHaveBeenLastCalledWith('2025-02-24T02:30:00Z')
  })

  it('エラーを入力欄へ関連付ける', () => {
    render(
      <UtcDateTimePicker
        id="end"
        label="終了日時（UTC）"
        value=""
        onChange={() => undefined}
        error="終了日時（UTC）を入力してください。"
      />,
    )

    const input = screen.getByLabelText('終了日時（UTC）')
    expect(input).toHaveAttribute('aria-invalid', 'true')
    expect(input).toHaveAttribute('aria-describedby', 'end-error')
    expect(screen.getByRole('alert')).toHaveTextContent('終了日時（UTC）を入力してください。')
  })
})
