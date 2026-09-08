import { useEffect, useRef, useState } from 'react';
import type { ForecastPoint, Observation } from './api.generated';
import { formatValue } from './format';

function timestamp(label: string): number {
  if (/^\d{4}$/.test(label)) return Date.UTC(Number(label), 0);
  const quarter = /^(\d{4})Q([1-4])$/.exec(label);
  if (quarter)
    return Date.UTC(Number(quarter[1]), (Number(quarter[2]) - 1) * 3);
  const month = /^(\d{4})M(\d{2})$/.exec(label);
  if (month) return Date.UTC(Number(month[1]), Number(month[2]) - 1);
  return Date.parse(label);
}

export default function Chart({
  observations,
  title,
  forecast = [],
  comparison = [],
  interval = 95,
}: {
  observations: Observation[];
  title: string;
  forecast?: ForecastPoint[];
  comparison?: ForecastPoint[];
  interval?: number;
}) {
  const [hover, setHover] = useState<number | null>(null);
  const container = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(780);
  useEffect(() => {
    if (!container.current) return;
    const observer = new ResizeObserver(([entry]) => {
      if (entry) setWidth(Math.max(220, entry.contentRect.width));
    });
    observer.observe(container.current);
    return () => observer.disconnect();
  }, [observations.length]);
  const all = [...observations, ...forecast];
  const values = [
    ...all.flatMap((row) => (row.value === null ? [] : [row.value])),
    ...forecast.flatMap((row) => [row.lower, row.upper]),
    ...comparison.flatMap((row) => [row.value, row.lower, row.upper]),
  ];
  if (!values.length)
    return (
      <div className="empty-chart">No numeric observations in this range.</div>
    );
  const times = all.map((row) => timestamp(row.date));
  if (times.some((value) => !Number.isFinite(value)))
    return (
      <div className="empty-chart">
        This date format cannot be plotted. Open the table to inspect it.
      </div>
    );
  const min = values.reduce((a, b) => Math.min(a, b));
  const max = values.reduce((a, b) => Math.max(a, b));
  const padding = (max - min || Math.abs(max) || 1) * 0.12;
  const lower = min - padding,
    upper = max + padding;
  const right = width - (width < 440 ? 65 : 82);
  const x = (index: number) =>
    8 +
    ((times[index]! - times[0]!) / (times.at(-1)! - times[0]! || 1)) *
      (right - 8);
  const y = (value: number) => 254 - ((value - lower) / (upper - lower)) * 230;
  const path = observations
    .map((row, index) =>
      row.value === null
        ? ''
        : `${index > 0 && observations[index - 1]?.value !== null ? 'L' : 'M'}${x(index)},${y(row.value)}`,
    )
    .join(' ');
  const origin = observations.length - 1;
  const finalObserved = observations.at(-1)?.value;
  const forecastPath =
    (finalObserved != null ? `M${x(origin)},${y(finalObserved)} ` : '') +
    forecast
      .map(
        (row, index) =>
          `${index || finalObserved != null ? 'L' : 'M'}${x(observations.length + index)},${y(row.value)}`,
      )
      .join(' ');
  const band = forecast.length
    ? `M${x(origin)},${y(finalObserved ?? forecast[0]!.value)} ` +
      forecast
        .map(
          (row, index) => `L${x(observations.length + index)},${y(row.upper)}`,
        )
        .join(' ') +
      ' ' +
      [...forecast]
        .reverse()
        .map((row, index) => `L${x(all.length - 1 - index)},${y(row.lower)}`)
        .join(' ') +
      ' Z'
    : '';
  const point = hover === null ? undefined : all[hover];
  const comparisonX = (row: ForecastPoint) =>
    x(all.findIndex((item) => item.date === row.date));
  const comparisonPath = comparison
    .map((row, i) => `${i ? 'L' : 'M'}${comparisonX(row)},${y(row.value)}`)
    .join(' ');
  const comparisonBand = comparison.length
    ? comparison
        .map((row, i) => `${i ? 'L' : 'M'}${comparisonX(row)},${y(row.upper)}`)
        .join(' ') +
      ' ' +
      [...comparison]
        .reverse()
        .map((row) => `L${comparisonX(row)},${y(row.lower)}`)
        .join(' ') +
      ' Z'
    : '';
  const compared = point
    ? comparison.find((row) => row.date === point.date)
    : undefined;
  const future =
    hover !== null && hover >= observations.length
      ? forecast[hover - observations.length]
      : undefined;
  const indices = [0, Math.floor((all.length - 1) / 2), all.length - 1].filter(
    (v, i, a) => a.indexOf(v) === i && (width >= 500 || i !== 1),
  );
  return (
    <div className="chart-wrap" ref={container}>
      <div className="chart-readout" aria-live="off">
        {point ? (
          <>
            <strong>{formatValue(point.value)}</strong>
            <span>
              {point.date}
              {future
                ? ' · Forecast'
                : point.value === null
                  ? ' · Missing'
                  : ''}
            </span>
            {future && (
              <span className="readout-interval">
                {interval}%: {formatValue(future.lower)}–
                {formatValue(future.upper)}
              </span>
            )}
            {compared && (
              <span className="readout-interval">
                Predicted: {formatValue(compared.value)}
              </span>
            )}
          </>
        ) : (
          <span>Hover or use arrow keys to inspect</span>
        )}
      </div>
      <svg
        viewBox={`0 0 ${width} 302`}
        role="img"
        tabIndex={0}
        aria-label={`${title}. ${observations.length} observations${forecast.length ? ` and ${forecast.length} forecast periods with ${interval}% prediction intervals` : ''}${comparison.length ? ` compared with holdout predictions and ${interval}% intervals` : ''}. Use arrow keys to inspect; exact values are in the table.`}
        onBlur={() => setHover(null)}
        onKeyDown={(event) => {
          if (['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) {
            event.preventDefault();
            setHover(
              event.key === 'Home'
                ? 0
                : event.key === 'End'
                  ? all.length - 1
                  : Math.min(
                      all.length - 1,
                      Math.max(
                        0,
                        (hover ?? all.length - 1) +
                          (event.key === 'ArrowLeft' ? -1 : 1),
                      ),
                    ),
            );
          }
        }}
        onPointerLeave={() => setHover(null)}
        onPointerMove={(event) => {
          const bounds = event.currentTarget.getBoundingClientRect();
          const position =
            (((event.clientX - bounds.left) / bounds.width) * width - 8) /
            (right - 8);
          const target = times[0]! + position * (times.at(-1)! - times[0]!);
          let nearest = 0;
          for (let i = 1; i < times.length; i++)
            if (
              Math.abs(times[i]! - target) < Math.abs(times[nearest]! - target)
            )
              nearest = i;
          setHover(nearest);
        }}
      >
        {forecast.length > 0 && (
          <>
            <rect
              x={x(origin)}
              y={12}
              width={Math.max(0, right - x(origin))}
              height={252}
              fill="var(--forecast-tint)"
            />
            <line
              x1={x(origin)}
              x2={x(origin)}
              y1={14}
              y2={264}
              stroke="var(--forecast)"
              strokeOpacity=".35"
              strokeDasharray="3 5"
            />
            {right - x(origin) > 75 && (
              <text x={x(origin) + 10} y={20} className="forecast-label">
                Forecast
              </text>
            )}
          </>
        )}
        {[0, 1, 2, 3, 4].map((i) => {
          const value = lower + ((upper - lower) * i) / 4;
          return (
            <g key={i}>
              <line
                className="grid-line"
                x1={8}
                x2={right}
                y1={y(value)}
                y2={y(value)}
              />
              <text x={right + 12} y={y(value) + 4}>
                {formatValue(value, true)}
              </text>
            </g>
          );
        })}
        {band && <path d={band} fill="var(--forecast)" fillOpacity=".13" />}
        {comparisonBand && (
          <path d={comparisonBand} fill="var(--forecast)" fillOpacity=".13" />
        )}
        {comparisonPath && (
          <path
            d={comparisonPath}
            fill="none"
            stroke="var(--forecast)"
            strokeWidth="2.3"
            strokeDasharray="5 4"
          />
        )}
        <path
          d={path}
          fill="none"
          stroke="var(--accent)"
          strokeWidth="2.3"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        {forecast.length > 0 && (
          <path
            d={forecastPath}
            fill="none"
            stroke="var(--forecast)"
            strokeWidth="2.3"
            strokeDasharray="5 4"
            strokeLinejoin="round"
          />
        )}
        {observations.map((row, index) =>
          row.value !== null &&
          (index === 0 || observations[index - 1]?.value === null) &&
          (index === observations.length - 1 ||
            observations[index + 1]?.value === null) ? (
            <circle
              key={row.date}
              cx={x(index)}
              cy={y(row.value)}
              r={3}
              fill="var(--accent)"
            />
          ) : null,
        )}
        {point && hover !== null && (
          <g>
            <line
              x1={x(hover)}
              x2={x(hover)}
              y1={14}
              y2={264}
              className="crosshair"
            />
            {point.value !== null && (
              <circle
                cx={x(hover)}
                cy={y(point.value)}
                r={4.5}
                fill={future ? 'var(--forecast)' : 'var(--accent)'}
                stroke="white"
                strokeWidth={2}
              />
            )}
          </g>
        )}
        {indices.map((index, i) => (
          <text
            key={index}
            x={x(index)}
            y={289}
            textAnchor={
              i === 0 ? 'start' : index === all.length - 1 ? 'end' : 'middle'
            }
          >
            {all[index]?.date}
          </text>
        ))}
      </svg>
    </div>
  );
}
