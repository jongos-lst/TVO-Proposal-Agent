import { useState } from 'react';
import type { CustomerPersona } from '../../types';

interface Props {
  onSubmit: (persona: CustomerPersona) => void;
  isSubmitting: boolean;
  initialData?: CustomerPersona;
}

const INDUSTRIES = [
  'Field Service', 'Utilities', 'Oil & Gas', 'Manufacturing',
  'Public Safety', 'Transportation', 'Logistics', 'Healthcare',
  'Military / Defense', 'Mining', 'Construction', 'Warehouse',
  'Aviation', 'Emergency Response', 'Other',
];

export default function IntakeForm({ onSubmit, isSubmitting, initialData }: Props) {
  const [form, setForm] = useState<CustomerPersona>({
    customer_name: initialData?.customer_name || '',
    industry: initialData?.industry || '',
    pain_points: initialData?.pain_points || [],
    use_scenarios: initialData?.use_scenarios || [],
    budget_amount: initialData?.budget_amount ?? undefined,
    service_warranty_needs: initialData?.service_warranty_needs || '',
    current_devices: initialData?.current_devices || [],
    fleet_size: initialData?.fleet_size ?? undefined,
    deployment_timeline: initialData?.deployment_timeline || '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Helpers for comma-separated list fields
  const [painPointsText, setPainPointsText] = useState(initialData?.pain_points?.join('\n') || '');
  const [scenariosText, setScenariosText] = useState(initialData?.use_scenarios?.join('\n') || '');
  const [devicesText, setDevicesText] = useState(initialData?.current_devices?.join('\n') || '');

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!painPointsText.trim()) newErrors.pain_points = 'At least one pain point is required';
    if (!scenariosText.trim()) newErrors.use_scenarios = 'At least one use scenario is required';
    if (!form.budget_amount) newErrors.budget_amount = 'Budget is required';
    if (!form.service_warranty_needs?.trim()) newErrors.service_warranty_needs = 'Warranty needs are required';
    if (!devicesText.trim()) newErrors.current_devices = 'Current devices are required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    const persona: CustomerPersona = {
      ...form,
      pain_points: painPointsText.split('\n').map(s => s.trim()).filter(Boolean),
      use_scenarios: scenariosText.split('\n').map(s => s.trim()).filter(Boolean),
      current_devices: devicesText.split('\n').map(s => s.trim()).filter(Boolean),
    };
    onSubmit(persona);
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <form onSubmit={handleSubmit} className="max-w-3xl mx-auto p-8">
        {/* Header */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white">Customer Persona Intake</h2>
          <p className="text-sm text-gray-400 mt-1">
            Fill in the customer details below to begin building the TVO proposal.
          </p>
        </div>

        <div className="space-y-6">
          {/* Row: Customer Name + Industry */}
          <div className="grid grid-cols-2 gap-4">
            <Field
              label="Customer Name"
              value={form.customer_name || ''}
              onChange={v => setForm(f => ({ ...f, customer_name: v }))}
              placeholder="e.g. Acme Corp"
            />
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Industry</label>
              <select
                value={form.industry || ''}
                onChange={e => setForm(f => ({ ...f, industry: e.target.value }))}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-getac-light/50 focus:border-transparent"
              >
                <option value="">Select industry...</option>
                {INDUSTRIES.map(i => <option key={i} value={i}>{i}</option>)}
              </select>
            </div>
          </div>

          {/* Pain Points */}
          <TextAreaField
            label="Pain Points"
            required
            value={painPointsText}
            onChange={setPainPointsText}
            placeholder="Enter each pain point on a new line, e.g.&#10;Frequent device failures in the field&#10;High repair and replacement costs&#10;Excessive downtime during battery changes"
            error={errors.pain_points}
            rows={3}
          />

          {/* Use Scenarios */}
          <TextAreaField
            label="Use Scenarios"
            required
            value={scenariosText}
            onChange={setScenariosText}
            placeholder="Enter each scenario on a new line, e.g.&#10;Outdoor field inspection&#10;Warehouse inventory management&#10;Vehicle-mounted mobile computing"
            error={errors.use_scenarios}
            rows={3}
          />

          {/* Row: Budget + Fleet Size */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">
                Budget <span className="text-red-400">*</span>
                <span className="text-gray-500 font-normal text-xs ml-2">(USD)</span>
              </label>
              <input
                type="number"
                min={0}
                step={1000}
                value={form.budget_amount ?? ''}
                onChange={e => setForm(f => ({ ...f, budget_amount: e.target.value ? parseFloat(e.target.value) : undefined }))}
                placeholder="e.g. 500000"
                className={`w-full bg-gray-800 border rounded-lg px-3 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-getac-light/50 focus:border-transparent ${
                  errors.budget_amount ? 'border-red-500' : 'border-gray-700'
                }`}
              />
              {errors.budget_amount && <p className="text-xs text-red-400 mt-1">{errors.budget_amount}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">
                Fleet Size <span className="text-gray-500 font-normal">(devices)</span>
              </label>
              <input
                type="number"
                min={1}
                value={form.fleet_size ?? ''}
                onChange={e => setForm(f => ({ ...f, fleet_size: e.target.value ? parseInt(e.target.value) : undefined }))}
                placeholder="e.g. 100"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-getac-light/50 focus:border-transparent"
              />
            </div>
          </div>

          {/* Service & Warranty */}
          <Field
            label="Service & Warranty Needs"
            required
            value={form.service_warranty_needs || ''}
            onChange={v => setForm(f => ({ ...f, service_warranty_needs: v }))}
            placeholder="e.g. 3-year bumper-to-bumper, next-day replacement"
            error={errors.service_warranty_needs}
          />

          {/* Current Devices */}
          <TextAreaField
            label="Current Devices / Solutions"
            required
            value={devicesText}
            onChange={setDevicesText}
            placeholder="Enter each device on a new line, e.g.&#10;Dell Latitude 5430 Rugged&#10;iPad Pro with OtterBox case"
            error={errors.current_devices}
            rows={2}
          />

          {/* Deployment Timeline */}
          <Field
            label="Deployment Timeline"
            value={form.deployment_timeline || ''}
            onChange={v => setForm(f => ({ ...f, deployment_timeline: v }))}
            placeholder="e.g. Q3 2026"
          />
        </div>

        {/* Submit */}
        <div className="mt-8 flex items-center gap-4">
          <button
            type="submit"
            disabled={isSubmitting}
            className="bg-getac-light hover:bg-getac-blue text-white rounded-lg px-8 py-3 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Submitting...' : 'Continue to Product Recommendation'}
          </button>
          <span className="text-xs text-gray-500">
            Fields marked with <span className="text-red-400">*</span> are required
          </span>
        </div>
      </form>
    </div>
  );
}


/* ---------- Reusable field components ---------- */

function Field({
  label, value, onChange, placeholder, required, error,
}: {
  label: string; value: string; onChange: (v: string) => void;
  placeholder?: string; required?: boolean; error?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-300 mb-1.5">
        {label} {required && <span className="text-red-400">*</span>}
      </label>
      <input
        type="text"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className={`w-full bg-gray-800 border rounded-lg px-3 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-getac-light/50 focus:border-transparent ${
          error ? 'border-red-500' : 'border-gray-700'
        }`}
      />
      {error && <p className="text-xs text-red-400 mt-1">{error}</p>}
    </div>
  );
}

function TextAreaField({
  label, value, onChange, placeholder, required, error, rows = 3,
}: {
  label: string; value: string; onChange: (v: string) => void;
  placeholder?: string; required?: boolean; error?: string; rows?: number;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-300 mb-1.5">
        {label} {required && <span className="text-red-400">*</span>}
        <span className="text-gray-500 font-normal text-xs ml-2">(one per line)</span>
      </label>
      <textarea
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        className={`w-full bg-gray-800 border rounded-lg px-3 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-getac-light/50 focus:border-transparent resize-none ${
          error ? 'border-red-500' : 'border-gray-700'
        }`}
      />
      {error && <p className="text-xs text-red-400 mt-1">{error}</p>}
    </div>
  );
}
