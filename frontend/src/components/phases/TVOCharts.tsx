import { useState } from 'react';
import { getChartUrl } from '../../api/client';

interface Props {
  sessionId: string;
  productId: string;
  productName?: string;
}

// Full-width analytical charts
const WIDE_CHARTS_TOP = [
  { key: 'tco_comparison', label: 'TCO Comparison' },
];

// Compact metric charts in a 3-column row
const COMPACT_CHARTS = [
  { key: 'total_tco', label: 'Total Cost of Ownership' },
  { key: 'savings_breakdown', label: 'Savings Breakdown' },
  { key: 'risk_gauge', label: 'Risk Reduction' },
];

// Full-width analytical charts (bottom)
const WIDE_CHARTS_BOTTOM = [
  { key: 'roi_timeline', label: 'ROI Timeline' },
  { key: 'cost_waterfall', label: 'Cumulative Cost' },
  { key: 'productivity', label: 'Productivity Impact' },
];

function ChartCard({ chartKey, label, sessionId, productId }: { chartKey: string; label: string; sessionId: string; productId: string }) {
  return (
    <div className="rounded-2xl border border-gray-700/60 bg-gray-800/40 p-3 overflow-hidden">
      <div className="text-xs text-gray-500 mb-2 font-medium">{label}</div>
      <ChartImage
        src={getChartUrl(sessionId, productId, chartKey)}
        alt={label}
      />
    </div>
  );
}

export default function TVOCharts({ sessionId, productId, productName }: Props) {
  return (
    <div className="space-y-4">
      <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">
        {productName ? `Charts \u2014 ${productName}` : 'Charts'}
      </h4>

      {/* Full-width: TCO Comparison */}
      {WIDE_CHARTS_TOP.map(({ key, label }) => (
        <ChartCard key={key} chartKey={key} label={label} sessionId={sessionId} productId={productId} />
      ))}

      {/* 3-column row: Total TCO, Savings Breakdown, Risk Gauge */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {COMPACT_CHARTS.map(({ key, label }) => (
          <ChartCard key={key} chartKey={key} label={label} sessionId={sessionId} productId={productId} />
        ))}
      </div>

      {/* Full-width: ROI Timeline, Cumulative Cost, Productivity */}
      {WIDE_CHARTS_BOTTOM.map(({ key, label }) => (
        <ChartCard key={key} chartKey={key} label={label} sessionId={sessionId} productId={productId} />
      ))}
    </div>
  );
}

function ChartImage({ src, alt }: { src: string; alt: string }) {
  const [error, setError] = useState(false);

  if (error) {
    return (
      <div className="w-full h-32 rounded-lg bg-gray-800 flex items-center justify-center">
        <span className="text-xs text-gray-600">Chart unavailable</span>
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={alt}
      className="w-full rounded-lg bg-white"
      loading="lazy"
      onError={() => setError(true)}
    />
  );
}
