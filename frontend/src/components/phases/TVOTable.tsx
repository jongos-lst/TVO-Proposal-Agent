import type { TVOCalculation } from '../../types';
import TVOCharts from './TVOCharts';

interface Props {
  tvo?: TVOCalculation;
  compact?: boolean;
  sessionId?: string;
  productId?: string;
  productName?: string;
}

export default function TVOTable({ tvo, compact, sessionId, productId, productName }: Props) {
  if (!tvo) {
    return (
      <div className="w-full rounded-2xl border border-dashed border-gray-700 bg-gray-800/30 p-10 text-center">
        <p className="text-gray-500 text-sm">TVO calculation will appear here once product recommendation is complete.</p>
      </div>
    );
  }

  if (compact) {
    return (
      <div className="bg-gray-800/50 rounded-lg p-3 space-y-2">
        <div className="text-xs text-gray-500">Total Savings</div>
        <div className="text-green-400 font-bold text-lg">
          ${tvo.tco_savings.toLocaleString()} ({tvo.tco_savings_percent}%)
        </div>
      </div>
    );
  }

  const maxTCO = Math.max(tvo.getac_total_tco, tvo.competitor_total_tco);
  const getacPct = (tvo.getac_total_tco / maxTCO) * 100;
  const compPct = (tvo.competitor_total_tco / maxTCO) * 100;

  return (
    <div className="w-full space-y-6 animate-slide-down">
      {/* Summary Metric Cards */}
      <div className="grid grid-cols-3 gap-4">
        <MetricCard
          label="Total Cost Savings"
          value={`$${tvo.tco_savings.toLocaleString()}`}
          sub={`${tvo.tco_savings_percent}% lower TCO`}
          accent={tvo.tco_savings > 0 ? 'green' : 'red'}
        />
        <MetricCard
          label="Productivity Savings"
          value={`$${tvo.productivity_savings_total.toLocaleString()}`}
          sub={`Over ${tvo.deployment_years} years`}
          accent="blue"
        />
        <MetricCard
          label="Risk Reduction"
          value={`${tvo.risk_reduction_percent}%`}
          sub={`${tvo.competitor_expected_failures.toFixed(0)} → ${tvo.getac_expected_failures.toFixed(0)} failures`}
          accent="purple"
        />
      </div>

      {/* TCO Visual Comparison */}
      <div className="rounded-2xl border border-gray-700/60 bg-gray-800/40 p-5">
        <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">
          Total Cost of Ownership — {tvo.fleet_size} devices over {tvo.deployment_years} years
        </h4>
        <div className="space-y-3">
          <BarRow
            label="Getac"
            value={tvo.getac_total_tco}
            pct={getacPct}
            color="bg-getac-light"
          />
          <BarRow
            label="Competitor"
            value={tvo.competitor_total_tco}
            pct={compPct}
            color="bg-red-400"
          />
        </div>
      </div>

      {/* Cost Breakdown Table */}
      <div className="rounded-2xl border border-gray-700/60 bg-gray-800/40 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-700/50">
          <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Cost Breakdown</h4>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700/50 bg-gray-800/60">
              <th className="text-left px-5 py-3 text-gray-400 font-semibold">Category</th>
              <th className="text-right px-5 py-3 text-getac-light font-semibold">Getac</th>
              <th className="text-right px-5 py-3 text-red-400 font-semibold">Competitor</th>
              <th className="text-right px-5 py-3 text-gray-400 font-semibold">Savings</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800/60">
            {tvo.tco_line_items.map((item, i) => (
              <tr key={i} className="hover:bg-gray-800/40 transition-colors group">
                <td className="px-5 py-3">
                  <div className="text-gray-200 font-medium">{item.label}</div>
                  <div className="text-xs text-gray-500 mt-0.5 hidden group-hover:block">{item.formula}</div>
                </td>
                <td className="text-right px-5 py-3 text-gray-200 font-mono">${item.getac_value.toLocaleString()}</td>
                <td className="text-right px-5 py-3 text-gray-200 font-mono">${item.competitor_value.toLocaleString()}</td>
                <td className={`text-right px-5 py-3 font-mono font-semibold ${item.difference > 0 ? 'text-green-400' : item.difference < 0 ? 'text-red-400' : 'text-gray-400'}`}>
                  {item.difference > 0 ? '+' : ''}${item.difference.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="bg-gray-800/60 border-t border-gray-600">
              <td className="px-5 py-3 font-bold text-white">Total TCO</td>
              <td className="text-right px-5 py-3 font-mono font-bold text-getac-light">${tvo.getac_total_tco.toLocaleString()}</td>
              <td className="text-right px-5 py-3 font-mono font-bold text-red-400">${tvo.competitor_total_tco.toLocaleString()}</td>
              <td className={`text-right px-5 py-3 font-mono font-bold ${tvo.tco_savings > 0 ? 'text-green-400' : 'text-red-400'}`}>
                {tvo.tco_savings > 0 ? '+' : ''}${tvo.tco_savings.toLocaleString()}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Charts */}
      {sessionId && productId && (
        <TVOCharts sessionId={sessionId} productId={productId} productName={productName} />
      )}

      {/* Downtime Comparison */}
      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-2xl border border-gray-700/60 bg-gray-800/40 p-5">
          <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Annual Downtime Hours</h4>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Getac</span>
              <span className="text-lg font-bold text-getac-light">{tvo.getac_annual_downtime_hours}h</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Competitor</span>
              <span className="text-lg font-bold text-red-400">{tvo.competitor_annual_downtime_hours}h</span>
            </div>
          </div>
        </div>
        <div className="rounded-2xl border border-gray-700/60 bg-gray-800/40 p-5">
          <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Expected Device Failures</h4>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Getac ({tvo.deployment_years}yr)</span>
              <span className="text-lg font-bold text-getac-light">{tvo.getac_expected_failures.toFixed(0)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Competitor ({tvo.deployment_years}yr)</span>
              <span className="text-lg font-bold text-red-400">{tvo.competitor_expected_failures.toFixed(0)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Assumptions */}
      {tvo.assumptions.length > 0 && (
        <details className="rounded-2xl border border-gray-700/60 bg-gray-800/30 group">
          <summary className="px-5 py-3 cursor-pointer text-xs font-bold text-gray-500 uppercase tracking-wider hover:text-gray-300 transition-colors">
            Assumptions & Methodology ({tvo.assumptions.length})
          </summary>
          <div className="px-5 pb-4 space-y-1">
            {tvo.assumptions.map((a, i) => (
              <div key={i} className="text-xs text-gray-500 flex items-start gap-2">
                <span className="text-gray-600 mt-px">&#x2022;</span>
                <span>{a}</span>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}

/* ---------- Sub-components ---------- */

function MetricCard({ label, value, sub, accent }: { label: string; value: string; sub: string; accent: string }) {
  const borderColor = {
    green: 'border-green-500/30',
    red: 'border-red-500/30',
    blue: 'border-getac-light/30',
    purple: 'border-purple-500/30',
  }[accent] || 'border-gray-700/60';

  const valueColor = {
    green: 'text-green-400',
    red: 'text-red-400',
    blue: 'text-getac-light',
    purple: 'text-purple-400',
  }[accent] || 'text-white';

  return (
    <div className={`rounded-2xl border ${borderColor} bg-gray-800/40 p-5 text-center`}>
      <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">{label}</div>
      <div className={`text-2xl font-bold ${valueColor}`}>{value}</div>
      <div className="text-xs text-gray-500 mt-1">{sub}</div>
    </div>
  );
}

function BarRow({ label, value, pct, color }: { label: string; value: number; pct: number; color: string }) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-300 font-medium">{label}</span>
        <span className="text-gray-200 font-mono font-semibold">${value.toLocaleString()}</span>
      </div>
      <div className="w-full bg-gray-700/40 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all duration-700`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
