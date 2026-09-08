import { useEffect, useRef, useState } from 'react';
import type { CsvImportRequest, CsvPreview, Snapshot } from './api.generated';
import { post } from './api';
import { Icon } from './components';

export default function ImportDialog({
  close,
  imported,
}: {
  close: () => void;
  imported: (data: Snapshot) => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const active = useRef<AbortController | null>(null);
  const [content, setContent] = useState('');
  const [preview, setPreview] = useState<CsvPreview>();
  const [title, setTitle] = useState('');
  const [dateColumn, setDateColumn] = useState('');
  const [valueColumn, setValueColumn] = useState('');
  const [units, setUnits] = useState('Value');
  const [frequency, setFrequency] =
    useState<CsvImportRequest['frequency']>('monthly');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    dialog.current?.showModal();
    return () => active.current?.abort();
  }, []);
  async function load(file: File) {
    active.current?.abort();
    const controller = new AbortController();
    active.current = controller;
    setBusy(true);
    setError('');
    setPreview(undefined);
    try {
      if (file.size > 2_000_000)
        throw new Error('Choose a CSV smaller than 2 MB.');
      const text = await file.text();
      if (controller.signal.aborted) return;
      const result = await post<CsvPreview>(
        '/api/v1/imports/preview',
        { content: text },
        controller.signal,
      );
      if (controller.signal.aborted) return;
      setContent(text);
      setPreview(result);
      setTitle(file.name.replace(/\.csv$/i, ''));
      setDateColumn(
        result.columns.find((col) => /date|time|year/i.test(col)) ??
          result.columns[0]!,
      );
      setValueColumn(
        result.columns.find((col) => /value|observation/i.test(col)) ??
          result.columns[1] ??
          result.columns[0]!,
      );
    } catch (problem) {
      if (!controller.signal.aborted)
        setError(
          problem instanceof Error ? problem.message : 'Cannot read this file.',
        );
    } finally {
      if (!controller.signal.aborted) setBusy(false);
    }
  }
  async function submit() {
    const controller = new AbortController();
    active.current = controller;
    setBusy(true);
    setError('');
    try {
      const snapshot = await post<Snapshot>(
        '/api/v1/imports',
        {
          content,
          title,
          date_column: dateColumn,
          value_column: valueColumn,
          frequency,
          units,
        },
        controller.signal,
      );
      if (!controller.signal.aborted) imported(snapshot);
    } catch (problem) {
      if (!controller.signal.aborted)
        setError(problem instanceof Error ? problem.message : 'Import failed.');
    } finally {
      if (!controller.signal.aborted) setBusy(false);
    }
  }
  return (
    <dialog
      ref={dialog}
      className="import-dialog"
      onCancel={close}
      aria-labelledby="import-title"
    >
      <div className="dialog-heading">
        <h2 id="import-title">Import CSV</h2>
        <button
          className="icon-button"
          onClick={close}
          aria-label="Close import"
        >
          <Icon name="close" />
        </button>
      </div>
      <label className="file-drop">
        <Icon name="upload" size={24} />
        <strong>{preview ? 'Choose another file' : 'Choose a CSV file'}</strong>
        <span>UTF-8 · Comma-separated · Up to 2 MB</span>
        <input
          type="file"
          accept=".csv,text/csv"
          disabled={busy}
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) void load(file);
          }}
        />
      </label>
      {error && (
        <p className="notice error" role="alert">
          {error}
        </p>
      )}
      {busy && (
        <p className="small" role="status">
          {preview ? 'Saving data…' : 'Reading file…'}
        </p>
      )}
      {preview && (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void submit();
          }}
        >
          <fieldset disabled={busy}>
            <label>
              Series name
              <input
                value={title}
                maxLength={160}
                required
                onChange={(event) => setTitle(event.target.value)}
              />
            </label>
            <div className="form-grid">
              <label>
                Date column
                <select
                  value={dateColumn}
                  onChange={(event) => setDateColumn(event.target.value)}
                >
                  {preview.columns.map((col) => (
                    <option key={col}>{col}</option>
                  ))}
                </select>
              </label>
              <label>
                Value column
                <select
                  value={valueColumn}
                  onChange={(event) => setValueColumn(event.target.value)}
                >
                  {preview.columns.map((col) => (
                    <option key={col}>{col}</option>
                  ))}
                </select>
              </label>
              <label>
                Frequency
                <select
                  value={frequency}
                  onChange={(event) =>
                    setFrequency(
                      event.target.value as CsvImportRequest['frequency'],
                    )
                  }
                >
                  {['annual', 'quarterly', 'monthly', 'weekly', 'daily'].map(
                    (freq) => (
                      <option key={freq} value={freq}>
                        {freq[0]!.toUpperCase() + freq.slice(1)}
                      </option>
                    ),
                  )}
                </select>
              </label>
              <label>
                Units
                <input
                  value={units}
                  maxLength={160}
                  required
                  onChange={(event) => setUnits(event.target.value)}
                />
              </label>
            </div>
            <div className="section-label">
              Preview <span>{preview.count.toLocaleString()} rows</span>
            </div>
            <div className="table-region">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.rows.map((row, index) => (
                    <tr key={index}>
                      <td>{row[preview.columns.indexOf(dateColumn)]}</td>
                      <td>
                        {row[preview.columns.indexOf(valueColumn)] || (
                          <span className="muted">Missing</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="small import-note">
              Use YYYY, YYYY-MM, YYYYQ1 or YYYY-MM-DD dates. Blank, NA, N/A,
              null and “.” values stay missing. Rows are sorted by date;
              duplicate periods are rejected.
            </p>
            <div className="dialog-actions">
              <button type="button" className="secondary" onClick={close}>
                Cancel
              </button>
              <button
                type="submit"
                className="primary"
                disabled={dateColumn === valueColumn}
              >
                Load data
                <Icon name="arrow" size={15} />
              </button>
            </div>
          </fieldset>
        </form>
      )}
    </dialog>
  );
}
