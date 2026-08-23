import type { ChangeEvent } from 'react'
import { dateTimeLocalToUtcIso, utcIsoToDateTimeLocal } from './utcDateTime'

export type UtcDateTimePickerProps = {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  error?: string
  description?: string
  min?: string
  max?: string
  required?: boolean
  disabled?: boolean
}

function toLocalValue(value: string | undefined) {
  if (!value) return undefined
  try {
    return utcIsoToDateTimeLocal(value)
  } catch {
    return undefined
  }
}

export function UtcDateTimePicker({
  id,
  label,
  value,
  onChange,
  error,
  description,
  min,
  max,
  required = false,
  disabled = false,
}: UtcDateTimePickerProps) {
  const descriptionId = `${id}-description`
  const errorId = `${id}-error`
  const describedBy = [description ? descriptionId : '', error ? errorId : ''].filter(Boolean).join(' ') || undefined

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    try {
      onChange(dateTimeLocalToUtcIso(event.target.value))
    } catch {
      onChange('')
    }
  }

  return (
    <div className="field-label">
      <label htmlFor={id}><span>{label}</span></label>
      <input
        id={id}
        type="datetime-local"
        step="60"
        value={toLocalValue(value) ?? ''}
        min={toLocalValue(min)}
        max={toLocalValue(max)}
        required={required}
        disabled={disabled}
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={describedBy}
        onChange={handleChange}
      />
      {description && <span id={descriptionId} className="muted">{description}</span>}
      {error && <span id={errorId} className="inline-notice error-notice" role="alert">{error}</span>}
    </div>
  )
}
