export const formatValue = (
  value: number | null | undefined,
  compact = false,
) =>
  value == null
    ? '—'
    : new Intl.NumberFormat('en-US', {
        ...(compact
          ? { notation: 'compact', maximumFractionDigits: 3 }
          : { maximumSignificantDigits: 21 }),
      }).format(value);
