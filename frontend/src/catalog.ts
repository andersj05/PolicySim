import type { Series } from './api.generated';

export type Provider = 'fred' | 'worldbank';
export const modelNames = {
  naive: 'Naive',
  drift: 'Drift',
  seasonal_naive: 'Seasonal naive',
  ets: 'Exponential smoothing',
  sarima: 'ARIMA / SARIMA',
};
export type SeriesPick = Pick<
  Series,
  'provider' | 'id' | 'title' | 'source_id'
> & {
  snapshot_id?: string;
  country?: string;
};
export const names = { fred: 'FRED', worldbank: 'World Bank', local: 'CSV' };
export const starters: Record<Provider, SeriesPick[]> = {
  fred: [
    ['UNRATE', 'Unemployment Rate'],
    ['GDP', 'Gross Domestic Product'],
    ['CPIAUCSL', 'Consumer Price Index'],
    ['FEDFUNDS', 'Federal Funds Rate'],
    ['DGS10', '10-Year Treasury Yield'],
  ].map(([id, title]) => ({
    provider: 'fred',
    id: id!,
    title: title!,
    source_id: '',
  })),
  worldbank: [
    ['NY.GDP.MKTP.CD', 'GDP (current US$)'],
    ['SP.POP.TOTL', 'Population, total'],
    ['FP.CPI.TOTL.ZG', 'Consumer price inflation'],
    ['SL.UEM.TOTL.ZS', 'Unemployment'],
    ['SP.DYN.LE00.IN', 'Life expectancy at birth'],
  ].map(([id, title]) => ({
    provider: 'worldbank',
    id: id!,
    title: title!,
    source_id: '2',
  })),
};

export const pickKey = (item: SeriesPick) =>
  `${item.provider}-${item.source_id}-${item.id}-${item.country ?? ''}-${item.snapshot_id ?? ''}`;

export function readLibrary(): SeriesPick[] {
  try {
    const value: unknown = JSON.parse(
      localStorage.getItem('policysim.library.v1') ?? '[]',
    );
    return Array.isArray(value)
      ? value
          .filter((item: unknown): item is SeriesPick => {
            if (!item || typeof item !== 'object') return false;
            const row = item as Partial<SeriesPick>;
            return (
              (row.provider === 'fred' ||
                row.provider === 'worldbank' ||
                row.provider === 'local') &&
              typeof row.id === 'string' &&
              typeof row.title === 'string' &&
              typeof row.source_id === 'string' &&
              typeof row.snapshot_id === 'string' &&
              /^[a-f0-9]{64}$/.test(row.snapshot_id) &&
              (row.country === undefined || typeof row.country === 'string')
            );
          })
          .slice(0, 30)
      : [];
  } catch {
    return [];
  }
}
