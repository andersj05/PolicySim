import { useEffect, useRef, useState } from 'react';
import type {
  Country,
  ProviderStatus,
  SearchResult,
  Snapshot,
} from './api.generated';
import { useRemote } from './api';
import {
  names,
  pickKey,
  readLibrary,
  starters,
  sourceDescriptions,
} from './catalog';
import type { Provider, SeriesPick } from './catalog';
import Detail from './Detail';
import ImportDialog from './ImportDialog';
import Runs from './Runs';
import { Icon, Message, SourceDialog } from './components';

export default function App() {
  const [pageView, setPageView] = useState<'data' | 'runs'>('data');
  const [provider, setProvider] = useState<Provider>('fred');
  const [input, setInput] = useState('');
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const [refresh, setRefresh] = useState(0);
  const [countryRefresh, setCountryRefresh] = useState(0);
  const [selected, setSelected] = useState<SeriesPick>(starters.fred[0]!);
  const [library, setLibrary] = useState(readLibrary);
  const [storageError, setStorageError] = useState('');
  const [country, setCountry] = useState('USA');
  const [guide, setGuide] = useState(false);
  const [importing, setImporting] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const status = useRemote<ProviderStatus>('/api/v1/providers');
  const countries = useRemote<Country[]>(
    provider === 'worldbank' ? '/api/v1/countries' : null,
    countryRefresh,
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
        setPageView('data');
        window.requestAnimationFrame(() => inputRef.current?.focus());
      }
    };
    window.addEventListener('keydown', handle);
    return () => window.removeEventListener('keydown', handle);
  }, []);
  function pick(item: SeriesPick) {
    setSelected(item);
    if (item.provider !== 'local') setProvider(item.provider);
    if (item.country) setCountry(item.country);
    setPageView('data');
  }
  function persist(next: SeriesPick[]) {
    setLibrary(next);
    try {
      localStorage.setItem('policysim.library.v1', JSON.stringify(next));
      setStorageError('');
    } catch {
      setStorageError(
        'Browser storage is unavailable. Saved shortcuts will last for this session.',
      );
    }
  }
  function save(data: Snapshot) {
    const item: SeriesPick = {
      provider: data.series.provider,
      id: data.series.id,
      title: data.series.title,
      source_id: data.series.source_id,
      snapshot_id: data.snapshot_id,
      country: data.country,
    };
    persist(
      [
        item,
        ...library.filter((entry) => entry.snapshot_id !== data.snapshot_id),
      ].slice(0, 30),
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
        Skip to workspace
      </a>
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="PolicySim home">
          <span className="brand-mark">
            <i />
            <i />
            <i />
          </span>
          <span>PolicySim</span>
        </a>
        <nav aria-label="Workspace">
          <button
            className={`nav-item ${pageView === 'data' ? 'active' : ''}`}
            aria-current={pageView === 'data' ? 'page' : undefined}
            onClick={() => setPageView('data')}
          >
            <Icon name="grid" />
            <span>Data</span>
          </button>
          <button
            className={`nav-item ${pageView === 'runs' ? 'active' : ''}`}
            aria-current={pageView === 'runs' ? 'page' : undefined}
            onClick={() => setPageView('runs')}
          >
            <Icon name="forecast" />
            <span>Forecasts</span>
          </button>
        </nav>
        <div className="library-heading">
          <span>Saved data</span>
          <span>{library.length}</span>
        </div>
        <div className="library-list">
          {library.length ? (
            library.map((item) => (
              <div className="library-item" key={pickKey(item)}>
                <button
                  className={
                    selected.snapshot_id === item.snapshot_id &&
                    pageView === 'data'
                      ? 'selected'
                      : ''
                  }
                  onClick={() => pick(item)}
                  title={`${item.title}${item.country ? ` · ${item.country}` : ''}`}
                >
                  <Icon name="chart" size={14} />
                  <span>
                    {item.title}
                    <small>{item.country || names[item.provider]}</small>
                  </span>
                </button>
                <button
                  className="remove-saved icon-button"
                  aria-label={`Remove ${item.title} shortcut`}
                  onClick={() =>
                    persist(
                      library.filter(
                        (entry) => pickKey(entry) !== pickKey(item),
                      ),
                    )
                  }
                >
                  <Icon name="close" size={12} />
                </button>
              </div>
            ))
          ) : (
            <p className="small library-empty">
              Save a series to open it here.
            </p>
          )}
        </div>
        {storageError && (
          <p className="small error-text" role="alert">
            {storageError}
          </p>
        )}
        <div className="sidebar-bottom">
          <button className="nav-item" onClick={() => setImporting(true)}>
            <Icon name="upload" />
            <span>Import CSV</span>
          </button>
          <button className="nav-item" onClick={() => setGuide(true)}>
            <Icon name="globe" />
            <span>Data sources</span>
          </button>
          <div className="connection-status">
            <span className={`status-dot ${status.error ? 'offline' : ''}`} />
            {status.error ? 'Server unavailable' : 'Local workspace'}
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="mobile-brand">PolicySim</div>
          <h1>{pageView === 'data' ? 'Data' : 'Forecasts'}</h1>
          <div className="topbar-actions">
            <div className="mobile-nav">
              <button
                aria-pressed={pageView === 'data'}
                onClick={() => setPageView('data')}
              >
                Data
              </button>
              <button
                aria-pressed={pageView === 'runs'}
                onClick={() => setPageView('runs')}
              >
                Forecasts
              </button>
            </div>
            <button className="secondary" onClick={() => setImporting(true)}>
              <Icon name="upload" size={15} />
              Import CSV
            </button>
            <button
              className="icon-button mobile-help"
              aria-label="Data sources"
              onClick={() => setGuide(true)}
            >
              <Icon name="globe" />
            </button>
          </div>
        </header>
        <main id="main">
          {pageView === 'data' && library.length > 0 && (
            <label className="compact-library">
              Saved data
              <select
                value={selected.snapshot_id ?? ''}
                onChange={(event) => {
                  const item = library.find(
                    (entry) => entry.snapshot_id === event.target.value,
                  );
                  if (item) pick(item);
                }}
              >
                <option value="">Choose a saved series</option>
                {library.map((item) => (
                  <option key={pickKey(item)} value={item.snapshot_id}>
                    {item.title}
                    {item.country ? ` · ${item.country}` : ''}
                  </option>
                ))}
              </select>
            </label>
          )}
          {pageView === 'runs' ? (
            <Runs />
          ) : (
            <div className="explorer-grid">
              <section className="catalog" aria-label="Series catalog">
                <div className="provider-tabs" aria-label="Data provider">
                  {(['fred', 'worldbank', 'bls', 'ecb'] as const).map(
                    (item) => (
                      <button
                        key={item}
                        aria-pressed={provider === item}
                        onClick={() => {
                          setProvider(item);
                          setPage(1);
                          setInput('');
                          setQuery('');
                          setSelected(starters[item][0]!);
                        }}
                      >
                        {names[item]}
                      </button>
                    ),
                  )}
                </div>
                <p className="source-description">
                  {sourceDescriptions[provider]}
                </p>
                <form
                  className="search-form"
                  role="search"
                  onSubmit={(event) => {
                    event.preventDefault();
                    submit(input);
                  }}
                >
                  <Icon name="search" size={16} />
                  <input
                    ref={inputRef}
                    value={input}
                    aria-label={`Search ${names[provider]} series`}
                    placeholder="Search series…"
                    maxLength={200}
                    onChange={(event) => setInput(event.target.value)}
                  />
                  {input ? (
                    <button
                      type="button"
                      className="icon-button"
                      aria-label="Clear search"
                      onClick={() => submit('')}
                    >
                      <Icon name="close" size={14} />
                    </button>
                  ) : (
                    <kbd>Ctrl K</kbd>
                  )}
                  <button
                    type="submit"
                    className="icon-button"
                    aria-label="Search"
                  >
                    <Icon name="arrow" size={16} />
                  </button>
                </form>
                {provider === 'worldbank' && (
                  <div className="country-control">
                    <label htmlFor="country">Country or aggregate</label>
                    <select
                      id="country"
                      value={country}
                      disabled={countries.loading}
                      onChange={(event) => {
                        setCountry(event.target.value);
                        if (selected.provider === 'worldbank')
                          setSelected({
                            ...selected,
                            snapshot_id: undefined,
                            country: event.target.value,
                          });
                      }}
                    >
                      <option value="USA">United States</option>
                      {countries.data
                        ?.filter((item) => item.id !== 'USA')
                        .map((item) => (
                          <option key={item.id} value={item.id}>
                            {item.name}
                            {item.aggregate ? ' (aggregate)' : ''}
                          </option>
                        ))}
                    </select>
                    {countries.loading && (
                      <span className="small" role="status">
                        Loading countries…
                      </span>
                    )}
                    {countries.error && (
                      <Message
                        error={countries.error}
                        retry={() => setCountryRefresh((v) => v + 1)}
                      />
                    )}
                  </div>
                )}
                <div className="catalog-heading">
                  <h2>{query ? 'Search results' : 'Indicators'}</h2>
                  <span className="count">
                    {query
                      ? (search.data?.total.toLocaleString() ?? '…')
                      : list.length}
                  </span>
                </div>
                <div className="result-list" aria-busy={search.loading}>
                  {search.loading ? (
                    <div className="catalog-loading" role="status">
                      <div className="skeleton" />
                      <div className="skeleton" />
                      <p>Searching {names[provider]}…</p>
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
                        key={pickKey(item)}
                        onClick={() => pick(item)}
                      >
                        <strong>{item.title}</strong>
                        <span className="result-meta">
                          <span className="mono">{item.id}</span>
                          {'frequency' in item && (
                            <span>
                              {item.provider === 'worldbank'
                                ? item.source_name
                                : item.frequency}
                            </span>
                          )}
                        </span>
                      </button>
                    ))
                  ) : (
                    <div className="message">
                      <strong>No matching series</strong>
                      <p>Try another keyword or provider.</p>
                      <button className="secondary" onClick={() => submit('')}>
                        Clear search
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
                      disabled={
                        page * search.data.page_size >= search.data.total
                      }
                      onClick={() => setPage((v) => v + 1)}
                    >
                      Next
                    </button>
                  </div>
                )}
                <button
                  className="catalog-source-link text-button"
                  onClick={() => setGuide(true)}
                >
                  <Icon name="globe" size={14} />
                  {names[provider]} source details
                  <Icon name="arrow" size={14} />
                </button>
              </section>
              <Detail
                key={`${pickKey(selected)}-${country}`}
                selected={selected}
                country={country}
                countryName={
                  countries.data?.find((item) => item.id === country)?.name ??
                  country
                }
                save={save}
                library={library}
              />
            </div>
          )}
        </main>
      </div>
      {guide && <SourceDialog close={() => setGuide(false)} />}
      {importing && (
        <ImportDialog
          close={() => setImporting(false)}
          imported={(snapshot) => {
            save(snapshot);
            pick({
              ...snapshot.series,
              snapshot_id: snapshot.snapshot_id,
              country: '',
            });
            setImporting(false);
          }}
        />
      )}
    </div>
  );
}
