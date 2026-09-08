import { useState } from 'react';
import type {
  ForecastRequest,
  ForecastRun,
  ModelOptions,
  Snapshot,
} from './api.generated';
import { post } from './api';
import { FrequencySelect } from './AnalysisView';
import { Icon } from './components';
import ForecastResults from './ForecastResults';
import ForecastReadiness from './ForecastReadiness';

import { modelNames } from './catalog';
const descriptions = {
  naive: 'Last observed value',
  mean: 'Long-run average with a constant forecast',
  autoreg: 'Learn persistence from consecutive lags',
  drift: 'Average historical change',
  seasonal_naive: 'Repeat the last seasonal cycle',
  ets: 'Estimate level, trend and seasonality',
  sarima: 'Autoregression, differencing and moving averages',
};
type Model = ForecastRequest['models'][number];
const defaults: ModelOptions = {
  ar_lags: 3,
  ar_trend: 'constant',
  p: 1,
  d: 1,
  q: 1,
  seasonal_p: 0,
  seasonal_d: 0,
  seasonal_q: 0,
  seasonal_period: 1,
  sarima_trend: 'none',
  ets_trend: true,
  ets_damped: true,
  ets_seasonal: false,
};

export default function Forecast({
  snapshot,
  start,
  end,
  applyRange,
}: {
  snapshot: Snapshot;
  start: string;
  end: string;
  applyRange: (start: string, end: string) => void;
}) {
  const annual = snapshot.series.frequency.toLowerCase() === 'annual';
  const quarterly = snapshot.series.frequency.toLowerCase() === 'quarterly';
  const [horizon, setHorizon] = useState(annual ? 3 : quarterly ? 4 : 12);
  const [folds, setFolds] = useState(3);
  const [interval, setInterval] = useState<80 | 95>(95);
  const [frequency, setFrequency] =
    useState<ForecastRequest['frequency']>('auto');
  const [missing, setMissing] =
    useState<ForecastRequest['missing']>('trim_edges');
  const [models, setModels] = useState<Model[]>(['naive', 'ets', 'sarima']);
  const [options, setOptions] = useState<ModelOptions>(defaults);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [run, setRun] = useState<ForecastRun>();
  const [submitted, setSubmitted] = useState('');
  const [editing, setEditing] = useState(true);
  const config: ForecastRequest = {
    snapshot_id: snapshot.snapshot_id,
    start,
    end,
    horizon,
    folds,
    interval,
    frequency,
    missing,
    models,
    options,
  };
  const stale = Boolean(run && submitted !== JSON.stringify(config));
  function toggle(model: Model) {
    setModels((values) =>
      values.includes(model)
        ? values.filter((value) => value !== model)
        : [...values, model],
    );
  }
  async function forecast() {
    setBusy(true);
    setError('');
    const key = JSON.stringify(config);
    try {
      const result = await post<ForecastRun>('/api/v1/forecasts', config);
      setRun(result);
      setSubmitted(key);
      setEditing(false);
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : 'Forecast failed.');
    } finally {
      setBusy(false);
    }
  }
  function order(key: keyof ModelOptions, label: string, max: number) {
    return (
      <label key={key}>
        {label}
        <input
          type="number"
          min={0}
          max={max}
          required
          value={Number(options[key])}
          onChange={(event) =>
            setOptions({ ...options, [key]: Number(event.target.value) })
          }
        />
      </label>
    );
  }
  return (
    <section className="forecast-workspace" aria-label="Forecast setup">
      <div className="forecast-heading">
        <div>
          <h3>{run ? 'Forecast' : 'New forecast'}</h3>
          {run && (
            <span className="small">
              {run.request.horizon} periods · {run.request.interval}% prediction
              interval
            </span>
          )}
        </div>
        {run && (
          <button className="secondary" onClick={() => setEditing(!editing)}>
            {editing ? 'Hide settings' : 'Edit settings'}
          </button>
        )}
      </div>
      {editing && (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void forecast();
          }}
        >
          <fieldset disabled={busy}>
            <div className="forecast-config">
              <div className="model-selection">
                <div className="section-label">Models</div>
                {(Object.keys(modelNames) as Model[]).map((model) => (
                  <label
                    className={`model-option ${models.includes(model) ? 'checked' : ''}`}
                    key={model}
                  >
                    <input
                      type="checkbox"
                      checked={models.includes(model)}
                      disabled={model === 'naive'}
                      onChange={() => toggle(model)}
                    />
                    <span>
                      <strong>
                        {modelNames[model]}
                        {model === 'naive' && <small>Baseline</small>}
                      </strong>
                      <span>{descriptions[model]}</span>
                    </span>
                  </label>
                ))}
              </div>
              <div className="forecast-settings">
                <div className="section-label">Evaluation</div>
                <div className="form-grid">
                  <label>
                    Horizon · periods
                    <input
                      type="number"
                      value={horizon}
                      min={1}
                      max={36}
                      required
                      onChange={(event) =>
                        setHorizon(Number(event.target.value))
                      }
                    />
                  </label>
                  <label>
                    Validation windows
                    <select
                      value={folds}
                      onChange={(event) => setFolds(Number(event.target.value))}
                    >
                      {[2, 3, 4, 5].map((value) => (
                        <option key={value}>{value}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Prediction interval
                    <select
                      value={interval}
                      onChange={(event) =>
                        setInterval(Number(event.target.value) as 80 | 95)
                      }
                    >
                      <option value={80}>80%</option>
                      <option value={95}>95%</option>
                    </select>
                  </label>
                  <label>
                    Seasonal period
                    <input
                      type="number"
                      value={options.seasonal_period}
                      min={1}
                      max={24}
                      required
                      onChange={(event) =>
                        setOptions({
                          ...options,
                          seasonal_period: Number(event.target.value),
                        })
                      }
                    />
                  </label>
                </div>
                <p className="field-help">
                  Use 1 for no seasonality, 4 for quarterly or 12 for monthly
                  annual cycles.
                </p>
                <div
                  className="evaluation-strip"
                  aria-label="Training, rolling validation, then final holdout"
                >
                  <span>Train</span>
                  {Array.from({ length: folds }, (_, i) => (
                    <span key={i}>V{i + 1}</span>
                  ))}
                  <span>Holdout</span>
                </div>
                <p className="field-help">
                  Each window predicts {horizon} future periods. The final
                  holdout follows validation. Forecasts then refit on the full
                  selection.
                </p>
              </div>
            </div>
            <details className="model-options">
              <summary>Model parameters & data handling</summary>
              <div className="advanced-grid">
                {models.includes('autoreg') && (
                  <section>
                    <h4>Autoregression</h4>
                    <label>
                      Consecutive lags
                      <input
                        type="number"
                        min={1}
                        max={24}
                        required
                        value={options.ar_lags}
                        onChange={(event) =>
                          setOptions({
                            ...options,
                            ar_lags: Number(event.target.value),
                          })
                        }
                      />
                    </label>
                    <label>
                      Deterministic trend
                      <select
                        value={options.ar_trend}
                        onChange={(event) =>
                          setOptions({
                            ...options,
                            ar_trend: event.target
                              .value as ModelOptions['ar_trend'],
                          })
                        }
                      >
                        <option value="constant">Constant</option>
                        <option value="linear">Constant + linear trend</option>
                      </select>
                    </label>
                    <p className="field-help">
                      Fixed lags, estimated by least squares. Unstable fits are
                      reported as failures.
                    </p>
                  </section>
                )}
                {models.includes('sarima') && (
                  <section>
                    <h4>ARIMA / SARIMA</h4>
                    <div className="order-grid">
                      {order('p', 'AR · p', 3)}
                      {order('d', 'Difference · d', 2)}
                      {order('q', 'MA · q', 3)}
                      {order('seasonal_p', 'Seasonal P', 1)}
                      {order('seasonal_d', 'Seasonal D', 1)}
                      {order('seasonal_q', 'Seasonal Q', 1)}
                    </div>
                    <label>
                      Trend term
                      <select
                        value={options.sarima_trend}
                        onChange={(event) =>
                          setOptions({
                            ...options,
                            sarima_trend: event.target
                              .value as ModelOptions['sarima_trend'],
                          })
                        }
                      >
                        <option value="none">None</option>
                        <option value="constant">
                          Constant (drift when d = 1)
                        </option>
                      </select>
                    </label>
                  </section>
                )}
                {models.includes('ets') && (
                  <section>
                    <h4>Exponential smoothing</h4>
                    <label className="checkbox">
                      <input
                        type="checkbox"
                        checked={options.ets_trend}
                        onChange={(event) =>
                          setOptions({
                            ...options,
                            ets_trend: event.target.checked,
                            ets_damped:
                              event.target.checked && options.ets_damped,
                          })
                        }
                      />
                      Additive trend
                    </label>
                    <label className="checkbox">
                      <input
                        type="checkbox"
                        disabled={!options.ets_trend}
                        checked={options.ets_damped}
                        onChange={(event) =>
                          setOptions({
                            ...options,
                            ets_damped: event.target.checked,
                          })
                        }
                      />
                      Damped trend
                    </label>
                    <label className="checkbox">
                      <input
                        type="checkbox"
                        checked={options.ets_seasonal}
                        onChange={(event) =>
                          setOptions({
                            ...options,
                            ets_seasonal: event.target.checked,
                          })
                        }
                      />
                      Additive seasonality
                    </label>
                    <p className="field-help">
                      Additive errors with analytical intervals. Seasonal models
                      require at least three cycles in every training window.
                    </p>
                  </section>
                )}
                <section>
                  <h4>Data handling</h4>
                  <FrequencySelect value={frequency} change={setFrequency} />
                  <label>
                    Missing observations
                    <select
                      value={missing}
                      onChange={(event) =>
                        setMissing(
                          event.target.value as ForecastRequest['missing'],
                        )
                      }
                    >
                      <option value="trim_edges">Trim missing edges</option>
                      <option value="reject">Reject any missing value</option>
                    </select>
                  </label>
                  <p className="field-help">
                    Internal gaps are always rejected. Dates above select the
                    original values used for forecasting.
                  </p>
                </section>
              </div>
            </details>
            <ForecastReadiness request={config} applyRange={applyRange} />
            <div className="run-actions">
              <span className="small">
                {start || 'First observation'} → {end || 'Latest'} · Original
                units
              </span>
              <button type="submit" className="primary">
                <Icon name="forecast" size={16} />
                {busy ? 'Running…' : run ? 'Run again' : 'Run forecast'}
              </button>
            </div>
          </fieldset>
        </form>
      )}
      {busy && (
        <div className="notice" role="status">
          <span className="spinner" />
          Fitting models and evaluating historical windows. The run will be
          saved when finished.
        </div>
      )}
      {error && (
        <p className="notice error" role="alert">
          {error}
        </p>
      )}
      {stale && (
        <p className="notice">
          Settings changed. Results below belong to the previous run.
        </p>
      )}
      {run && <ForecastResults key={run.run_id} run={run} />}
    </section>
  );
}
