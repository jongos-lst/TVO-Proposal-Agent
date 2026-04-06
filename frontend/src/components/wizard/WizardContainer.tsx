import { PHASE_CONFIG } from '../../config/PhaseConfig';
import type { Message, Phase, ProposalState, CalculationParams } from '../../types';
import RichMarkdown from '../shared/RichMarkdown';
import ProductCard from '../phases/ProductCard';
import TVOTable from '../phases/TVOTable';
import ReviewPanel from '../phases/ReviewPanel';
import ExportButton from '../phases/ExportButton';
import ConfirmationPanel from '../phases/ConfirmationPanel';
import InputBar from '../chat/InputBar';

interface Props {
    proposal: ProposalState;
    messages: Message[];
    isStreaming: boolean;
    onNext: (message: string) => void;
    onBack: (targetPhase: Phase) => void;
    sessionId: string;
    showConfirmation: boolean;
    setShowConfirmation: (show: boolean) => void;
    confirmCalculation: (params: CalculationParams) => void;
    approveAndGenerate: () => void;
}

export default function WizardContainer({ proposal, messages, isStreaming, onNext, onBack, sessionId, showConfirmation, setShowConfirmation, confirmCalculation, approveAndGenerate }: Props) {
    const currentPhase = proposal.phase;
    const config = PHASE_CONFIG[currentPhase];

    // Helper to determine the previous phase
    const getPreviousPhase = (): Phase | null => {
        switch (currentPhase) {
            case 'recommendation': return 'intake';
            case 'calculation': return 'recommendation';
            case 'review': return 'calculation';
            case 'generation': return 'review';
            case 'complete': return 'review';
            default: return null;
        }
    };

    // Helper to determine the next phase
    const getNextPhase = (): Phase | null => {
        switch (currentPhase) {
            case 'intake': return 'recommendation';
            case 'recommendation': return 'calculation';
            case 'calculation': return 'review';
            case 'review': return 'generation';
            default: return null;
        }
    };

    const prevPhase = getPreviousPhase();
    const nextPhase = getNextPhase();
    const nextPhaseLabel = nextPhase ? PHASE_CONFIG[nextPhase].label : null;

    // The latest assistant message acts as the Agent's Insight for the current screen
    const agentInsight = messages.slice().reverse().find(m => m.role === 'assistant')?.content || '';

    // Continue button is disabled until phase prerequisites are met
    const canContinue = (() => {
        if (isStreaming) return false;
        if (!nextPhase) return false;
        switch (currentPhase) {
            case 'recommendation':
                return !!(proposal.selectedProducts && proposal.selectedProducts.length > 0);
            case 'calculation':
                return !!(proposal.tvoResults && Object.keys(proposal.tvoResults).length > 0);
            case 'review':
                return !!(proposal.tvoResults && Object.keys(proposal.tvoResults).length > 0);
            default:
                return true;
        }
    })();

    const handleNextClick = () => {
        if (currentPhase === 'recommendation') {
            setShowConfirmation(true);
            return;
        }
        if (currentPhase === 'review') {
            approveAndGenerate();
            return;
        }
        if (nextPhase) {
            onBack(nextPhase);  // reuse goToPhase for forward navigation
        }
    };

    // Show confirmation panel as full-page overlay
    if (showConfirmation) {
        return (
            <ConfirmationPanel
                proposal={proposal}
                onConfirm={confirmCalculation}
                onBack={() => setShowConfirmation(false)}
                isSubmitting={isStreaming}
            />
        );
    }

    // Determine layout: structured data panel on left, agent insight on right for wider phases
    const hasSelectedProducts = proposal.selectedProducts && proposal.selectedProducts.length > 0;
    const hasTvoResults = proposal.tvoResults && Object.keys(proposal.tvoResults).length > 0;
    const hasStructuredData = (
        (currentPhase === 'recommendation' && hasSelectedProducts) ||
        (currentPhase === 'calculation' && hasTvoResults) ||
        currentPhase === 'review'
    );

    return (
        <div className="flex flex-col h-full bg-gray-900/50 backdrop-blur-md overflow-hidden animate-fade-in relative z-10 mx-auto max-w-7xl w-full border-x border-gray-800 shadow-2xl">
            {/* Wizard Header */}
            <div
                className="px-8 py-5 border-b border-gray-800 bg-gray-900 shadow-sm flex items-center gap-4 transition-all duration-500"
                style={{ borderLeft: `4px solid var(--color-phase-${currentPhase})` }}
            >
                <span className="text-3xl bg-gray-800 p-3 rounded-xl shadow-inner">{config?.icon || '\u{1F4DD}'}</span>
                <div className="flex-1">
                    <h2 className="text-xl font-bold text-white tracking-wide">{config?.label || 'Processing...'}</h2>
                    <p className="text-sm text-gray-400 mt-0.5">{config?.description || 'Please wait contextually.'}</p>
                </div>
                {isStreaming && (
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-800 border border-gray-700">
                        <span className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: `var(--color-phase-${currentPhase})` }} />
                        <span className="text-xs text-gray-400">Analyzing...</span>
                    </div>
                )}
            </div>

            {/* Main Content Area (Scrollable) */}
            <div className="flex-1 overflow-y-auto chat-scroll">

                {/* Two-column layout when we have both structured data and agent insight */}
                {hasStructuredData ? (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-0 min-h-full">
                        {/* Left: Structured Data Panel */}
                        <div className="p-6 border-r border-gray-800/50 overflow-y-auto">
                            <div className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                                <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: `var(--color-phase-${currentPhase})` }} />
                                {currentPhase === 'recommendation' && 'Product Details'}
                                {currentPhase === 'calculation' && 'TVO / TCO Analysis'}
                                {currentPhase === 'review' && 'Proposal Summary'}
                            </div>

                            {currentPhase === 'recommendation' && proposal.selectedProducts && (
                                <div className="space-y-6">
                                    {proposal.selectedProducts.map((product) => (
                                        <ProductCard
                                            key={product.id}
                                            product={product}
                                            competitiveAdvantages={proposal.competitiveAdvantages?.[product.id]}
                                        />
                                    ))}
                                </div>
                            )}
                            {currentPhase === 'calculation' && proposal.tvoResults && proposal.selectedProducts && (
                                <div className="space-y-8">
                                    {proposal.selectedProducts.map((product) => {
                                        const tvo = proposal.tvoResults?.[product.id];
                                        return (
                                            <div key={product.id}>
                                                {proposal.selectedProducts!.length > 1 && (
                                                    <h3 className="text-sm font-bold text-getac-light mb-3">{product.name}</h3>
                                                )}
                                                <TVOTable tvo={tvo} sessionId={sessionId} productId={product.id} productName={product.name} />
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                            {currentPhase === 'review' && (
                                <ReviewPanel proposal={proposal} />
                            )}
                        </div>

                        {/* Right: Agent Insight Panel */}
                        <div className="p-6 overflow-y-auto bg-gray-900/30">
                            <div className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                                <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ backgroundColor: `var(--color-phase-${currentPhase})` }} />
                                Agent Analysis
                            </div>
                            {isStreaming && !agentInsight ? (
                                <div className="flex items-center gap-3 py-8">
                                    <div className="flex gap-1">
                                        <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                        <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                        <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                    </div>
                                    <span className="text-sm text-gray-500">Generating analysis...</span>
                                </div>
                            ) : agentInsight ? (
                                <RichMarkdown content={agentInsight} phase={currentPhase} />
                            ) : (
                                <p className="text-sm text-gray-500 py-4">
                                    Use the chat below or click {nextPhaseLabel ? `"Continue to ${nextPhaseLabel}"` : '"Continue"'} to generate the agent's analysis.
                                </p>
                            )}
                        </div>
                    </div>
                ) : (
                    /* Single-column layout for phases without structured data */
                    <div className="p-8 space-y-8">
                        {/* Recommendation without product yet */}
                        {currentPhase === 'recommendation' && !hasSelectedProducts && (
                            <div className="flex justify-center">
                                <div className="w-full max-w-2xl">
                                    <ProductCard product={undefined} />
                                </div>
                            </div>
                        )}

                        {/* Calculation without TVO yet */}
                        {currentPhase === 'calculation' && !hasTvoResults && (
                            <div className="flex justify-center">
                                <div className="w-full max-w-2xl">
                                    <TVOTable tvo={undefined} />
                                </div>
                            </div>
                        )}

                        {/* Generation phase */}
                        {(currentPhase === 'generation' || currentPhase === 'complete') && (
                            <div className="flex justify-center">
                                <div className="w-full max-w-lg flex flex-col items-center justify-center gap-6 animate-fade-in py-8">
                                    <div className="text-center space-y-2">
                                        <div className="text-5xl">{currentPhase === 'complete' ? '\u{2705}' : '\u{1F4CA}'}</div>
                                        <h3 className="text-lg font-bold text-white">
                                            {currentPhase === 'complete' ? 'Proposal Complete' : 'Generating Proposal...'}
                                        </h3>
                                        <p className="text-sm text-gray-400">
                                            {currentPhase === 'complete'
                                                ? 'Your TVO proposal deck is ready. Download it below.'
                                                : 'Creating your PowerPoint deck...'}
                                        </p>
                                    </div>
                                    <ExportButton sessionId={sessionId} ready={currentPhase === 'complete' || currentPhase === 'generation'} />
                                </div>
                            </div>
                        )}

                        {/* Agent insight in full-width for single-column */}
                        {(agentInsight || isStreaming) && (
                            <div className="max-w-3xl mx-auto">
                                <div className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ backgroundColor: `var(--color-phase-${currentPhase})` }} />
                                    Agent Analysis
                                </div>
                                <div className="rounded-2xl border border-gray-700/40 bg-gray-800/20 p-6">
                                    {isStreaming && !agentInsight ? (
                                        <div className="flex items-center gap-3">
                                            <div className="flex gap-1">
                                                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                            </div>
                                            <span className="text-sm text-gray-500">Generating analysis...</span>
                                        </div>
                                    ) : (
                                        <RichMarkdown content={agentInsight} phase={currentPhase} />
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Input & Footer Actions */}
            <div className="border-t border-gray-800 bg-gray-900 shadow-lg">
                <InputBar
                    onSend={onNext}
                    disabled={isStreaming || currentPhase === 'complete'}
                    placeholder={config?.placeholder}
                    quickChips={config?.chips}
                />
                <div className="px-8 py-4 bg-gray-950/50 flex justify-between items-center">
                    <button
                        onClick={() => prevPhase && onBack(prevPhase)}
                        disabled={!prevPhase || isStreaming}
                        className="px-6 py-2.5 rounded-lg font-medium text-sm text-gray-300 bg-gray-800 hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors focus:ring-2 focus:ring-gray-600 outline-none"
                    >
                        Previous Step
                    </button>

                    {currentPhase !== 'complete' && (
                    <button
                        onClick={handleNextClick}
                        disabled={!canContinue}
                        className="px-8 py-2.5 rounded-lg font-semibold text-sm text-white shadow-md disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:-translate-y-0.5 focus:ring-2 outline-none"
                        style={{ backgroundColor: `var(--color-phase-${currentPhase})`, boxShadow: `0 4px 20px -5px var(--color-phase-${currentPhase})` }}
                    >
                        {isStreaming ? 'Processing...' : nextPhaseLabel ? `Continue to ${nextPhaseLabel}` : 'Generate Deck'}
                    </button>
                    )}
                </div>
            </div>
        </div>
    );
}
