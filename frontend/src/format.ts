export const formatValue = (
  value: number | null | undefined,
  compact = false,
  precise = false,
) =>
  value == null
    ? '—'
    : new Intl.NumberFormat('en-US', {
        ...(compact
          ? { notation: 'compact', maximumFractionDigits: 2 }
          : precise
            ? { maximumSignificantDigits: 21 }
            : value !== 0 && Math.abs(value) < 0.001
              ? { notation: 'scientific', maximumFractionDigits: 3 }
              : { maximumFractionDigits: 3 }),
      }).format(value);
