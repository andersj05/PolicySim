import { useState } from 'react';
import type { SeriesPick } from './catalog';
import { names } from './catalog';
import type { Snapshot } from './api.generated';
import { useRemote } from './api';
import AnalysisView from './AnalysisView';
import Forecast from './Forecast';
import { formatValue } from './format';
import { Icon, Message } from './components';

export default function Detail({
  selected,
  country,
  countryName,
  save,
  library,
}: {
  selected: SeriesPick;
  country: string;
  countryName: string;
  save: (data: Snapshot) => void;
  library: SeriesPick[];
}) {
  const [refresh, setRefresh] = useState(0);
  const [tab, setTab] = useState<'data' | 'statistics' | 'forecast'>('data');
  const [range, setRange] = useState(
    selected.provider === 'fred' ? '10Y' : 'MAX',
  );
  const [custom, setCustom] = useState({ start: '', end: '' });
  const [draft, setDraft] = useState(custom);
  const params = new URLSearchParams({
    provider: selected.provider,
    series_id: selected.id,
    country,
    source_id: selected.source_id || '2',
  });
  const url = selected.snapshot_id
    ? `/api/v1/snapshots/${selected.snapshot_id}`
    : `/api/v1/observations?${params}`;
  const { data, error, loading } = useRemote<Snapshot>(url, refresh);
  const latest = data
    ? [...data.observations].reverse().find((row) => row.value !== null)
    : undefined;
  const lastYear = Number(data?.observations.at(-1)?.date.slice(0, 4));
  const start =
    range === 'Custom'
      ? custom.start
      : range === 'MAX' || !lastYear
        ? ''
        : `${lastYear - Number.parseInt(range) + 1}-01-01`;
  const end = range === 'Custom' ? custom.end : '';
  const saved =
    data && library.some((entry) => entry.snapshot_id === data.snapshot_id);
  return (
    <article className="detail" aria-busy={loading}>
      <div className="detail-top">
        <span className={`source-label ${selected.provider}`}>
          <span />
          {names[selected.provider]}
        </span>
        <span className="mono">{selected.id}</span>
        {data && (
          <button
            className={`text-button save-button ${saved ? 'is-saved' : ''}`}
            onClick={() => save(data)}
            disabled={saved}
          >
            <Icon name="save" size={15} />
            {saved ? 'Saved' : 'Save series'}
          </button>
        )}
      </div>
      <h2>{data?.series.title ?? selected.title}</h2>
      <p className="series-context">
        {selected.provider === 'worldbank' ? `${countryName} · ` : ''}
        {data?.series.frequency}
        {data ? ` · ${data.series.seasonal_adjustment}` : ''}
      </p>
      {loading && (
        <div className="loading-detail" role="status">
          <div className="skeleton number-skeleton" />
          <div className="skeleton chart-skeleton" />
          <p>Loading observations…</p>
        </div>
      )}
      {error && (
        <Message error={error} retry={() => setRefresh((v) => v + 1)} />
      )}
      {data && (
        <>
          <div className="metric-row">
            <div>
              <div className="metric" title={String(latest?.value)}>
                {formatValue(
                  latest?.value,
                  Math.abs(latest?.value ?? 0) >= 1e9,
                )}
              </div>
              <span className="metric-caption">{data.series.units}</span>
            </div>
            <div className="latest-label">
              <span>Latest available</span>
              <strong>{latest?.date ?? 'No numeric data'}</strong>
            </div>
          </div>
          <div className="detail-tabs" aria-label="Series workspace">
            {(['data', 'statistics', 'forecast'] as const).map((value) => (
              <button
                key={value}
                aria-pressed={tab === value}
                onClick={() => setTab(value)}
              >
                {value === 'data'
                  ? 'Data'
                  : value === 'statistics'
                    ? 'Statistics'
                    : 'Forecast'}
              </button>
            ))}
            <span className="tab-spacer" />
            <a
              className="text-button"
              href={`/api/v1/snapshots/${data.snapshot_id}/download`}
              download
              title="Original snapshot with provenance"
            >
              <Icon name="download" size={15} />
              <span>Source JSON</span>
            </a>
          </div>
          <div className="date-toolbar">
            <div className="ranges" aria-label="Analysis date range">
              {['5Y', '10Y', '25Y', 'MAX'].map((value) => (
                <button
                  key={value}
                  aria-pressed={range === value}
                  onClick={() => setRange(value)}
                >
                  {value === 'MAX' ? 'All' : value}
                </button>
              ))}
            </div>
            <details className="custom-dates">
              <summary>
                {range === 'Custom'
                  ? `${custom.start || 'Start'} → ${custom.end || 'Latest'}`
                  : 'Custom dates'}
              </summary>
              <form
                onSubmit={(event) => {
                  event.preventDefault();
                  setCustom(draft);
                  setRange('Custom');
                }}
              >
                <label>
                  From
                  <input
                    type="date"
                    value={draft.start}
                    max={draft.end || undefined}
                    onChange={(event) =>
                      setDraft({ ...draft, start: event.target.value })
                    }
                  />
                </label>
                <label>
                  To
                  <input
                    type="date"
                    value={draft.end}
                    min={draft.start || undefined}
                    onChange={(event) =>
                      setDraft({ ...draft, end: event.target.value })
                    }
                  />
                </label>
                <button className="secondary">Apply</button>
              </form>
            </details>
          </div>
          {tab === 'forecast' ? (
            <Forecast
              key={`${data.snapshot_id}-${start}-${end}`}
              snapshot={data}
              start={start}
              end={end}
            />
          ) : (
            <AnalysisView
              snapshot={data}
              start={start}
              end={end}
              statistics={tab === 'statistics'}
            />
          )}
          <details className="provenance">
            <summary>
              Source & details{' '}
              <span className="muted">
                {data.series.provider === 'local'
                  ? 'Imported CSV'
                  : 'Latest revision'}
              </span>
            </summary>
            <dl>
              <div>
                <dt>Source</dt>
                <dd>
                  {data.series.source_url ? (
                    <a
                      href={data.series.source_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {data.series.source_name} ↗
                    </a>
                  ) : (
                    data.series.source_name
                  )}
                </dd>
              </div>
              <div>
                <dt>Retrieved</dt>
                <dd>{new Date(data.retrieved_at).toLocaleString()}</dd>
              </div>
              <div>
                <dt>Source transformations</dt>
                <dd>{data.transformations.join(' ') || 'None'}</dd>
              </div>
              <div>
                <dt>Updated</dt>
                <dd>{data.series.updated || 'Not reported'}</dd>
              </div>
            </dl>
            <p className="small source-notes">{data.series.notes}</p>
            <p className="small">{data.vintage}</p>
            <p className="small hash">Snapshot: {data.snapshot_id}</p>
            {data.series.license_url && (
              <a
                href={data.series.license_url}
                target="_blank"
                rel="noreferrer"
              >
                Provider terms ↗
              </a>
            )}
            <a
              className="text-button"
              href={`/api/v1/snapshots/${data.snapshot_id}/csv`}
              download
            >
              <Icon name="download" size={14} />
              Original CSV
            </a>
          </details>
        </>
      )}
    </article>
  );
}
