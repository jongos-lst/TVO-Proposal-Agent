import { useState, useEffect } from 'react';
import type { CalculationParams, ProductCalcParams, ProposalState, CompetitorProduct } from '../../types';
import { fetchCompetitors } from '../../api/client';

interface Props {
  proposal: ProposalState;
  onConfirm: (params: CalculationParams) => void;
  onBack: () => void;
  isSubmitting: boolean;
}

export default function ConfirmationPanel({ proposal, onConfirm, onBack, isSubmitting }: Props) {
  const [fleetSize, setFleetSize] = useState(proposal.persona?.fleet_size || 100);
  const [deploymentYears, setDeploymentYears] = useState(5);
  const [hourlyProductivityValue, setHourlyProductivityValue] = useState(50.0);
  const [avgDowntimeHours, setAvgDowntimeHours] = useState(16.0);
  const [annualRepairCost, setAnnualRepairCost] = useState(450.0);
  const [productParams, setProductParams] = useState<ProductCalcParams[]>([]);
  const [competitors, setCompetitors] = useState<CompetitorProduct[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Fetch competitors on mount
  useEffect(() => {
    fetchCompetitors()
      .then(setCompetitors)
      .catch(() => setCompetitors([]));
  }, []);

  // Initialize product params from proposal data + competitors
  useEffect(() => {
    if (!proposal.selectedProducts?.length) return;

    const params: ProductCalcParams[] = proposal.selectedProducts.map((product) => {
      const competitorName = proposal.competitorProductNames?.[product.id] || '';
      const comp = competitors.find(c =>
        competitorName && c.name.toLowerCase().includes(competitorName.split(' ')[0].toLowerCase())
      );

      // Extract feature flags from product data
      const features = product.key_features || [];
      const hasHotSwap = features.some(f => f.toLowerCase().includes('hot-swap'));
      const hasWifi7 = features.some(f => f.toLowerCase().includes('wi-fi 7') || f.toLowerCase().includes('802.11be'));

      // Extract display nits from product specs
      const ruggedRating = product.rugged_rating || '';
      const ipMatch = ruggedRating.match(/IP(\d{2})/);
      const ipRating = ipMatch ? parseInt(ipMatch[1]) : 53;

      return {
        product_id: product.id,
        product_name: product.name,
        unit_price: product.base_price,
        warranty_years: parseInt(product.warranty_standard[0]) || 3,
        failure_rate: product.annual_failure_rate,
        competitor_name: competitorName || comp?.name || 'Competitor',
        competitor_price: comp?.base_price || 2000,
        competitor_warranty_years: comp ? parseInt(comp.warranty_standard[0]) || 1 : 1,
        competitor_failure_rate: comp?.annual_failure_rate || 0.10,
        // Feature flags
        has_hot_swap: hasHotSwap,
        display_nits: 1400,
        competitor_display_nits: 600,
        ip_rating: ipRating,
        competitor_ip_rating: 53,
        has_wifi7: hasWifi7,
        competitor_has_wifi7: false,
      };
    });

    setProductParams(params);
  }, [proposal.selectedProducts, proposal.competitorProductNames, competitors]);

  const updateProduct = (index: number, field: keyof ProductCalcParams, value: string | number | boolean) => {
    setProductParams(prev => prev.map((p, i) =>
      i === index ? { ...p, [field]: value } : p
    ));
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (fleetSize <= 0) newErrors.fleet_size = 'Fleet size must be greater than 0';
    if (deploymentYears <= 0) newErrors.deployment_years = 'Deployment years must be greater than 0';
    if (hourlyProductivityValue <= 0) newErrors.hourly_productivity_value = 'Must be greater than 0';
    if (avgDowntimeHours < 0) newErrors.avg_downtime_hours = 'Cannot be negative';
    if (annualRepairCost < 0) newErrors.annual_repair_cost = 'Cannot be negative';
    productParams.forEach((p, i) => {
      if (p.unit_price <= 0) newErrors[`product_${i}_price`] = 'Price must be greater than 0';
      if (p.failure_rate < 0 || p.failure_rate > 1) newErrors[`product_${i}_failure`] = 'Failure rate must be 0-100%';
      if (p.competitor_price <= 0) newErrors[`product_${i}_comp_price`] = 'Competitor price must be greater than 0';
      if (p.competitor_failure_rate < 0 || p.competitor_failure_rate > 1) newErrors[`product_${i}_comp_failure`] = 'Failure rate must be 0-100%';
      if (p.display_nits < 0) newErrors[`product_${i}_nits`] = 'Cannot be negative';
      if (p.competitor_display_nits < 0) newErrors[`product_${i}_comp_nits`] = 'Cannot be negative';
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) return;
    onConfirm({
      fleet_size: fleetSize,
      deployment_years: deploymentYears,
      hourly_productivity_value: hourlyProductivityValue,
      avg_downtime_hours_per_failure: avgDowntimeHours,
      annual_repair_cost: annualRepairCost,
      products: productParams,
    });
  };

  return (
    <div className="flex flex-col h-full bg-gray-900/50 backdrop-blur-md overflow-hidden animate-fade-in relative z-10 mx-auto max-w-7xl w-full border-x border-gray-800 shadow-2xl">
      {/* Header */}
      <div
        className="px-8 py-5 border-b border-gray-800 bg-gray-900 shadow-sm flex items-center gap-4"
        style={{ borderLeft: '4px solid var(--color-phase-calculation)' }}
      >
        <span className="text-3xl bg-gray-800 p-3 rounded-xl shadow-inner">&#x2699;</span>
        <div className="flex-1">
          <h2 className="text-xl font-bold text-white tracking-wide">Confirm Calculation Parameters</h2>
          <p className="text-sm text-gray-400 mt-0.5">Review and edit all values below before running TVO calculation.</p>
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto chat-scroll p-8">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Global Parameters */}
          <div className="rounded-2xl border border-gray-700/60 bg-gray-800/40 p-6">
            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-5 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-getac-light" />
              Deployment Parameters
            </h3>
            <div className="grid grid-cols-2 gap-6">
              <NumberField
                label="Fleet Size"
                value={fleetSize}
                onChange={setFleetSize}
                suffix="units"
                error={errors.fleet_size}
              />
              <NumberField
                label="Deployment Period"
                value={deploymentYears}
                onChange={setDeploymentYears}
                suffix="years"
                error={errors.deployment_years}
              />
            </div>
          </div>

          {/* Cost & Productivity Assumptions */}
          <div className="rounded-2xl border border-gray-700/60 bg-gray-800/40 p-6">
            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-5 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              Cost & Productivity Assumptions
            </h3>
            <div className="grid grid-cols-3 gap-6">
              <NumberField
                label="Hourly Productivity Value"
                value={hourlyProductivityValue}
                onChange={setHourlyProductivityValue}
                prefix="$"
                suffix="/hr"
                step={5}
                error={errors.hourly_productivity_value}
              />
              <NumberField
                label="Avg Downtime per Failure"
                value={avgDowntimeHours}
                onChange={setAvgDowntimeHours}
                suffix="hours"
                step={1}
                error={errors.avg_downtime_hours}
              />
              <NumberField
                label="Repair Cost per Incident"
                value={annualRepairCost}
                onChange={setAnnualRepairCost}
                prefix="$"
                step={50}
                error={errors.annual_repair_cost}
              />
            </div>
          </div>

          {/* Per-Product Cards */}
          {productParams.map((product, index) => (
            <div key={product.product_id} className="rounded-2xl border border-gray-700/60 bg-gray-800/40 overflow-hidden">
              {/* Product Header */}
              <div className="px-6 py-4 bg-getac-blue/20 border-b border-getac-light/10 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-getac-blue/30 border border-getac-light/20 flex items-center justify-center">
                    <span className="text-getac-light text-xs font-bold font-mono">
                      {product.product_id.slice(0, 3).toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <div className="text-sm font-bold text-white">{product.product_name}</div>
                    <div className="text-[11px] text-gray-500 font-mono uppercase tracking-wider">Getac Product</div>
                  </div>
                </div>
                {productParams.length > 1 && (
                  <span className="text-xs text-gray-500 font-mono">Product {index + 1} of {productParams.length}</span>
                )}
              </div>

              <div className="p-6">
                {/* Side-by-side paired rows: Getac vs Competitor */}
                <div className="grid grid-cols-2 gap-x-6 gap-y-4">
                  {/* Column Headers */}
                  <h4 className="text-[11px] font-bold text-getac-light uppercase tracking-widest pb-1">Getac Parameters</h4>
                  <h4 className="text-[11px] font-bold text-red-400 uppercase tracking-widest pb-1">Competitor Parameters</h4>

                  {/* Row: Name */}
                  <ReadOnlyField label="Product Name" value={product.product_name} />
                  <TextField
                    label="Competitor Name"
                    value={product.competitor_name}
                    onChange={v => updateProduct(index, 'competitor_name', v)}
                    placeholder="e.g. Dell Latitude 5430 Rugged"
                  />

                  {/* Row: Unit Price */}
                  <NumberField
                    label="Unit Price"
                    value={product.unit_price}
                    onChange={v => updateProduct(index, 'unit_price', v)}
                    prefix="$"
                    error={errors[`product_${index}_price`]}
                  />
                  <NumberField
                    label="Unit Price"
                    value={product.competitor_price}
                    onChange={v => updateProduct(index, 'competitor_price', v)}
                    prefix="$"
                    error={errors[`product_${index}_comp_price`]}
                  />

                  {/* Row: Warranty */}
                  <NumberField
                    label="Warranty"
                    value={product.warranty_years}
                    onChange={v => updateProduct(index, 'warranty_years', v)}
                    suffix="years"
                  />
                  <NumberField
                    label="Warranty"
                    value={product.competitor_warranty_years}
                    onChange={v => updateProduct(index, 'competitor_warranty_years', v)}
                    suffix="years"
                  />

                  {/* Row: Annual Failure Rate */}
                  <NumberField
                    label="Annual Failure Rate"
                    value={Math.round(product.failure_rate * 1000) / 10}
                    onChange={v => updateProduct(index, 'failure_rate', v / 100)}
                    suffix="%"
                    step={0.1}
                    error={errors[`product_${index}_failure`]}
                  />
                  <NumberField
                    label="Annual Failure Rate"
                    value={Math.round(product.competitor_failure_rate * 1000) / 10}
                    onChange={v => updateProduct(index, 'competitor_failure_rate', v / 100)}
                    suffix="%"
                    step={0.1}
                    error={errors[`product_${index}_comp_failure`]}
                  />

                  {/* Row: Display Brightness */}
                  <NumberField
                    label="Display Brightness"
                    value={product.display_nits}
                    onChange={v => updateProduct(index, 'display_nits', v)}
                    suffix="nits"
                    step={100}
                    error={errors[`product_${index}_nits`]}
                  />
                  <NumberField
                    label="Display Brightness"
                    value={product.competitor_display_nits}
                    onChange={v => updateProduct(index, 'competitor_display_nits', v)}
                    suffix="nits"
                    step={100}
                    error={errors[`product_${index}_comp_nits`]}
                  />

                  {/* Row: IP Rating */}
                  <NumberField
                    label="IP Rating"
                    value={product.ip_rating}
                    onChange={v => updateProduct(index, 'ip_rating', v)}
                    prefix="IP"
                  />
                  <NumberField
                    label="IP Rating"
                    value={product.competitor_ip_rating}
                    onChange={v => updateProduct(index, 'competitor_ip_rating', v)}
                    prefix="IP"
                  />

                  {/* Row: Hot-Swap Battery */}
                  <ToggleField
                    label="Hot-Swap Battery"
                    value={product.has_hot_swap}
                    onChange={v => updateProduct(index, 'has_hot_swap', v)}
                    color="blue"
                  />
                  <ToggleField
                    label="Hot-Swap Battery"
                    value={false}
                    onChange={() => {}}
                    color="red"
                    disabled
                  />

                  {/* Row: Wi-Fi 7 */}
                  <ToggleField
                    label="Wi-Fi 7"
                    value={product.has_wifi7}
                    onChange={v => updateProduct(index, 'has_wifi7', v)}
                    color="blue"
                  />
                  <ToggleField
                    label="Wi-Fi 7"
                    value={product.competitor_has_wifi7}
                    onChange={v => updateProduct(index, 'competitor_has_wifi7', v)}
                    color="red"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer Actions */}
      <div className="border-t border-gray-800 bg-gray-950/50 px-8 py-4 flex justify-between items-center">
        <button
          onClick={onBack}
          disabled={isSubmitting}
          className="px-6 py-2.5 rounded-lg font-medium text-sm text-gray-300 bg-gray-800 hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors focus:ring-2 focus:ring-gray-600 outline-none"
        >
          Back to Recommendation
        </button>
        <button
          onClick={handleSubmit}
          disabled={isSubmitting || productParams.length === 0}
          className="px-8 py-2.5 rounded-lg font-semibold text-sm text-white shadow-md disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:-translate-y-0.5 focus:ring-2 outline-none"
          style={{ backgroundColor: 'var(--color-phase-calculation)', boxShadow: '0 4px 20px -5px var(--color-phase-calculation)' }}
        >
          {isSubmitting ? 'Calculating...' : 'Confirm & Calculate TVO'}
        </button>
      </div>
    </div>
  );
}

/* ── Sub-components ── */

function TextField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
        {label}
      </label>
      <input
        type="text"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-gray-700 bg-gray-900 text-white text-sm px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-getac-light/30 hover:border-gray-600 transition-colors placeholder-gray-600"
      />
    </div>
  );
}

function NumberField({
  label,
  value,
  onChange,
  prefix,
  suffix,
  step = 1,
  error,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  prefix?: string;
  suffix?: string;
  step?: number;
  error?: string;
}) {
  return (
    <div>
      <label className="block text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
        {label}
      </label>
      <div className="relative flex items-center">
        {prefix && (
          <span className="absolute left-3 text-gray-500 text-sm pointer-events-none">{prefix}</span>
        )}
        <input
          type="number"
          value={value}
          step={step}
          onChange={e => onChange(parseFloat(e.target.value) || 0)}
          className={`w-full rounded-lg border bg-gray-900 text-white text-sm font-mono px-3 py-2.5 focus:outline-none focus:ring-2 transition-colors ${
            error
              ? 'border-red-500/50 focus:ring-red-500/30'
              : 'border-gray-700 focus:ring-getac-light/30 hover:border-gray-600'
          } ${prefix ? 'pl-7' : ''} ${suffix ? 'pr-12' : ''}`}
        />
        {suffix && (
          <span className="absolute right-3 text-gray-500 text-xs pointer-events-none">{suffix}</span>
        )}
      </div>
      {error && <p className="text-xs text-red-400 mt-1">{error}</p>}
    </div>
  );
}

function ReadOnlyField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <label className="block text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
        {label}
      </label>
      <div className="w-full rounded-lg border border-gray-700/50 bg-gray-900/50 text-gray-300 text-sm px-3 py-2.5">
        {value}
      </div>
    </div>
  );
}

function ToggleField({
  label,
  value,
  onChange,
  color = 'blue',
  disabled = false,
}: {
  label: string;
  value: boolean;
  onChange: (value: boolean) => void;
  color?: 'blue' | 'red';
  disabled?: boolean;
}) {
  const activeColor = color === 'blue' ? 'bg-blue-500' : 'bg-red-500';
  return (
    <div>
      <label className="block text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
        {label}
      </label>
      <button
        type="button"
        onClick={() => !disabled && onChange(!value)}
        disabled={disabled}
        className={`w-full rounded-lg border px-3 py-2.5 text-sm font-mono text-left transition-colors focus:outline-none focus:ring-2 focus:ring-getac-light/30 disabled:opacity-50 disabled:cursor-not-allowed ${
          value
            ? `border-${color === 'blue' ? 'blue' : 'red'}-500/40 bg-${color === 'blue' ? 'blue' : 'red'}-500/10 text-white`
            : 'border-gray-700 bg-gray-900 text-gray-500'
        }`}
      >
        <span className="flex items-center gap-2">
          <span className={`w-3 h-3 rounded-full border-2 flex items-center justify-center ${
            value ? `${activeColor} border-transparent` : 'border-gray-600'
          }`}>
            {value && <span className="text-white text-[8px]">&#x2713;</span>}
          </span>
          {value ? 'Yes' : 'No'}
        </span>
      </button>
    </div>
  );
}
