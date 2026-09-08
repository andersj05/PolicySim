import { useState } from 'react';
import type {
  AnalysisRequest,
  AnalysisResult,
  Snapshot,
} from './api.generated';
import { useAnalysis } from './api';
import Chart from './Chart';
import DataTable from './DataTable';
import { Icon, Message } from './components';
import { formatValue } from './format';

export function FrequencySelect({
  value,
  change,
}: {
  value: AnalysisRequest['frequency'];
  change: (value: AnalysisRequest['frequency']) => void;
}) {
  return (
    <label>
      Frequency
      <select
        value={value}
        onChange={(event) =>
          change(event.target.value as AnalysisRequest['frequency'])
        }
      >
        <option value="auto">From source</option>
        {['annual', 'quarterly', 'monthly', 'weekly', 'daily'].map(
          (frequency) => (
            <option key={frequency} value={frequency}>
              {frequency[0]!.toUpperCase() + frequency.slice(1)}
            </option>
          ),
        )}
      </select>
    </label>
  );
}

export default function AnalysisView({
  snapshot,
  start,
  end,
  statistics,
}: {
  snapshot: Snapshot;
  start: string;
  end: string;
  statistics: boolean;
}) {
  const [transform, setTransform] =
    useState<AnalysisRequest['transform']>('level');
  const [frequency, setFrequency] =
    useState<AnalysisRequest['frequency']>('auto');
  const [lag, setLag] = useState(1);
  const [windowSize, setWindowSize] = useState(12);
  const [view, setView] = useState<'chart' | 'table'>('chart');
  const [exportError, setExportError] = useState('');
  const request: AnalysisRequest = {
    snapshot_id: snapshot.snapshot_id,
    start,
    end,
    transform,
    frequency,
    lag,
    window: windowSize,
  };
  const result = useAnalysis<AnalysisResult>('/api/v1/analysis', request);
  const data = result.data;
  async function download() {
    setExportError('');
    try {
      const response = await fetch('/api/v1/analysis/csv', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });
      if (!response.ok)
        throw new Error('Export failed. Retry after the analysis loads.');
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement('a');
      link.href = url;
      link.download = `${snapshot.series.id}-${transform}.csv`;
      link.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) {
      setExportError(error instanceof Error ? error.message : 'Export failed.');
    }
  }
  return (
    <section
      className="analysis-view"
      aria-label={statistics ? 'Series statistics' : 'Data analysis'}
    >
      <div className="analysis-toolbar">
        <label>
          Transform
          <select
            value={transform}
            onChange={(event) =>
              setTransform(event.target.value as AnalysisRequest['transform'])
            }
          >
            <option value="level">Original values</option>
            <option value="difference">Difference</option>
            <option value="pct_change">Percent change</option>
            <option value="log">Natural log</option>
            <option value="rolling_mean">Rolling mean</option>
          </select>
        </label>
        {(transform === 'difference' || transform === 'pct_change') && (
          <label className="short-field">
            Lag
            <input
              type="number"
              min={1}
              max={60}
              value={lag}
              onChange={(event) =>
                setLag(Math.max(1, Math.min(60, Number(event.target.value))))
              }
            />
          </label>
        )}
        {transform === 'rolling_mean' && (
          <label className="short-field">
            Window
            <input
              type="number"
              min={2}
              max={120}
              value={windowSize}
              onChange={(event) =>
                setWindowSize(
                  Math.max(2, Math.min(120, Number(event.target.value))),
                )
              }
            />
          </label>
        )}
        <details className="frequency-details">
          <summary>Calendar</summary>
          <FrequencySelect value={frequency} change={setFrequency} />
        </details>
        {!statistics && (
          <div className="view-switch" aria-label="Data view">
            <button
              aria-pressed={view === 'chart'}
              onClick={() => setView('chart')}
            >
              <Icon name="chart" size={15} />
              Chart
            </button>
            <button
              aria-pressed={view === 'table'}
              onClick={() => setView('table')}
            >
              <Icon name="table" size={15} />
              Table
            </button>
          </div>
        )}
      </div>
      {result.loading && (
        <div role="status" className="loading-analysis">
          <div className="skeleton chart-skeleton" />
          <span>Calculating…</span>
        </div>
      )}
      {result.error && <Message error={result.error} retry={result.retry} />}
      {data && (
        <>
          {statistics ? (
            <>
              <div className="statistics-grid">
                {(
                  [
                    ['Mean', data.statistics.mean],
                    ['Median', data.statistics.median],
                    ['Std. deviation', data.statistics.std],
                    ['Minimum', data.statistics.minimum],
                    ['Maximum', data.statistics.maximum],
                    ['25th percentile', data.statistics.q25],
                    ['75th percentile', data.statistics.q75],
                    ['Numeric values', data.statistics.count],
                  ] as const
                ).map(([label, value]) => (
                  <div className="stat-cell" key={label}>
                    <span>{label}</span>
                    <strong title={String(value)}>
                      {formatValue(value, Math.abs(value ?? 0) >= 1e6)}
                    </strong>
                  </div>
                ))}
              </div>
              <div className="diagnostic-grid">
                <section>
                  <div className="section-label">Autocorrelation</div>
                  {data.autocorrelation.length ? (
                    <div
                      className="acf-chart"
                      role="img"
                      aria-label="Autocorrelation by lag. Values are available in the table below."
                    >
                      <div className="acf-zero" />
                      {data.autocorrelation.map((point) => (
                        <div className="acf-column" key={point.lag}>
                          <div
                            className={`acf-bar ${point.value < 0 ? 'negative' : ''}`}
                            style={{
                              height: `${Math.abs(point.value) * 44}%`,
                              bottom:
                                point.value < 0
                                  ? `${50 - Math.abs(point.value) * 44}%`
                                  : '50%',
                            }}
                            title={`Lag ${point.lag}: ${point.value.toFixed(4)}`}
                          />
                          <span>{point.lag}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="empty-inline">
                      Unavailable for this selection.
                    </p>
                  )}
                  <details>
                    <summary>Correlation values</summary>
                    <div className="table-region">
                      <table>
                        <thead>
                          <tr>
                            <th>Lag</th>
                            <th>Correlation</th>
                          </tr>
                        </thead>
                        <tbody>
                          {data.autocorrelation.map((point) => (
                            <tr key={point.lag}>
                              <td>{point.lag}</td>
                              <td>{point.value.toFixed(4)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </details>
                </section>
                <section>
                  <div className="section-label">Stationarity · ADF</div>
                  <div className="test-value">
                    {data.statistics.adf_pvalue === null
                      ? '—'
                      : data.statistics.adf_pvalue < 0.0001
                        ? '< 0.0001'
                        : data.statistics.adf_pvalue.toFixed(4)}
                    <span>p-value</span>
                  </div>
                  <p className="small">
                    The null hypothesis is a unit root. A small p-value is
                    evidence against it; this test alone does not select a
                    model.
                  </p>
                  <dl className="compact-dl">
                    <div>
                      <dt>Statistic</dt>
                      <dd>{formatValue(data.statistics.adf_statistic)}</dd>
                    </div>
                    <div>
                      <dt>Lags (AIC)</dt>
                      <dd>{data.statistics.adf_lags ?? '—'}</dd>
                    </div>
                    <div>
                      <dt>Regression</dt>
                      <dd>Constant</dd>
                    </div>
                  </dl>
                </section>
              </div>
            </>
          ) : view === 'chart' ? (
            <Chart
              key={`${start}-${end}-${transform}`}
              observations={data.observations}
              title={snapshot.series.title}
            />
          ) : (
            <DataTable
              key={`${start}-${end}-${transform}`}
              observations={data.observations}
              title={snapshot.series.title}
              units={data.units}
            />
          )}
          <div className="chart-footnote">
            <span>
              <span className="legend-line" />
              {data.units}
            </span>
            <span>
              {data.statistics.count.toLocaleString()} values ·{' '}
              {data.statistics.missing} missing
            </span>
            <button className="text-button" onClick={() => void download()}>
              <Icon name="download" size={14} />
              Export CSV
            </button>
          </div>
          {data.warnings.length > 0 && (
            <details className="analysis-notes">
              <summary>
                Data notes <span className="count">{data.warnings.length}</span>
              </summary>
              {data.warnings.map((note) => (
                <p className="small" key={note}>
                  {note}
                </p>
              ))}
            </details>
          )}
        </>
      )}
      {exportError && (
        <p role="alert" className="notice error">
          {exportError}
        </p>
      )}
    </section>
  );
}
