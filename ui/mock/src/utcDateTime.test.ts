import { describe, expect, it } from 'vitest'
import {
  dateTimeLocalToUtcIso,
  isValidDateTimeLocal,
  utcIsoToDateTimeLocal,
  validateUtcRange,
} from './utcDateTime'

describe('UTC日時変換', () => {
  it('ISO UTCをdatetime-local表示値へ変換する', () => {
    expect(utcIsoToDateTimeLocal('2025-02-24T00:00:00Z')).toBe('2025-02-24T00:00')
  })

  it('datetime-local値をUTC ISO文字列へ変換する', () => {
    expect(dateTimeLocalToUtcIso('2025-02-24T02:30')).toBe('2025-02-24T02:30:00Z')
  })

  it('ブラウザのローカルタイムゾーンを使わずに日付境界を保持する', () => {
    expect(dateTimeLocalToUtcIso('2026-01-01T00:00')).toBe('2026-01-01T00:00:00Z')
    expect(utcIsoToDateTimeLocal('2025-12-31T23:59:00Z')).toBe('2025-12-31T23:59')
  })

  it('うるう日を有効な日時として扱う', () => {
    expect(isValidDateTimeLocal('2024-02-29T12:00')).toBe(true)
    expect(isValidDateTimeLocal('2025-02-29T12:00')).toBe(false)
  })

  it('存在しない日付と不正な日時を拒否する', () => {
    expect(isValidDateTimeLocal('2025-02-30T12:00')).toBe(false)
    expect(() => dateTimeLocalToUtcIso('2025-02-30T12:00')).toThrow('日時が不正です')
    expect(() => utcIsoToDateTimeLocal('2025-02-24T00:00:01Z')).toThrow('秒')
  })

  it('空欄を許容し、範囲検証では未入力として扱う', () => {
    expect(dateTimeLocalToUtcIso('')).toBe('')
    expect(validateUtcRange('', '2025-02-24T01:00:00Z')).toEqual({
      valid: false,
      message: '開始日時（UTC）を入力してください。',
    })
  })

  it('開始が終了以上の範囲を拒否する', () => {
    expect(validateUtcRange('2025-02-24T02:00:00Z', '2025-02-24T01:00:00Z')).toEqual({
      valid: false,
      message: '開始日時は終了日時より前にしてください。',
    })
    expect(validateUtcRange('2025-02-24T01:00:00Z', '2025-02-24T01:00:00Z')).toEqual({
      valid: false,
      message: '開始日時は終了日時より前にしてください。',
    })
  })
})
