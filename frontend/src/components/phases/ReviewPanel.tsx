import type { ProposalState } from '../../types';
import IntakeSummary from './IntakeSummary';
import ProductCard from './ProductCard';

interface Props {
  proposal: ProposalState;
}

export default function ReviewPanel({ proposal }: Props) {
  const selectedProducts = proposal.selectedProducts || [];
  const tvoResults = proposal.tvoResults || {};
  const advantagesMap = proposal.competitiveAdvantages || {};

  return (
    <div className="w-full space-y-6 animate-slide-down">
      {/* Review Header */}
      <div className="rounded-2xl border border-purple-500/20 bg-purple-500/5 p-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center text-lg">
            &#x1F4CB;
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Proposal Review</h3>
            <p className="text-xs text-gray-400">
              Review all sections below ({selectedProducts.length} product{selectedProducts.length !== 1 ? 's' : ''}). Use the chat to request changes, or approve to generate the deck.
            </p>
          </div>
          {proposal.proposalApproved && (
            <span className="ml-auto px-3 py-1 rounded-full bg-green-500/20 text-green-400 text-xs font-bold border border-green-500/30">
              &#x2713; Approved
            </span>
          )}
        </div>
      </div>

      {/* Section 1: Customer Profile */}
      <ReviewSection number={1} title="Customer Profile" status="complete">
        <IntakeSummary persona={proposal.persona} />
      </ReviewSection>

      {/* Section 2: Product Recommendation(s) */}
      <ReviewSection
        number={2}
        title={`Recommended Product${selectedProducts.length > 1 ? 's' : ''} (${selectedProducts.length})`}
        status={selectedProducts.length > 0 ? 'complete' : 'pending'}
      >
        {selectedProducts.length > 0 ? (
          <div className="space-y-4">
            {selectedProducts.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                competitiveAdvantages={advantagesMap[product.id]}
                compact
              />
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No products selected yet.</p>
        )}
      </ReviewSection>

      {/* Section 3: TVO / TCO Analysis (per product) */}
      <ReviewSection
        number={3}
        title="TVO / TCO Analysis"
        status={Object.keys(tvoResults).length > 0 ? 'complete' : 'pending'}
      >
        {Object.keys(tvoResults).length > 0 ? (
          <div className="space-y-6">
            {selectedProducts.map((product) => {
              const tvo = tvoResults[product.id];
              if (!tvo) return null;
              return (
                <div key={product.id}>
                  {selectedProducts.length > 1 && (
                    <h4 className="text-sm font-bold text-getac-light mb-3">{product.name}</h4>
                  )}
                  <div className="space-y-4">
                    {/* Key metrics inline */}
                    <div className="grid grid-cols-3 gap-3">
                      <MiniMetric label="Getac TCO" value={`$${tvo.getac_total_tco.toLocaleString()}`} />
                      <MiniMetric label="Competitor TCO" value={`$${tvo.competitor_total_tco.toLocaleString()}`} />
                      <MiniMetric
                        label="Savings"
                        value={`$${tvo.tco_savings.toLocaleString()}`}
                        accent={tvo.tco_savings > 0 ? 'green' : 'red'}
                      />
                    </div>
                    {/* Breakdown table */}
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-700/50">
                          <th className="text-left py-2 text-gray-500 text-xs font-semibold">Cost Category</th>
                          <th className="text-right py-2 text-gray-500 text-xs font-semibold">Getac</th>
                          <th className="text-right py-2 text-gray-500 text-xs font-semibold">Competitor</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-800/40">
                        {tvo.tco_line_items.map((item, i) => (
                          <tr key={i}>
                            <td className="py-2 text-gray-300">{item.label}</td>
                            <td className="py-2 text-right text-gray-200 font-mono">${item.getac_value.toLocaleString()}</td>
                            <td className="py-2 text-right text-gray-200 font-mono">${item.competitor_value.toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              );
            })}

            {/* Combined total if multiple products */}
            {selectedProducts.length > 1 && (
              <div className="rounded-xl border border-green-500/20 bg-green-500/5 p-4">
                <h4 className="text-xs font-bold text-green-400 uppercase tracking-wider mb-2">
                  Combined Savings ({selectedProducts.length} products)
                </h4>
                <div className="text-2xl font-bold text-green-400">
                  ${Object.values(tvoResults).reduce((sum, t) => sum + t.tco_savings, 0).toLocaleString()}
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">Pending calculation...</p>
        )}
      </ReviewSection>

      {/* Section 4: Competitive Advantages (combined) */}
      {Object.keys(advantagesMap).length > 0 && (
        <ReviewSection number={4} title="Competitive Advantages" status="complete">
          <div className="space-y-4">
            {selectedProducts.map((product) => {
              const advantages = advantagesMap[product.id];
              if (!advantages?.length) return null;
              return (
                <div key={product.id}>
                  {selectedProducts.length > 1 && (
                    <h4 className="text-xs font-semibold text-getac-light mb-2">{product.name}</h4>
                  )}
                  <div className="space-y-2">
                    {advantages.map((adv, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm">
                        <span className="text-amber-400 mt-0.5 shrink-0">&#x25B6;</span>
                        <span className="text-gray-300">{adv}</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </ReviewSection>
      )}
    </div>
  );
}


/* ---------- Sub-components ---------- */

function ReviewSection({
  number, title, status, children,
}: {
  number: number; title: string; status: 'complete' | 'pending'; children: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-gray-700/60 bg-gray-800/40 overflow-hidden">
      <div className="px-5 py-3 border-b border-gray-700/50 flex items-center justify-between bg-gray-800/60">
        <div className="flex items-center gap-3">
          <span className="w-6 h-6 rounded bg-gray-700 flex items-center justify-center text-xs font-bold text-gray-300">
            {number}
          </span>
          <h4 className="text-sm font-semibold text-white">{title}</h4>
        </div>
        <span className={`text-xs font-medium ${status === 'complete' ? 'text-green-400' : 'text-gray-500'}`}>
          {status === 'complete' ? '&#x2713; Complete' : 'Pending'}
        </span>
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}

function MiniMetric({ label, value, accent }: { label: string; value: string; accent?: string }) {
  const color = accent === 'green' ? 'text-green-400' : accent === 'red' ? 'text-red-400' : 'text-white';
  return (
    <div className="rounded-xl bg-gray-800/60 p-3 text-center">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-sm font-bold font-mono ${color}`}>{value}</div>
    </div>
  );
}
