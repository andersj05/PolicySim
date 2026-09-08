import { useEffect, useState } from 'react';
import type {
  ForecastReadiness as Readiness,
  ForecastRequest,
} from './api.generated';
import { post } from './api';
import { Icon } from './components';

export default function ForecastReadiness({
  request,
  applyRange,
}: {
  request: ForecastRequest;
  applyRange: (start: string, end: string) => void;
}) {
  const key = JSON.stringify(request);
  const [response, setResponse] = useState<{
    key: string;
    data?: Readiness;
    error?: string;
  }>();
  useEffect(() => {
    let active = true;
    const timer = window.setTimeout(() => {
      void post<Readiness>('/api/v1/forecast-readiness', JSON.parse(key)).then(
        (data) => {
          if (active) setResponse({ key, data });
        },
        (problem: unknown) => {
          if (active)
            setResponse({
              key,
              error:
                problem instanceof Error
                  ? problem.message
                  : 'Unable to check this selection.',
            });
        },
      );
    }, 250);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [key]);
  const result = response?.key === key ? response : undefined;
  return (
    <div
      className={`readiness ${result?.data?.ready ? 'ready' : ''}`}
      role="status"
    >
      <Icon name="chart" size={17} />
      <div>
        <strong>
          {!result
            ? 'Checking selected history…'
            : result.data?.ready
              ? 'Ready to evaluate'
              : 'Review selected history'}
        </strong>
        {result?.data && (
          <>
            <span>
              {result.data.periods} periods · {result.data.required_periods}{' '}
              minimum · {result.data.missing_periods} missing before edge
              trimming
            </span>
            {!result.data.ready && <p>{result.data.message}</p>}
            {result.data.ready && (
              <p>
                Calendar and sample checks passed. Individual model fits may
                still fail.
              </p>
            )}
            {result.data.suggested_start && (
              <button
                type="button"
                className="secondary"
                onClick={() =>
                  applyRange(
                    result.data!.suggested_start,
                    result.data!.suggested_end,
                  )
                }
              >
                Use complete segment: {result.data.suggested_start} →{' '}
                {result.data.suggested_end}
              </button>
            )}
          </>
        )}
        {result?.error && <p>{result.error}</p>}
      </div>
    </div>
  );
}
