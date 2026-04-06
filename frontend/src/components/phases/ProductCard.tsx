import type { GetacProduct } from '../../types';

interface Props {
  product?: GetacProduct;
  competitiveAdvantages?: string[];
  compact?: boolean;
}

export default function ProductCard({ product, competitiveAdvantages, compact }: Props) {
  if (!product) {
    return (
      <div className="w-full rounded-2xl border border-dashed border-gray-700 bg-gray-800/20 p-12 text-center space-y-3">
        <div className="text-4xl opacity-30">&#x1F4BB;</div>
        <p className="text-gray-500 text-sm max-w-xs mx-auto leading-relaxed">
          No product selected yet. Use the chat or quick chips below to get a recommendation.
        </p>
      </div>
    );
  }

  if (compact) {
    return <CompactCard product={product} competitiveAdvantages={competitiveAdvantages} />;
  }

  return <FullCard product={product} competitiveAdvantages={competitiveAdvantages} />;
}

/* ─────────────────────────── COMPACT CARD (used in ReviewPanel) ─────────────────────────── */

function CompactCard({ product, competitiveAdvantages }: { product: GetacProduct; competitiveAdvantages?: string[] }) {
  const ruggedBadges = parseRuggedRating(product.rugged_rating);

  return (
    <div className="space-y-3">
      {/* Identity strip */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-lg bg-getac-blue/30 border border-getac-light/20 flex items-center justify-center shrink-0">
            <span className="text-getac-light text-xs font-bold font-mono">{product.id.slice(0, 3).toUpperCase()}</span>
          </div>
          <div className="min-w-0">
            <div className="text-sm font-bold text-white truncate">{product.name}</div>
            <div className="text-[11px] text-gray-500 font-mono uppercase tracking-wider">{product.category}</div>
          </div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-lg font-bold text-white font-mono">${product.base_price.toLocaleString()}</div>
        </div>
      </div>

      {/* Rugged badges inline */}
      <div className="flex flex-wrap gap-1.5">
        {ruggedBadges.map((badge, i) => (
          <span key={i} className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded border border-amber-500/25 bg-amber-500/8 text-amber-400/90 uppercase tracking-wider">
            {badge}
          </span>
        ))}
      </div>

      {/* Competitive advantages (compact) */}
      {competitiveAdvantages && competitiveAdvantages.length > 0 && (
        <div className="space-y-1 pt-1 border-t border-gray-700/40">
          {competitiveAdvantages.slice(0, 3).map((adv, i) => (
            <div key={i} className="flex items-start gap-2 text-xs">
              <span className="text-amber-400 mt-0.5 shrink-0 font-mono text-[10px]">&#x25B8;</span>
              <span className="text-gray-400 line-clamp-1">{adv}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ─────────────────────────── FULL CARD (used in recommendation phase) ─────────────────────────── */

function FullCard({ product, competitiveAdvantages }: { product: GetacProduct; competitiveAdvantages?: string[] }) {
  const ruggedBadges = parseRuggedRating(product.rugged_rating);
  const failurePercent = product.annual_failure_rate * 100;
  const reliabilityPercent = 100 - failurePercent;

  return (
    <div className="w-full space-y-5 animate-slide-down">

      {/* ── HERO: Device Identity ── */}
      <div className="rounded-2xl border border-gray-700/50 overflow-hidden bg-gray-900/80">
        {/* Top strip — product line + model indicator */}
        <div className="px-5 py-1.5 bg-getac-blue/20 border-b border-getac-light/10 flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-getac-light animate-pulse" />
          <span className="text-[10px] font-mono text-getac-light/70 uppercase tracking-[0.2em]">AI-Recommended Device</span>
        </div>

        {/* Name + price */}
        <div className="px-6 py-5 flex items-start justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-getac-blue/40 to-gray-800 border border-getac-light/15 flex items-center justify-center shadow-lg shadow-getac-blue/10">
                <span className="text-getac-light font-bold font-mono text-sm tracking-tight">{product.id.slice(0, 2).toUpperCase()}</span>
              </div>
              <div>
                <h3 className="text-xl font-extrabold text-white tracking-tight">{product.name}</h3>
                <p className="text-xs text-gray-400 font-mono uppercase tracking-wider mt-0.5">{product.category}</p>
              </div>
            </div>
          </div>
          <div className="text-right shrink-0">
            <div className="text-xs text-gray-500 font-mono uppercase tracking-wider">Unit Price</div>
            <div className="text-2xl font-extrabold text-white font-mono tracking-tight">
              <span className="text-gray-500 text-lg">$</span>{product.base_price.toLocaleString()}
            </div>
          </div>
        </div>

        {/* Rugged certification badges */}
        <div className="px-6 pb-5 flex flex-wrap gap-2">
          {ruggedBadges.map((badge, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1.5 text-[11px] font-mono font-bold px-2.5 py-1 rounded-md border border-amber-500/25 bg-amber-500/8 text-amber-400/90 uppercase tracking-wider"
            >
              <svg className="w-3 h-3 text-amber-500/60" fill="currentColor" viewBox="0 0 16 16">
                <path d="M8 1.5a1 1 0 0 1 .894.553l.448.894h1.882a1 1 0 0 1 .707 1.707l-1.414 1.414.553 1.658a1 1 0 0 1-1.504 1.095L8 7.882l-1.566.939a1 1 0 0 1-1.504-1.095l.553-1.658L4.069 4.654A1 1 0 0 1 4.776 2.947h1.882l.448-.894A1 1 0 0 1 8 1.5z" />
              </svg>
              {badge}
            </span>
          ))}
        </div>
      </div>

      {/* ── SPEC GRID: 2x2 quadrant layout ── */}
      <div className="grid grid-cols-2 gap-3">
        {/* Performance */}
        <SpecGroup title="Performance" icon="&#x26A1;">
          <SpecLine label="Processor" value={product.processor} mono />
          <SpecLine label="RAM" value={product.ram_options.join(' / ')} />
          <SpecLine label="Storage" value={product.storage_options[product.storage_options.length - 1]} sub={`${product.storage_options.length} options`} />
        </SpecGroup>

        {/* Display */}
        <SpecGroup title="Display" icon="&#x1F4BB;">
          <SpecLine label="Size" value={product.display_size} />
          <SpecLine label="Battery" value={product.battery_life} />
        </SpecGroup>

        {/* Durability */}
        <SpecGroup title="Durability" icon="&#x1F6E1;">
          <SpecLine label="Operating Temp" value={product.operating_temp} />
          <SpecLine label="Warranty" value={product.warranty_standard} highlight />
          <div className="mt-2">
            <div className="flex items-center justify-between text-[11px] mb-1">
              <span className="text-gray-500 font-mono uppercase tracking-wider">Reliability</span>
              <span className="text-green-400 font-bold font-mono">{reliabilityPercent.toFixed(1)}%</span>
            </div>
            <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-1000 ease-out"
                style={{
                  width: `${reliabilityPercent}%`,
                  background: `linear-gradient(90deg, #10b981 0%, #34d399 100%)`,
                }}
              />
            </div>
            <div className="text-[10px] text-gray-600 mt-1 font-mono">{failurePercent.toFixed(1)}% annual failure rate</div>
          </div>
        </SpecGroup>

        {/* Connectivity */}
        <SpecGroup title="Connectivity" icon="&#x1F4F6;">
          <SpecLine label="Warranty Opts" value={product.warranty_options.slice(0, 2).join(', ')} />
          <SpecLine label="RAM Options" value={product.ram_options.join(', ')} />
        </SpecGroup>
      </div>

      {/* ── KEY FEATURES ── */}
      {product.key_features.length > 0 && (
        <div className="rounded-2xl border border-gray-700/40 bg-gray-800/25 overflow-hidden">
          <div className="px-5 py-3 border-b border-gray-700/30 flex items-center gap-2">
            <span className="text-getac-light text-xs">&#x2B22;</span>
            <h4 className="text-[11px] font-bold text-gray-400 uppercase tracking-[0.15em]">Key Capabilities</h4>
            <span className="ml-auto text-[10px] text-gray-600 font-mono">{product.key_features.length} features</span>
          </div>
          <div className="p-5 grid grid-cols-2 gap-x-6 gap-y-2">
            {product.key_features.map((feat, i) => (
              <div key={i} className="flex items-start gap-2.5 text-sm group">
                <span className="text-getac-light/60 mt-1 shrink-0 text-[10px] font-mono group-hover:text-getac-light transition-colors">&#x25C6;</span>
                <span className="text-gray-300 leading-snug text-[13px]">{feat}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── TARGET INDUSTRIES ── */}
      {product.target_industries.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[10px] text-gray-600 font-mono uppercase tracking-wider shrink-0 mr-1">Industries:</span>
          {product.target_industries.map((ind, i) => (
            <span
              key={i}
              className="text-[11px] px-2.5 py-1 rounded-md bg-getac-blue/15 text-getac-light/80 border border-getac-light/10 font-medium hover:bg-getac-blue/25 hover:border-getac-light/20 transition-colors cursor-default"
            >
              {ind}
            </span>
          ))}
        </div>
      )}

      {/* ── COMPETITIVE ADVANTAGES ── */}
      {competitiveAdvantages && competitiveAdvantages.length > 0 && (
        <div className="rounded-2xl border border-amber-500/15 bg-amber-500/[0.03] overflow-hidden">
          <div className="px-5 py-3 border-b border-amber-500/10 flex items-center gap-2">
            <svg className="w-3.5 h-3.5 text-amber-400/70" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M12.577 4.878a.75.75 0 01.919-.53l4.78 1.281a.75.75 0 01.531.919l-1.281 4.78a.75.75 0 01-1.449-.387l.81-3.022a19.407 19.407 0 00-5.594 5.203.75.75 0 01-1.139.093L7 10.06l-4.72 4.72a.75.75 0 01-1.06-1.06l5.25-5.25a.75.75 0 011.06 0l3.074 3.073a20.923 20.923 0 015.545-4.931l-3.042.815a.75.75 0 01-.53-.919z" clipRule="evenodd" />
            </svg>
            <h4 className="text-[11px] font-bold text-amber-400/80 uppercase tracking-[0.15em]">Competitive Advantages</h4>
          </div>
          <div className="p-5 space-y-3">
            {competitiveAdvantages.map((adv, i) => (
              <div key={i} className="flex items-start gap-3 group">
                <div className="w-5 h-5 rounded bg-amber-500/10 border border-amber-500/20 flex items-center justify-center shrink-0 mt-0.5 group-hover:bg-amber-500/20 transition-colors">
                  <span className="text-amber-400 text-[10px] font-bold font-mono">{i + 1}</span>
                </div>
                <span className="text-[13px] text-gray-300 leading-relaxed">{adv}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


/* ═══════════════════════════ Sub-components ═══════════════════════════ */

function SpecGroup({ title, icon, children }: { title: string; icon: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-gray-700/40 bg-gray-800/30 overflow-hidden">
      <div className="px-4 py-2 border-b border-gray-700/25 flex items-center gap-2 bg-gray-800/40">
        <span className="text-xs opacity-60">{icon}</span>
        <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">{title}</h4>
      </div>
      <div className="px-4 py-3 space-y-2">
        {children}
      </div>
    </div>
  );
}

function SpecLine({
  label,
  value,
  highlight,
  mono,
  sub,
}: {
  label: string;
  value: string;
  highlight?: boolean;
  mono?: boolean;
  sub?: string;
}) {
  return (
    <div className="flex items-start justify-between gap-2">
      <span className="text-[11px] text-gray-500 font-mono uppercase tracking-wider shrink-0 mt-0.5">{label}</span>
      <div className="text-right min-w-0">
        <span className={`text-[12px] leading-tight ${mono ? 'font-mono' : ''} ${highlight ? 'text-getac-light font-semibold' : 'text-gray-300'}`}>
          {value}
        </span>
        {sub && <div className="text-[10px] text-gray-600 mt-0.5">{sub}</div>}
      </div>
    </div>
  );
}


/* ═══════════════════════════ Helpers ═══════════════════════════ */

/** Parse "MIL-STD-810H, MIL-STD-461G, IP66" into individual badges */
function parseRuggedRating(rating: string): string[] {
  return rating
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);
}
