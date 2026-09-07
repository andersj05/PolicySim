import { useEffect, useRef, useState } from 'react';
import type { Observation } from './api.generated';
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
}: {
  observations: Observation[];
  title: string;
}) {
  const [hover, setHover] = useState<number | null>(null);
  const container = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(780);
  useEffect(() => {
    if (!container.current) return;
    const observer = new ResizeObserver(([entry]) => {
      if (entry) setWidth(Math.max(240, entry.contentRect.width));
    });
    observer.observe(container.current);
    return () => observer.disconnect();
  }, [observations.length]);
  const values = observations
    .filter((row) => row.value !== null)
    .map((row) => row.value!);
  if (!values.length)
    return (
      <div className="empty-chart">
        No numeric observations in this date range.
        <br />
        <span>Try a different country or time period.</span>
      </div>
    );
  const times = observations.map((row) => timestamp(row.date));
  if (times.some((value) => !Number.isFinite(value)))
    return (
      <div className="empty-chart">
        This provider uses a nonstandard time format.
        <br />
        <span>Open the table to inspect the original observations.</span>
      </div>
    );
  const min = values.reduce((a, b) => Math.min(a, b)),
    max = values.reduce((a, b) => Math.max(a, b));
  const padding = (max - min || Math.abs(max) || 1) * 0.12;
  const lower = min - padding,
    upper = max + padding;
  const x = (index: number) =>
    12 +
    ((times[index]! - times[0]!) / (times.at(-1)! - times[0]! || 1)) *
      (width - 90);
  const y = (value: number) => 218 - ((value - lower) / (upper - lower)) * 202;
  const path = observations
    .map((row, index) => {
      if (row.value === null) {
        return '';
      }
      return `${index > 0 && observations[index - 1]?.value !== null ? 'L' : 'M'}${x(index)},${y(row.value)}`;
    })
    .join(' ');
  const point = hover === null ? undefined : observations[hover];
  return (
    <div className="chart-wrap" ref={container}>
      <div className="chart-readout" aria-live="off">
        {point ? (
          <>
            <strong>{formatValue(point.value)}</strong>
            <span>
              {point.date}
              {point.value === null ? ' · Missing observation' : ''}
            </span>
          </>
        ) : (
          <span>Move across the chart to inspect observations</span>
        )}
      </div>
      <svg
        viewBox={`0 0 ${width} 268`}
        role="img"
        aria-label={`${title}. ${observations.length} observations. Exact values are available in the table.`}
        onPointerLeave={() => setHover(null)}
        onPointerMove={(event) => {
          const bounds = event.currentTarget.getBoundingClientRect();
          const position =
            (((event.clientX - bounds.left) / bounds.width) * width - 12) /
            (width - 90);
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
        {[0, 1, 2, 3].map((i) => {
          const value = lower + ((upper - lower) * i) / 3;
          return (
            <g key={i}>
              <line
                className="grid-line"
                x1="12"
                x2={width - 78}
                y1={y(value)}
                y2={y(value)}
              />
              <text x={width - 65} y={y(value) + 4}>
                {formatValue(value, true)}
              </text>
            </g>
          );
        })}
        <path
          d={path}
          fill="none"
          stroke="var(--accent)"
          strokeWidth="2.4"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        {observations.map((row, index) =>
          row.value !== null &&
          (index === 0 || observations[index - 1]?.value === null) &&
          (index === observations.length - 1 ||
            observations[index + 1]?.value === null) ? (
            <circle
              key={row.date}
              cx={x(index)}
              cy={y(row.value)}
              r="3"
              fill="var(--accent)"
            />
          ) : null,
        )}
        {point && hover !== null && (
          <g>
            <line
              x1={x(hover)}
              x2={x(hover)}
              y1="12"
              y2="220"
              className="crosshair"
            />
            {point.value !== null && (
              <circle
                cx={x(hover)}
                cy={y(point.value)}
                r="5"
                fill="var(--accent)"
                stroke="white"
                strokeWidth="2"
              />
            )}
          </g>
        )}
        {[0, Math.floor((observations.length - 1) / 2), observations.length - 1]
          .filter((v, i, a) => a.indexOf(v) === i && (width >= 500 || i !== 1))
          .map((index, i) => (
            <text
              key={index}
              x={x(index)}
              y="253"
              textAnchor={
                i === 0
                  ? 'start'
                  : index === observations.length - 1
                    ? 'end'
                    : 'middle'
              }
            >
              {observations[index]?.date}
            </text>
          ))}
      </svg>
    </div>
  );
}
