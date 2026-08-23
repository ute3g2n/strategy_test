type DateTimeLocalParts = {
  year: number
  month: number
  day: number
  hour: number
  minute: number
}

const DATE_TIME_LOCAL_PATTERN = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/
const UTC_ISO_PATTERN = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z$/

function daysInMonth(year: number, month: number) {
  if (month === 2) {
    const leapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0)
    return leapYear ? 29 : 28
  }
  return [4, 6, 9, 11].includes(month) ? 30 : 31
}

function parseDateTimeLocal(value: string): DateTimeLocalParts | null {
  const match = DATE_TIME_LOCAL_PATTERN.exec(value)
  if (!match) return null
  const [, yearText, monthText, dayText, hourText, minuteText] = match
  const year = Number(yearText)
  const month = Number(monthText)
  const day = Number(dayText)
  const hour = Number(hourText)
  const minute = Number(minuteText)
  if (month < 1 || month > 12 || day < 1 || day > daysInMonth(year, month)) return null
  if (hour < 0 || hour > 23 || minute < 0 || minute > 59) return null
  return { year, month, day, hour, minute }
}

function toComparableMinutes(parts: DateTimeLocalParts) {
  const daysBeforeMonth = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
  const leapDays = parts.month > 2 && (parts.year % 4 === 0 && (parts.year % 100 !== 0 || parts.year % 400 === 0)) ? 1 : 0
  return (((parts.year * 365) + Math.floor(parts.year / 4) - Math.floor(parts.year / 100) + Math.floor(parts.year / 400) + daysBeforeMonth[parts.month - 1] + leapDays + parts.day) * 24 * 60) + (parts.hour * 60) + parts.minute
}

export function isValidDateTimeLocal(value: string) {
  return parseDateTimeLocal(value) !== null
}

export function dateTimeLocalToUtcIso(value: string) {
  if (value === '') return ''
  if (!isValidDateTimeLocal(value)) throw new Error('日時が不正です。')
  return `${value}:00Z`
}

export function utcIsoToDateTimeLocal(value: string) {
  if (value === '') return ''
  const match = UTC_ISO_PATTERN.exec(value)
  if (!match) throw new Error('UTC日時の形式が不正です。')
  const [, year, month, day, hour, minute, second] = match
  const localValue = `${year}-${month}-${day}T${hour}:${minute}`
  if (second !== '00') throw new Error('UTC日時の秒は00にしてください。')
  if (!isValidDateTimeLocal(localValue)) throw new Error('UTC日時が不正です。')
  return localValue
}

export type UtcRangeValidation =
  | { valid: true }
  | { valid: false; message: string }

export function validateUtcRange(start: string, end: string): UtcRangeValidation {
  if (!start) return { valid: false, message: '開始日時（UTC）を入力してください。' }
  if (!end) return { valid: false, message: '終了日時（UTC）を入力してください。' }

  try {
    const startLocal = utcIsoToDateTimeLocal(start)
    const endLocal = utcIsoToDateTimeLocal(end)
    const startParts = parseDateTimeLocal(startLocal)
    const endParts = parseDateTimeLocal(endLocal)
    if (!startParts || !endParts || toComparableMinutes(startParts) >= toComparableMinutes(endParts)) {
      return { valid: false, message: '開始日時は終了日時より前にしてください。' }
    }
  } catch {
    return { valid: false, message: '開始・終了日時を正しいUTC形式で指定してください。' }
  }
  return { valid: true }
}
