import { useState } from 'react';
import type { ForecastRun, RunSummary } from './api.generated';
import { useRemote } from './api';
import { Icon, Message } from './components';
import ForecastResults from './ForecastResults';
import { modelNames } from './catalog';

export default function Runs() {
  const [selected, setSelected] = useState<string>();
  const [query, setQuery] = useState('');
  const [refresh, setRefresh] = useState(0);
  const list = useRemote<RunSummary[]>('/api/v1/forecasts', refresh);
  const run = useRemote<ForecastRun>(
    selected ? `/api/v1/forecasts/${selected}` : null,
    refresh,
  );
  const filtered = list.data?.filter((item) =>
    `${item.title} ${item.country}`.toLowerCase().includes(query.toLowerCase()),
  );
  if (selected)
    return (
      <div className="saved-run-view">
        <button
          className="text-button back-button"
          onClick={() => setSelected(undefined)}
        >
          ← Saved forecasts
        </button>
        {run.loading && (
          <p role="status" className="empty-inline">
            Loading forecast…
          </p>
        )}
        {run.error && (
          <Message error={run.error} retry={() => setRefresh((v) => v + 1)} />
        )}
        {run.data && (
          <>
            <div className="saved-run-heading">
              <h2>{run.data.title}</h2>
              <span className="small">
                {run.data.country}{' '}
                {new Date(run.data.created_at).toLocaleString()}
              </span>
            </div>
            <ForecastResults run={run.data} />
          </>
        )}
      </div>
    );
  return (
    <section className="runs-page">
      <div className="runs-heading">
        <div>
          <h2>Saved forecasts</h2>
          <p className="small">
            {list.data?.length ?? 0} runs · Most recent 100
          </p>
        </div>
        <button className="secondary" onClick={() => setRefresh((v) => v + 1)}>
          Refresh
        </button>
      </div>
      <label className="runs-search">
        <Icon name="search" size={17} />
        <input
          aria-label="Filter saved forecasts"
          placeholder="Filter by series or country…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </label>
      {list.loading && (
        <p className="empty-inline" role="status">
          Loading saved runs…
        </p>
      )}
      {list.error && (
        <Message error={list.error} retry={() => setRefresh((v) => v + 1)} />
      )}
      {filtered?.length ? (
        <div className="run-cards">
          {filtered.map((item) => (
            <button
              className="run-card"
              key={item.run_id}
              onClick={() => setSelected(item.run_id)}
            >
              <span className="run-card-icon">
                <Icon name="forecast" size={22} />
              </span>
              <span>
                <strong>{item.title}</strong>
                <span>
                  {item.country ? `${item.country} · ` : ''}
                  {item.horizon} periods · {item.frequency}
                </span>
                <small>
                  {item.models
                    .map(
                      (name) =>
                        modelNames[name as keyof typeof modelNames] ?? name,
                    )
                    .join(' · ')}
                </small>
              </span>
              <span className="run-date">
                {new Date(item.created_at).toLocaleString()}
                <Icon name="arrow" size={17} />
              </span>
            </button>
          ))}
        </div>
      ) : (
        !list.loading &&
        !list.error && (
          <div className="runs-empty">
            <Icon name="forecast" size={36} />
            <h3>
              {query ? 'No matching forecasts' : 'No saved forecasts yet'}
            </h3>
            <p>
              {query
                ? 'Try another series name.'
                : 'Open a series in Data, choose Forecast, and run a model.'}
            </p>
          </div>
        )
      )}
    </section>
  );
}
