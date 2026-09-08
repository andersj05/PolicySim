import type { Series } from './api.generated';

export type Provider = 'fred' | 'worldbank' | 'bls' | 'ecb';
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
export const names = {
  fred: 'FRED',
  worldbank: 'World Bank',
  bls: 'BLS',
  ecb: 'ECB',
  local: 'CSV',
};
export const sourceDescriptions: Record<Provider, string> = {
  fred: 'US & global economic series · full catalog search',
  worldbank: 'Global development · countries & aggregates',
  bls: '10 supported US labor & price series · 10 calendar years',
  ecb: 'Monthly reference FX · search currency or exact EXR.M key',
};
export const starters: Record<Provider, SeriesPick[]> = {
  bls: [
    ['LNS14000000', 'Unemployment rate'],
    ['CES0000000001', 'Total nonfarm payrolls'],
    ['CUSR0000SA0', 'Consumer price index'],
    ['CUSR0000SA0L1E', 'Core consumer prices'],
    ['CES0500000003', 'Average hourly earnings'],
  ].map(([id, title]) => ({
    provider: 'bls',
    id: id!,
    title: title!,
    source_id: '',
  })),
  ecb: [
    ['USD', 'US dollar / euro'],
    ['GBP', 'Pound sterling / euro'],
    ['JPY', 'Japanese yen / euro'],
    ['CHF', 'Swiss franc / euro'],
    ['CAD', 'Canadian dollar / euro'],
  ].map(([code, title]) => ({
    provider: 'ecb',
    id: `EXR.M.${code}.EUR.SP00.A`,
    title: title!,
    source_id: '',
  })),
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
                row.provider === 'bls' ||
                row.provider === 'ecb' ||
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
