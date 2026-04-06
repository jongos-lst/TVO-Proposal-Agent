import type { CustomerPersona } from '../../types';

interface Props {
  persona?: CustomerPersona;
  compact?: boolean;
}

export default function IntakeSummary({ persona, compact }: Props) {
  if (!persona) return null;

  const fields = [
    { label: 'Customer', value: persona.customer_name, icon: '&#x1F3E2;' },
    { label: 'Industry', value: persona.industry, icon: '&#x1F3ED;' },
    { label: 'Pain Points', value: persona.pain_points, icon: '&#x26A0;' },
    { label: 'Use Scenarios', value: persona.use_scenarios, icon: '&#x1F4CB;' },
    { label: 'Budget', value: persona.budget_amount ? `$${persona.budget_amount.toLocaleString()}` : undefined, icon: '&#x1F4B0;' },
    { label: 'Warranty Needs', value: persona.service_warranty_needs, icon: '&#x1F6E1;' },
    { label: 'Current Devices', value: persona.current_devices, icon: '&#x1F4BB;' },
    { label: 'Fleet Size', value: persona.fleet_size ? `${persona.fleet_size} devices` : undefined, icon: '&#x1F4E6;' },
    { label: 'Timeline', value: persona.deployment_timeline, icon: '&#x1F4C5;' },
  ];

  const filled = fields.filter(f => {
    if (Array.isArray(f.value)) return f.value.length > 0;
    return !!f.value;
  });

  if (filled.length === 0) return null;

  if (compact) {
    return (
      <div className="bg-gray-800/50 rounded-lg p-3 space-y-1">
        <div className="text-xs font-semibold text-gray-400 uppercase">Customer</div>
        <div className="text-sm text-white font-medium">{persona.customer_name || 'Unknown'}</div>
        <div className="text-xs text-gray-500">{persona.industry}</div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-gray-700/60 bg-gray-800/40 overflow-hidden animate-slide-down">
      <div className="px-5 py-4 border-b border-gray-700/50">
        <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Customer Profile</h4>
      </div>
      <div className="divide-y divide-gray-800/60">
        {filled.map(({ label, value, icon }) => (
          <div key={label} className="flex items-start gap-3 px-5 py-3 hover:bg-gray-800/40 transition-colors">
            <span className="text-base mt-0.5 shrink-0 w-6 text-center" dangerouslySetInnerHTML={{ __html: icon }} />
            <div className="flex-1 min-w-0">
              <div className="text-xs text-gray-500 mb-0.5">{label}</div>
              {Array.isArray(value) ? (
                <div className="flex flex-wrap gap-1.5">
                  {value.map((v, i) => (
                    <span key={i} className="text-xs px-2 py-0.5 rounded bg-gray-700/60 text-gray-300">{v}</span>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-gray-200">{value}</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
