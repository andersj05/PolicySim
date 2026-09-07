import { useState } from 'react';
import type { Observation } from './api.generated';
import { formatValue } from './format';

export default function DataTable({
  observations,
  title,
  units,
}: {
  observations: Observation[];
  title: string;
  units: string;
}) {
  const [sort, setSort] = useState<'date' | 'value'>('date');
  const [ascending, setAscending] = useState(false);
  const [missingOnly, setMissingOnly] = useState(false);
  const [page, setPage] = useState(0);
  const [size, setSize] = useState(20);
  const rows = observations
    .filter((row) => !missingOnly || row.value === null)
    .slice()
    .sort((a, b) => {
      if (sort === 'value' && (a.value === null || b.value === null))
        return a.value === null ? (b.value === null ? 0 : 1) : -1;
      const order =
        sort === 'date' ? a.date.localeCompare(b.date) : a.value! - b.value!;
      return ascending ? order : -order;
    });
  const current = Math.min(
    page,
    Math.max(0, Math.ceil(rows.length / size) - 1),
  );
  function order(field: 'date' | 'value') {
    setSort(field);
    setAscending(field === sort ? !ascending : false);
    setPage(0);
  }
  return (
    <div className="data-table">
      <div className="table-tools">
        <label className="checkbox">
          <input
            type="checkbox"
            checked={missingOnly}
            onChange={(event) => {
              setMissingOnly(event.target.checked);
              setPage(0);
            }}
          />
          Missing only
        </label>
        <label className="inline-label">
          Rows
          <select
            value={size}
            onChange={(event) => {
              setSize(Number(event.target.value));
              setPage(0);
            }}
          >
            {[20, 50, 100].map((n) => (
              <option key={n}>{n}</option>
            ))}
          </select>
        </label>
      </div>
      <div className="table-region">
        <table>
          <caption className="sr-only">
            {title} · {units}
          </caption>
          <thead>
            <tr>
              <th
                aria-sort={
                  sort === 'date'
                    ? ascending
                      ? 'ascending'
                      : 'descending'
                    : 'none'
                }
              >
                <button onClick={() => order('date')}>
                  Date {sort === 'date' ? (ascending ? '↑' : '↓') : '↕'}
                </button>
              </th>
              <th
                aria-sort={
                  sort === 'value'
                    ? ascending
                      ? 'ascending'
                      : 'descending'
                    : 'none'
                }
              >
                <button onClick={() => order('value')}>
                  {units} {sort === 'value' ? (ascending ? '↑' : '↓') : '↕'}
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(current * size, (current + 1) * size).map((row) => (
              <tr key={row.date}>
                <td>{row.date}</td>
                <td>
                  {row.value === null ? (
                    <span className="missing-value">Missing</span>
                  ) : (
                    <span title={String(row.value)}>
                      {formatValue(row.value)}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!rows.length && (
        <div className="empty-inline">
          {missingOnly
            ? 'No missing values in this range.'
            : 'No observations in this range.'}
        </div>
      )}
      <div className="pagination">
        <button disabled={current === 0} onClick={() => setPage(current - 1)}>
          Previous
        </button>
        <span>
          {rows.length ? current * size + 1 : 0}–
          {Math.min((current + 1) * size, rows.length)} of{' '}
          {rows.length.toLocaleString()}
        </span>
        <button
          disabled={(current + 1) * size >= rows.length}
          onClick={() => setPage(current + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
