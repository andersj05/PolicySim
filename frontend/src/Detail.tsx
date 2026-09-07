import { useState } from 'react';
import type { SeriesPick } from './App';
import type { Snapshot } from './api.generated';
import { download, useRemote } from './api';
import Chart from './Chart';
import { formatValue } from './format';
import { Icon, Message } from './components';

export default function Detail({
  selected,
  country,
  countryName,
}: {
  selected: SeriesPick;
  country: string;
  countryName: string;
}) {
  const [refresh, setRefresh] = useState(0);
  const [tab, setTab] = useState<'chart' | 'table'>('chart');
  const [range, setRange] = useState('10Y');
  const [dates, setDates] = useState({
    start: '1776-07-04',
    end: new Date().toISOString().slice(0, 10),
  });
  const [draft, setDraft] = useState(dates);
  const [tablePage, setTablePage] = useState(0);
  const params = new URLSearchParams({
    provider: selected.provider,
    series_id: selected.id,
    country,
    source_id: selected.source_id || '2',
    ...dates,
  });
  const { data, error, loading } = useRemote<Snapshot>(
    `/api/v1/observations?${params}`,
    refresh,
  );
  const latest = data
    ? [...data.observations].reverse().find((row) => row.value !== null)
    : undefined;
  const lastYear = Number(data?.observations.at(-1)?.date.slice(0, 4));
  const visible =
    data?.observations.filter(
      (row) =>
        range === 'MAX' ||
        Number(row.date.slice(0, 4)) >= lastYear - Number.parseInt(range) + 1,
    ) ?? [];
  const rows = [...visible].reverse();
  const missing = visible.filter((row) => row.value === null).length;
  return (
    <article className="detail" aria-busy={loading}>
      <div className="detail-top">
        <span className={`source-label ${selected.provider}`}>
          <span />
          {selected.provider === 'fred' ? 'FRED' : 'World Bank'}
        </span>
        <span className="mono">{selected.id}</span>
      </div>
      <h2>{data?.series.title ?? selected.title}</h2>
      <p className="series-context">
        {selected.provider === 'worldbank'
          ? countryName
          : 'Economic time series'}
        {data ? ` · ${data.series.frequency}` : ''}
      </p>
      {loading && (
        <div className="loading-detail" role="status">
          <div className="skeleton number-skeleton" />
          <div className="skeleton chart-skeleton" />
          <p>Retrieving observations and preserving their source…</p>
        </div>
      )}
      {error && (
        <Message error={error} retry={() => setRefresh((v) => v + 1)} />
      )}
      {data && (
        <>
          <div className="metric-row">
            <div>
              <div className="metric" title={formatValue(latest?.value)}>
                {formatValue(
                  latest?.value,
                  Math.abs(latest?.value ?? 0) >= 1e9,
                )}
              </div>
              <div className="metric-caption">{data.series.units}</div>
            </div>
            <div className="latest-label">
              <span>Latest available</span>
              <strong>{latest?.date ?? 'No numeric data'}</strong>
            </div>
          </div>
          <div className="chart-toolbar">
            <div className="view-switch" aria-label="Data view">
              <button
                aria-pressed={tab === 'chart'}
                onClick={() => setTab('chart')}
              >
                <Icon name="chart" size={15} />
                Chart
              </button>
              <button
                aria-pressed={tab === 'table'}
                onClick={() => setTab('table')}
              >
                <Icon name="table" size={15} />
                Table
              </button>
            </div>
            <div className="ranges" aria-label="Visible time range">
              {['5Y', '10Y', '25Y', 'MAX'].map((value) => (
                <button
                  key={value}
                  aria-pressed={range === value}
                  onClick={() => {
                    setRange(value);
                    setTablePage(0);
                  }}
                >
                  {value}
                </button>
              ))}
            </div>
          </div>
          {tab === 'chart' ? (
            <Chart
              key={range}
              observations={visible}
              title={data.series.title}
            />
          ) : (
            <div className="table-region">
              <table>
                <caption className="sr-only">
                  {data.series.title} — original observations
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Observation date</th>
                    <th scope="col">Value</th>
                  </tr>
                </thead>
                <tbody>
                  {rows
                    .slice(tablePage * 10, (tablePage + 1) * 10)
                    .map((row) => (
                      <tr key={row.date}>
                        <td>{row.date}</td>
                        <td>
                          {row.value === null
                            ? 'Missing'
                            : formatValue(row.value)}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
              {!rows.length && (
                <p className="small">No observations in this range.</p>
              )}
              <div className="pagination">
                <button
                  disabled={!tablePage}
                  onClick={() => setTablePage((v) => v - 1)}
                >
                  Previous
                </button>
                <span>
                  {rows.length ? tablePage + 1 : 0} /{' '}
                  {Math.ceil(rows.length / 10)}
                </span>
                <button
                  disabled={(tablePage + 1) * 10 >= rows.length}
                  onClick={() => setTablePage((v) => v + 1)}
                >
                  Next
                </button>
              </div>
            </div>
          )}
          <div className="chart-footnote">
            <span>
              <span className="legend-line" />
              Original observations
            </span>
            <span>
              {visible.length.toLocaleString()} points
              {missing ? ` · ${missing} missing` : ''}
            </span>
          </div>
          <div className="provenance">
            <div>
              <Icon name="book" size={17} />
              <strong>Know your data</strong>
              <span className="badge">Latest revision</span>
            </div>
            <dl>
              <div>
                <dt>Source</dt>
                <dd>
                  <a
                    href={data.series.source_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {data.series.source_name} ↗
                  </a>
                </dd>
              </div>
              <div>
                <dt>Adjustment</dt>
                <dd>{data.series.seasonal_adjustment}</dd>
              </div>
              <div>
                <dt>Retrieved</dt>
                <dd>{new Date(data.retrieved_at).toLocaleString()}</dd>
              </div>
              <div>
                <dt>Transformations</dt>
                <dd>None · Original provider values</dd>
              </div>
            </dl>
            <details>
              <summary>Source notes & snapshot details</summary>
              <p className="source-notes">
                {data.series.notes ||
                  'No additional notes supplied by the provider.'}
              </p>
              <p>{data.vintage}</p>
              <p className="small">
                Observation dates are provider periods, not publication dates.
                World Bank date filters use calendar years.
              </p>
              <p className="small">
                Updated: {data.series.updated || 'Not reported'}
              </p>
              <p className="small hash">Snapshot: {data.snapshot_id}</p>
              <a
                href={data.series.license_url}
                target="_blank"
                rel="noreferrer"
              >
                Provider terms & usage rights ↗
              </a>
            </details>
          </div>
          <div className="detail-actions">
            <span className="small">Source snapshot saved locally</span>
            <button
              className="secondary"
              onClick={() =>
                download(
                  `${selected.provider}-${selected.id}-${country || 'series'}.json`,
                  JSON.stringify(data, null, 2),
                )
              }
            >
              <Icon name="download" size={16} />
              Download data
            </button>
          </div>
        </>
      )}
      <details className="date-settings">
        <summary>Adjust retrieval dates</summary>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            setDates(draft);
            setTablePage(0);
          }}
        >
          <label>
            From
            <input
              type="date"
              required
              value={draft.start}
              max={draft.end}
              onChange={(event) =>
                setDraft({ ...draft, start: event.target.value })
              }
            />
          </label>
          <label>
            To
            <input
              type="date"
              required
              value={draft.end}
              min={draft.start}
              onChange={(event) =>
                setDraft({ ...draft, end: event.target.value })
              }
            />
          </label>
          <button className="secondary" type="submit">
            Load dates
          </button>
        </form>
      </details>
    </article>
  );
}
