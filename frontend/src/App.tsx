import { useEffect, useRef, useState } from 'react';
import type {
  Country,
  ProviderStatus,
  SearchResult,
  Series,
} from './api.generated';
import { useRemote } from './api';
import Detail from './Detail';
import { Icon, Message, SourceDialog } from './components';

export type Provider = Series['provider'];
export type SeriesPick = {
  provider: Provider;
  id: string;
  title: string;
  source_id: string;
};
const names = { fred: 'FRED', worldbank: 'World Bank' };
const starters: Record<Provider, SeriesPick[]> = {
  fred: [
    {
      provider: 'fred',
      id: 'UNRATE',
      title: 'Unemployment Rate',
      source_id: '',
    },
    {
      provider: 'fred',
      id: 'GDP',
      title: 'Gross Domestic Product',
      source_id: '',
    },
    {
      provider: 'fred',
      id: 'CPIAUCSL',
      title: 'Consumer Price Index',
      source_id: '',
    },
    {
      provider: 'fred',
      id: 'FEDFUNDS',
      title: 'Federal Funds Effective Rate',
      source_id: '',
    },
    {
      provider: 'fred',
      id: 'DGS10',
      title: '10-Year Treasury Yield',
      source_id: '',
    },
  ],
  worldbank: [
    {
      provider: 'worldbank',
      id: 'NY.GDP.MKTP.CD',
      title: 'GDP (current US$)',
      source_id: '2',
    },
    {
      provider: 'worldbank',
      id: 'SP.POP.TOTL',
      title: 'Population, total',
      source_id: '2',
    },
    {
      provider: 'worldbank',
      id: 'FP.CPI.TOTL.ZG',
      title: 'Inflation, consumer prices (annual %)',
      source_id: '2',
    },
    {
      provider: 'worldbank',
      id: 'SL.UEM.TOTL.ZS',
      title: 'Unemployment, total (% of labor force)',
      source_id: '2',
    },
    {
      provider: 'worldbank',
      id: 'SP.DYN.LE00.IN',
      title: 'Life expectancy at birth, total (years)',
      source_id: '2',
    },
  ],
};

