import type { Phase, ProposalState } from '../../types';
import { PHASE_CONFIG } from '../../config/PhaseConfig';

const phaseOrder: Phase[] = ['intake', 'recommendation', 'calculation', 'review', 'generation', 'complete'];

interface Props {
  currentPhase: Phase;
  proposal?: ProposalState;
  onPhaseClick?: (phase: Phase) => void;
}

/** Determine which phases have been completed based on actual data presence. */
function getCompletedPhases(proposal?: ProposalState): Set<Phase> {
  const completed = new Set<Phase>();
  if (!proposal) return completed;
  if (proposal.persona) completed.add('intake');
  if (proposal.selectedProducts?.length) completed.add('recommendation');
  if (proposal.tvoResults && Object.keys(proposal.tvoResults).length > 0) completed.add('calculation');
  if (proposal.proposalApproved) completed.add('review');
  if (proposal.pptxPath) completed.add('generation');
  return completed;
}

export default function PhaseIndicator({ currentPhase, proposal, onPhaseClick }: Props) {
  const currentIndex = phaseOrder.indexOf(currentPhase);
  const completedPhases = getCompletedPhases(proposal);

  return (
    <div className="space-y-0 relative">
      <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4 pb-2 border-b border-gray-800">
        Proposal Progress
      </h3>

      {/* Connecting vertical line underlying steps */}
      <div className="absolute left-[13px] top-[45px] bottom-[20px] w-[2px] bg-gray-800 rounded-full" />

      <div className="flex flex-col gap-4 relative z-10">
        {phaseOrder.map((phaseKey, index) => {
          const config = PHASE_CONFIG[phaseKey];
          const isComplete = currentPhase === 'complete' || completedPhases.has(phaseKey) || index < currentIndex;
          const isActive = phaseKey === currentPhase;
          const isClickable = isComplete && !isActive && onPhaseClick && phaseKey !== 'complete';

          let iconContent = config.icon;
          if (isComplete) iconContent = '✓';

          let bgClass = 'bg-gray-800 text-gray-500 border-gray-700';
          if (isComplete) bgClass = 'bg-green-500/20 text-green-400 border-green-500/30';
          if (isActive) bgClass = `${config.bgAccentClass} text-white border-transparent ring-4 ring-gray-900 shadow-lg`;

          return (
            <div
              key={phaseKey}
              className={`flex items-center gap-4 relative group ${isClickable ? 'cursor-pointer' : ''}`}
              onClick={() => isClickable && onPhaseClick(phaseKey)}
              role={isClickable ? 'button' : undefined}
              tabIndex={isClickable ? 0 : undefined}
              onKeyDown={e => isClickable && e.key === 'Enter' && onPhaseClick(phaseKey)}
            >
              <div
                className={`w-7 h-7 rounded bg-gray-900 border flex items-center justify-center text-xs font-bold transition-all duration-300 ${bgClass} ${isClickable ? 'group-hover:ring-2 group-hover:ring-green-500/40' : ''}`}
              >
                {iconContent}
              </div>

              <div className="flex flex-col">
                <span
                  className={`text-sm transition-colors ${isActive ? 'text-white font-semibold' : isComplete ? 'text-gray-300 group-hover:text-white' : 'text-gray-600'}`}
                >
                  {config.label}
                </span>
                {isActive && (
                  <span className={`text-[10px] ${config.accentClass} animate-pulse mt-0.5`}>
                    In Progress
                  </span>
                )}
                {isClickable && (
                  <span className="text-[10px] text-gray-600 group-hover:text-gray-400 mt-0.5 transition-colors">
                    Click to edit
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
