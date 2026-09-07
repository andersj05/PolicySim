import { useState } from 'react';
import type { ForecastRun, ModelResult } from './api.generated';
import Chart from './Chart';
import { modelNames } from './catalog';
import { formatValue } from './format';
import { Icon } from './components';

export default function ForecastResults({ run }: { run: ForecastRun }) {
  const available = run.models.filter((model) => model.status === 'success');
  const [selected, setSelected] = useState(
    available.find((model) => model.model === 'ets')?.model ??
      available[0]?.model,
  );
  const [tab, setTab] = useState<
    'forecast' | 'evaluation' | 'diagnostics' | 'values'
  >('forecast');
  const [evaluation, setEvaluation] = useState<'validation' | 'holdout'>(
    'validation',
  );
  const [historyRange, setHistoryRange] = useState<'recent' | 'all'>('recent');
  const model = available.find((item) => item.model === selected);
  const baseline = available.find((item) => item.model === 'naive');
  const last = model?.forecast.at(-1);
  function metric(
    item: ModelResult,
    name: 'mae' | 'rmse' | 'mase' | 'coverage',
  ) {
    const value = item[evaluation]?.[name];
    return name === 'coverage' && value != null
      ? `${(value * 100).toFixed(1)}%`
      : formatValue(value, Math.abs(value ?? 0) >= 1e6);
  }
  return (
    <div className="forecast-results">
      <div className="result-select">
        <label>
          Displayed model
          <select
            value={selected}
            onChange={(event) =>
              setSelected(event.target.value as typeof selected)
            }
          >
            {available.map((item) => (
              <option key={item.model} value={item.model}>
                {modelNames[item.model]}
              </option>
            ))}
          </select>
        </label>
        <a
          className="text-button"
          href={`/api/v1/forecasts/${run.run_id}/download`}
          download
        >
          <Icon name="download" size={15} />
          Download run
        </a>
        <span className="saved-state">
          <span className="status-dot" />
          Saved
        </span>
      </div>
      <div className="results-tabs" aria-label="Forecast result view">
        {(['forecast', 'evaluation', 'diagnostics', 'values'] as const).map(
          (value) => (
            <button
              key={value}
              aria-pressed={tab === value}
              onClick={() => setTab(value)}
            >
              {value[0]!.toUpperCase() + value.slice(1)}
            </button>
          ),
        )}
      </div>
      {model && (
        <>
          {tab === 'forecast' && (
            <>
              <div className="forecast-metrics">
                <div>
                  <span>{last?.date} forecast</span>
                  <strong>
                    {formatValue(
                      last?.value,
                      Math.abs(last?.value ?? 0) >= 1e6,
                    )}
                  </strong>
                  <small>{run.units}</small>
                </div>
                <div>
                  <span>{run.request.interval}% prediction interval</span>
                  <strong className="interval-value">
                    {formatValue(last?.lower, true)} <span>–</span>{' '}
                    {formatValue(last?.upper, true)}
                  </strong>
                  <small>Conditional on fitted parameters</small>
                </div>
                <div>
                  <span>Validation RMSE</span>
                  <strong>
                    {formatValue(
                      model.validation?.rmse,
                      Math.abs(model.validation?.rmse ?? 0) >= 1e6,
                    )}
                  </strong>
                  <small>
                    Naive:{' '}
                    {formatValue(
                      baseline?.validation?.rmse,
                      Math.abs(baseline?.validation?.rmse ?? 0) >= 1e6,
                    )}
                  </small>
                </div>
              </div>
              <div className="forecast-chart-toolbar">
                <span className="small">
                  {run.frequency[0]!.toUpperCase() + run.frequency.slice(1)} ·{' '}
                  {run.units}
                </span>
                <div className="ranges">
                  <button
                    aria-pressed={historyRange === 'recent'}
                    onClick={() => setHistoryRange('recent')}
                  >
                    Recent history
                  </button>
                  <button
                    aria-pressed={historyRange === 'all'}
                    onClick={() => setHistoryRange('all')}
                  >
                    All history
                  </button>
                </div>
              </div>
              <Chart
                key={`${model.model}-${historyRange}`}
                observations={
                  historyRange === 'recent'
                    ? run.history.slice(-Math.max(36, run.request.horizon * 3))
                    : run.history
                }
                forecast={model.forecast}
                interval={run.request.interval}
                title={run.title}
              />
              <div className="forecast-legend">
                <span>
                  <i className="legend-line" />
                  Observed
                </span>
                <span>
                  <i className="legend-line forecast-line" />
                  Forecast
                </span>
                <span>
                  <i className="interval-swatch" />
                  {run.request.interval}% interval
                </span>
              </div>
            </>
          )}
          {tab === 'evaluation' && (
            <>
              <div className="evaluation-heading">
                <div className="view-switch">
                  <button
                    aria-pressed={evaluation === 'validation'}
                    onClick={() => setEvaluation('validation')}
                  >
                    Rolling validation
                  </button>
                  <button
                    aria-pressed={evaluation === 'holdout'}
                    onClick={() => setEvaluation('holdout')}
                  >
                    Final holdout
                  </button>
                </div>
                <span className="small">Lower error is better</span>
              </div>
              <div className="table-region">
                <table>
                  <thead>
                    <tr>
                      <th>Model</th>
                      <th title="Mean absolute error">MAE</th>
                      <th title="Root mean squared error">RMSE</th>
                      <th title="Mean absolute scaled error; undefined when training scale is zero">
                        MASE
                      </th>
                      <th
                        title={`Observed coverage of the ${run.request.interval}% prediction interval`}
                      >
                        Coverage
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {available.map((item) => (
                      <tr
                        className={
                          item.model === selected ? 'selected-row' : ''
                        }
                        key={item.model}
                      >
                        <td>
                          <button
                            className="table-model"
                            onClick={() => setSelected(item.model)}
                          >
                            {modelNames[item.model]}
                          </button>
                        </td>
                        {(['mae', 'rmse', 'mase', 'coverage'] as const).map(
                          (name) => (
                            <td key={name}>{metric(item, name)}</td>
                          ),
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="small evaluation-note">
                {evaluation === 'validation'
                  ? `${run.request.folds} expanding training windows; each predicts ${run.request.horizon} periods. MASE uses the training-only scale at seasonal period ${run.request.options.seasonal_period}.`
                  : 'The final block follows validation. Repeated tuning against these results compromises holdout independence.'}
              </p>
              {evaluation === 'holdout' ? (
                <Chart
                  observations={model.holdout_points.map((point) => ({
                    date: point.date,
                    value: point.actual,
                    realtime_start: '',
                    realtime_end: '',
                  }))}
                  title={`${run.title}: holdout actuals`}
                />
              ) : (
                <>
                  <div className="section-label">
                    Error by forecast horizon{' '}
                    <span>{modelNames[model.model]}</span>
                  </div>
                  <div className="horizon-bars">
                    {model.by_horizon.map((point) => (
                      <div key={point.horizon}>
                        <span>h{point.horizon}</span>
                        <div>
                          <i
                            style={{
                              width: `${(point.rmse / (Math.max(...model.by_horizon.map((item) => item.rmse)) || 1)) * 100}%`,
                            }}
                          />
                        </div>
                        <strong>
                          {formatValue(point.rmse, Math.abs(point.rmse) >= 1e6)}
                        </strong>
                      </div>
                    ))}
                  </div>
                </>
              )}
              <details className="evaluation-points">
                <summary>Evaluation predictions</summary>
                <div className="table-region">
                  <table>
                    <thead>
                      <tr>
                        <th>Origin</th>
                        <th>Date</th>
                        <th>h</th>
                        <th>Actual</th>
                        <th>Predicted</th>
                        <th>Lower</th>
                        <th>Upper</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(evaluation === 'validation'
                        ? model.validation_points
                        : model.holdout_points
                      ).map((point) => (
                        <tr key={`${point.origin}-${point.date}`}>
                          <td>{point.origin}</td>
                          <td>{point.date}</td>
                          <td>{point.horizon}</td>
                          <td>{formatValue(point.actual)}</td>
                          <td>{formatValue(point.value)}</td>
                          <td>{formatValue(point.lower)}</td>
                          <td>{formatValue(point.upper)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
            </>
          )}
          {tab === 'diagnostics' && (
            <>
              <div className="diagnostic-grid">
                <section>
                  <div className="section-label">Residual mean</div>
                  <div className="test-value">
                    {formatValue(model.diagnostics?.mean)}
                  </div>
                  <p className="small">
                    Residuals are observed minus fitted values, after
                    initialization periods.
                  </p>
                </section>
                <section>
                  <div className="section-label">Ljung–Box p-value</div>
                  <div className="test-value">
                    {model.diagnostics?.ljung_box_pvalue == null
                      ? '—'
                      : model.diagnostics.ljung_box_pvalue < 0.0001
                        ? '< 0.0001'
                        : model.diagnostics.ljung_box_pvalue.toFixed(4)}
                  </div>
                  <p className="small">
                    Lag {model.diagnostics?.ljung_box_lag}; adjusted df{' '}
                    {model.diagnostics?.degrees_of_freedom}. A small p-value
                    suggests remaining autocorrelation. This is a diagnostic,
                    not an accuracy score.
                  </p>
                </section>
              </div>
              <Chart
                observations={model.residuals}
                title={`${run.title}: residuals`}
              />
              <details>
                <summary>Estimated parameters</summary>
                <p className="small">
                  Estimation uses scaled training values; training_scale
                  restores original units.
                </p>
                <dl className="compact-dl">
                  {model.parameters.map((parameter) => (
                    <div key={parameter.name}>
                      <dt>{parameter.name}</dt>
                      <dd>{parameter.value}</dd>
                    </div>
                  ))}
                </dl>
              </details>
            </>
          )}
          {tab === 'values' && (
            <div className="table-region">
              <table>
                <caption className="table-caption">
                  Future forecasts · {run.units} · {run.request.interval}%
                  prediction interval
                </caption>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Forecast</th>
                    <th>Lower</th>
                    <th>Upper</th>
                  </tr>
                </thead>
                <tbody>
                  {model.forecast.map((point) => (
                    <tr key={point.date}>
                      <td>{point.date}</td>
                      <td title={String(point.value)}>
                        {formatValue(point.value)}
                      </td>
                      <td title={String(point.lower)}>
                        {formatValue(point.lower)}
                      </td>
                      <td title={String(point.upper)}>
                        {formatValue(point.upper)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {model.warnings.map((warning) => (
            <p key={warning} className="notice">
              {warning}
            </p>
          ))}
        </>
      )}
      {run.models
        .filter((item) => item.status === 'failed')
        .map((item) => (
          <p className="notice error" key={item.model}>
            <strong>{modelNames[item.model]}:</strong> {item.error}
          </p>
        ))}
      <div className="run-notices">
        {run.warnings.map((warning) => (
          <p className="small" key={warning}>
            {warning}
          </p>
        ))}
      </div>
      <details className="run-details">
        <summary>Method & run details</summary>
        <ul>
          {run.assumptions.map((assumption) => (
            <li key={assumption}>{assumption}</li>
          ))}
        </ul>
        <p className="small">
          Created {new Date(run.created_at).toLocaleString()} · Engine{' '}
          {run.engine_version}
        </p>
        <p className="small hash">Run {run.run_id}</p>
        <p className="small hash">Input {run.request.snapshot_id}</p>
        <details>
          <summary>Configuration</summary>
          <pre>{JSON.stringify(run.request, null, 2)}</pre>
        </details>
        <details>
          <summary>Environment</summary>
          <dl className="compact-dl">
            {run.environment.map((item) => (
              <div key={item.name}>
                <dt>{item.name}</dt>
                <dd className="hash">{item.value}</dd>
              </div>
            ))}
          </dl>
        </details>
        <a
          href="https://otexts.com/fpp3/tscv.html"
          target="_blank"
          rel="noreferrer"
        >
          Time series evaluation methods ↗
        </a>
      </details>
    </div>
  );
}