export default function App() {
  const [provider, setProvider] = useState<Provider>('fred');
  const [input, setInput] = useState('');
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const [refresh, setRefresh] = useState(0);
  const [selected, setSelected] = useState<SeriesPick>(starters.fred[0]!);
  const [recent, setRecent] = useState<SeriesPick[]>([]);
  const [country, setCountry] = useState('USA');
  const [guide, setGuide] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const status = useRemote<ProviderStatus>('/api/v1/providers');
  const countries = useRemote<Country[]>(
    provider === 'worldbank' || selected.provider === 'worldbank'
      ? '/api/v1/countries'
      : null,
    refresh,
  );
  const search = useRemote<SearchResult>(
    query
      ? `/api/v1/series?${new URLSearchParams({ provider, q: query, page: String(page) })}`
      : null,
    refresh,
  );
  useEffect(() => {
    const handle = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
        event.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handle);
    return () => window.removeEventListener('keydown', handle);
  }, []);
  function pick(item: SeriesPick) {
    setSelected(item);
    setRecent((list) =>
      [
        item,
        ...list.filter(
          (entry) =>
            !(
              entry.id === item.id &&
              entry.provider === item.provider &&
              entry.source_id === item.source_id
            ),
        ),
      ].slice(0, 6),
    );
  }
  function submit(value: string) {
    setInput(value);
    setQuery(value.trim());
    setPage(1);
    setRefresh((v) => v + 1);
  }
  const list = query ? (search.data?.items ?? []) : starters[provider];
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        Skip to data explorer
      </a>
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="PolicySim home">
          <span className="brand-mark">
            <i />
            <i />
            <i />
          </span>
          PolicySim<span className="brand-dot">.</span>
        </a>
        <div className="workspace-label">
          <span className="workspace-avatar">P</span>
          <div>
            Personal workspace<span>Local research</span>
          </div>
        </div>
        <span className="nav-label">WORKSPACE</span>
        <nav aria-label="Workspace">
          <button
            className="nav-item active"
            onClick={() => inputRef.current?.focus()}
          >
            <Icon name="grid" />
            Data explorer
            <span className="nav-indicator" />
          </button>
          <button className="nav-item" onClick={() => setGuide(true)}>
            <Icon name="globe" />
            Data sources<small>2</small>
          </button>
        </nav>
        <div className="recent-heading">
          <span className="nav-label">RECENTLY OPENED</span>
          <Icon name="chart" size={14} />
        </div>
        <div className="recent-list">
          {recent.length ? (
            recent.map((item) => (
              <button
                key={`${item.provider}-${item.source_id}-${item.id}`}
                onClick={() => pick(item)}
                title={item.title}
              >
                <span className={`tiny-dot ${item.provider}`} />
                <span>{item.title}</span>
              </button>
            ))
          ) : (
            <p>
              Series you open will
              <br />
              appear here this session.
            </p>
          )}
        </div>
        <div className="sidebar-bottom">
          <div className="local-note">
            <span className="local-dot" />
            <div>
              Your local workspace<span>Source data stays on this device</span>
            </div>
          </div>
          <button className="profile" onClick={() => setGuide(true)}>
            <span className="profile-avatar">P</span>
            <div>
              Research workspace<span>Getting started</span>
            </div>
            <Icon name="chevron" size={15} />
          </button>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumbs">
            Workspace
            <Icon name="chevron" size={12} />
            <strong>Data explorer</strong>
          </div>
          <button className="text-button" onClick={() => setGuide(true)}>
            <Icon name="book" size={15} />
            Quick guide
          </button>
        </header>
        <main id="main">
          <div className="page-heading">
            <div>
              <div className="eyebrow">THE WORLD, IN DATA</div>
              <h1>Find your next insight.</h1>
              <p>Explore trusted economic data. Build a clearer picture.</p>
            </div>
            <span className="workspace-badge">
              <span />
              Data explorer <span className="version">01</span>
            </span>
          </div>
          <div className="source-cards" aria-label="Select data provider">
            {(['fred', 'worldbank'] as const).map((item) => (
              <button
                className={`source-card ${provider === item ? 'selected' : ''}`}
                key={item}
                aria-pressed={provider === item}
                onClick={() => {
                  setProvider(item);
                  setPage(1);
                }}
              >
                <span className={`provider-logo ${item}`}>
                  {item === 'fred' ? (
                    <Icon name="chart" size={23} />
                  ) : (
                    <Icon name="globe" size={25} />
                  )}
                </span>
                <span className="source-card-copy">
                  <strong>
                    {names[item]}
                    <span className="provider-tag">
                      {item === 'fred' ? 'U.S. & global' : 'Across countries'}
                    </span>
                  </strong>
                  <span>
                    {item === 'fred'
                      ? 'Markets, monetary policy & the economy'
                      : 'Development, people & the planet'}
                  </span>
                </span>
                <span className="selection-radio" />
              </button>
            ))}
          </div>
          <form
            className="search-form"
            role="search"
            onSubmit={(event) => {
              event.preventDefault();
              submit(input);
            }}
          >
            <Icon name="search" size={21} />
            <input
              ref={inputRef}
              aria-label={`Search ${names[provider]} series`}
              value={input}
              maxLength={200}
              placeholder={`Search ${names[provider]} by keyword or series ID…`}
              onChange={(event) => setInput(event.target.value)}
            />
            {input && (
              <button
                type="button"
                className="icon-button"
                aria-label="Clear search"
                onClick={() => submit('')}
              >
                <Icon name="close" size={16} />
              </button>
            )}
            <kbd>Ctrl K</kbd>
            <button className="primary" type="submit">
              Search
              <Icon name="arrow" size={16} />
            </button>
          </form>
          <div className="suggestions">
            <span>Try exploring</span>
            {['GDP', 'inflation', 'unemployment', 'population'].map((term) => (
              <button key={term} onClick={() => submit(term)}>
                {term}
                <Icon name="arrow" size={12} />
              </button>
            ))}
          </div>
          <div className="explorer-grid">
            <section className="catalog" aria-label="Series catalog">
              <div className="catalog-heading">
                <div>
                  <h2>{query ? 'Search results' : 'A good place to start'}</h2>
                  <span>
                    {query
                      ? `Matches in ${names[provider]}`
                      : 'Essential economic indicators'}
                  </span>
                </div>
                <span className="count">
                  {search.data && query
                    ? search.data.total.toLocaleString()
                    : query
                      ? '…'
                      : '05'}
                </span>
              </div>
              {provider === 'worldbank' && (
                <div className="country-control">
                  <label htmlFor="country">COUNTRY OR AGGREGATE</label>
                  <select
                    id="country"
                    value={country}
                    onChange={(event) => setCountry(event.target.value)}
                    disabled={countries.loading}
                  >
                    <option value="USA">United States</option>
                    {countries.data
                      ?.filter((c) => c.id !== 'USA')
                      .map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name}
                          {c.aggregate ? ' (aggregate)' : ''}
                        </option>
                      ))}
                  </select>
                  {countries.loading && (
                    <span role="status" className="small">
                      Loading geographies…
                    </span>
                  )}
                  {countries.error && (
                    <Message
                      error={countries.error}
                      retry={() => setRefresh((v) => v + 1)}
                    />
                  )}
                </div>
              )}
              <div className="result-list" aria-busy={search.loading}>
                {search.loading ? (
                  <div role="status" className="catalog-loading">
                    <div className="skeleton" />
                    <div className="skeleton" />
                    <div className="skeleton" />
                    <p>
                      Searching {names[provider]}…
                      {provider === 'worldbank' && (
                        <span>
                          The first search builds the indicator index. This can
                          take a moment.
                        </span>
                      )}
                    </p>
                  </div>
                ) : search.error && query ? (
                  <Message
                    error={search.error}
                    retry={() => setRefresh((v) => v + 1)}
                  />
                ) : list.length ? (
                  list.map((item) => (
                    <button
                      className={`series-result ${selected.id === item.id && selected.provider === item.provider && selected.source_id === item.source_id ? 'selected' : ''}`}
                      key={`${item.source_id}-${item.id}`}
                      onClick={() => pick(item)}
                    >
                      <span className="result-top">
                        <span className="mono">{item.id}</span>
                        <Icon name="arrow" size={15} />
                      </span>
                      <strong>{item.title}</strong>
                      <span className="result-meta">
                        {'frequency' in item
                          ? item.provider === 'worldbank'
                            ? (item as Series).source_name
                            : (item as Series).frequency
                          : names[provider]}
                      </span>
                    </button>
                  ))
                ) : (
                  <div className="message">
                    <Icon name="search" size={25} />
                    <h3>No matching series</h3>
                    <p>Try a broader keyword or switch providers.</p>
                    <button className="secondary" onClick={() => submit('')}>
                      Browse starting points
                    </button>
                  </div>
                )}
              </div>
              {query && search.data && (
                <div className="pagination">
                  <button
                    disabled={page === 1}
                    onClick={() => setPage((v) => v - 1)}
                  >
                    Previous
                  </button>
                  <span>
                    {search.data.total ? page : 0} /{' '}
                    {Math.ceil(search.data.total / search.data.page_size)}
                  </span>
                  <button
                    disabled={page * search.data.page_size >= search.data.total}
                    onClick={() => setPage((v) => v + 1)}
                  >
                    Next
                  </button>
                </div>
              )}
              <div className="catalog-note">
                <Icon name="globe" size={16} />
                <p>
                  Direct from the source.
                  <br />
                  <span>Every series keeps its provenance.</span>
                </p>
              </div>
            </section>
            <Detail
              key={`${selected.provider}-${selected.source_id}-${selected.id}-${country}`}
              selected={selected}
              country={country}
              countryName={
                countries.data?.find((c) => c.id === country)?.name ?? country
              }
            />
          </div>
          <footer>
            <span>
              PolicySim <span className="footer-separator">/</span> A workspace
              for better economic questions.
            </span>
            <span>
              {status.error
                ? 'Research server unavailable'
                : status.data?.fred_configured
                  ? 'FRED key configured'
                  : 'FRED key not configured'}{' '}
              <span className="footer-separator">·</span> World Bank requires no
              key
            </span>
          </footer>
        </main>
      </div>
      {guide && <SourceDialog close={() => setGuide(false)} />}
    </div>
  );
}
