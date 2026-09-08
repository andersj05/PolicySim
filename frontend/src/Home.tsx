import { Icon } from './components';
import { names, starters, pickKey } from './catalog';
import type { Provider, SeriesPick } from './catalog';

const collections: {
  provider: Provider;
  title: string;
  description: string;
  label: string;
  symbol: string;
}[] = [
  {
    provider: 'fred',
    title: 'The US economy',
    description: 'Growth, inflation, interest rates and financial conditions.',
    label: 'FRED',
    symbol: 'F',
  },
  {
    provider: 'bls',
    title: 'Labor & prices',
    description: 'Employment, wages and consumer prices, direct from BLS.',
    label: 'Bureau of Labor Statistics',
    symbol: 'B',
  },
  {
    provider: 'ecb',
    title: 'Global currencies',
    description:
      'Monthly reference exchange rates from the European Central Bank.',
    label: 'ECB',
    symbol: '€',
  },
  {
    provider: 'worldbank',
    title: 'Across economies',
    description: 'Development indicators across countries and regions.',
    label: 'World Bank',
    symbol: 'W',
  },
];

export default function Home({
  library,
  open,
  importData,
  forecasts,
}: {
  library: SeriesPick[];
  open: (item: SeriesPick) => void;
  importData: () => void;
  forecasts: () => void;
}) {
  return (
    <div className="home-page">
      <div className="home-heading">
        <div>
          <span className="eyebrow">YOUR RESEARCH WORKSPACE</span>
          <h2>Economic research, organized.</h2>
          <p>Official data, reproducible forecasts, and your saved research.</p>
        </div>
        <button className="secondary" onClick={importData}>
          <Icon name="upload" size={16} /> Import your data
        </button>
      </div>
      <section aria-labelledby="explore-title">
        <div className="section-heading">
          <h3 id="explore-title">Explore data</h3>
          <span>4 official sources</span>
        </div>
        <div className="collection-grid">
          {collections.map((item) => (
            <button
              key={item.provider}
              className={`collection-card collection-${item.provider}`}
              onClick={() => open(starters[item.provider][0]!)}
            >
              <div className="collection-art" aria-hidden="true">
                <span>{item.symbol}</span>
                <i />
                <i />
                <i />
              </div>
              <div className="collection-body">
                <span className="eyebrow">{item.label}</span>
                <h4>{item.title}</h4>
                <p>{item.description}</p>
                <span className="collection-action">
                  Explore series <Icon name="arrow" size={16} />
                </span>
              </div>
            </button>
          ))}
        </div>
      </section>
      <div className="home-lower">
        <section className="continue-panel" aria-labelledby="continue-title">
          <div className="section-heading">
            <h3 id="continue-title">Your library</h3>
            <span>{library.length} saved</span>
          </div>
          {library.length ? (
            <div className="recent-list">
              {library.slice(0, 5).map((item) => (
                <button key={pickKey(item)} onClick={() => open(item)}>
                  <span className={`recent-icon ${item.provider}`}>
                    <Icon name="chart" size={19} />
                  </span>
                  <span>
                    <strong>{item.title}</strong>
                    <small>
                      {names[item.provider]}
                      {item.country ? ` · ${item.country}` : ''} · Saved
                      snapshot
                    </small>
                  </span>
                  <Icon name="arrow" size={17} />
                </button>
              ))}
            </div>
          ) : (
            <div className="library-onboarding">
              <span className="onboarding-icon">
                <Icon name="save" size={24} />
              </span>
              <h4>Keep your research close</h4>
              <p>
                Save a series from the data workspace to return to its exact
                source snapshot.
              </p>
              <button
                className="text-button"
                onClick={() => open(starters.fred[1]!)}
              >
                Start with GDP <Icon name="arrow" size={15} />
              </button>
            </div>
          )}
        </section>
        <section className="forecast-feature" aria-labelledby="bench-title">
          <span className="eyebrow">MODEL WORKBENCH</span>
          <Icon name="forecast" size={28} />
          <h3 id="bench-title">
            Compare forecast
            <br />
            models.
          </h3>
          <p>
            Compare seven statistical methods against a naive baseline, with
            chronological validation and a separate final holdout.
          </p>
          <div className="method-tags">
            <span>ARIMA</span>
            <span>ETS</span>
            <span>Autoregression</span>
          </div>
          <button className="primary" onClick={forecasts}>
            Open saved forecasts <Icon name="arrow" size={16} />
          </button>
        </section>
      </div>
      <p className="home-footnote">
        <Icon name="save" size={14} /> Snapshots and forecasts stay on this
        computer. Source revisions and model assumptions are recorded with your
        work.
      </p>
    </div>
  );
}
