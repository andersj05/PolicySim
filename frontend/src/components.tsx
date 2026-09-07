import { useEffect, useRef } from 'react';

export function Icon({
  name,
  size = 18,
}: {
  name:
    | 'search'
    | 'grid'
    | 'globe'
    | 'arrow'
    | 'download'
    | 'chart'
    | 'table'
    | 'plus'
    | 'close'
    | 'book'
    | 'chevron';
  size?: number;
}) {
  const paths = {
    search: 'm21 21-5-5 M19 11a8 8 0 1 1-16 0 8 8 0 0 1 16 0',
    grid: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
    globe:
      'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0 M3 12h18 M12 3c-5 5-5 13 0 18 M12 3c5 5 5 13 0 18',
    arrow: 'M5 12h14 m-5-5 5 5-5 5',
    download: 'M12 3v12 m-5-5 5 5 5-5 M4 16v5h16v-5',
    chart: 'M3 3v18h18 M6 15l4-5 4 3 6-8',
    table: 'M3 4h18v16H3z M3 9h18 M9 4v16',
    plus: 'M12 5v14 M5 12h14',
    close: 'm6 6 12 12 M6 18 18 6',
    book: 'M4 4h6l2 2 2-2h6v16h-6l-2 2-2-2H4z M12 6v16',
    chevron: 'm9 5 7 7-7 7',
  };
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={paths[name]} />
    </svg>
  );
}

export function Message({
  error,
  retry,
}: {
  error: string;
  retry: () => void;
}) {
  return (
    <div className="message error" role="alert">
      <strong>We couldn’t load this data</strong>
      <p>{error}</p>
      <button className="secondary" onClick={retry}>
        Try again <Icon name="arrow" size={15} />
      </button>
    </div>
  );
}

export function SourceDialog({ close }: { close: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    ref.current?.showModal();
  }, []);
  return (
    <dialog
      ref={ref}
      aria-labelledby="guide-title"
      onCancel={close}
      onClick={(event) => {
        if (event.target === event.currentTarget) close();
      }}
    >
      <div className="dialog-heading">
        <span className="eyebrow">WORKSPACE GUIDE</span>
        <button
          className="icon-button"
          aria-label="Close source guide"
          onClick={close}
        >
          <Icon name="close" />
        </button>
      </div>
      <h2 id="guide-title">
        Good research starts
        <br />
        with a clear source.
      </h2>
      <p>
        Search by keyword or indicator code. Select a series to retrieve its
        original observations and save a local source snapshot.
      </p>
      <div className="guide-source">
        <strong>FRED</strong>
        <p>
          Economic time series from the Federal Reserve Bank of St. Louis and
          its data contributors. Your API key stays on the backend.
        </p>
        <a href="https://fred.stlouisfed.org/" target="_blank" rel="noreferrer">
          Explore FRED ↗
        </a>
      </div>
      <div className="guide-source">
        <strong>World Bank</strong>
        <p>
          Search the Indicators API catalog across databases. Select a country
          or aggregate before loading observations. No key required.
        </p>
        <a href="https://data.worldbank.org/" target="_blank" rel="noreferrer">
          Explore World Bank ↗
        </a>
      </div>
      <p className="small">
        Data reflects the latest provider revision. Missing values remain
        missing. This workspace does not yet run simulations or vintage-correct
        backtests.
      </p>
    </dialog>
  );
}
