import { useMemo, useCallback } from 'react';
import { useChat } from './hooks/useChat';
import type { Phase } from './types';
import PhaseIndicator from './components/layout/PhaseIndicator';
import IntakeForm from './components/phases/IntakeForm';
import WizardContainer from './components/wizard/WizardContainer';

function App() {
  const sessionId = useMemo(() => crypto.randomUUID(), []);
  const { messages, isStreaming, proposal, sendMessage, submitPersona, goToPhase, showConfirmation, setShowConfirmation, confirmCalculation, approveAndGenerate } = useChat(sessionId);

  const isIntakePhase = proposal.phase === 'intake';

  const handlePhaseClick = useCallback((phase: Phase) => {
    if (isStreaming) return;
    goToPhase(phase);
  }, [isStreaming, goToPhase]);

  return (
    <div className="h-screen flex bg-gray-950 text-white font-sans">
      {/* Sidebar */}
      <aside className="w-80 bg-gray-900 border-r border-gray-800 flex flex-col shadow-xl z-10 relative">
        {/* Logo */}
        <div className="p-6 border-b border-gray-800 bg-gray-900/80 backdrop-blur-md sticky top-0 z-20">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-gradient-to-br from-getac-light to-getac-blue flex items-center justify-center text-white font-bold tracking-tighter">
              G
            </div>
            <div>
              <h1 className="text-lg font-bold text-white leading-tight">Getac</h1>
              <p className="text-xs text-getac-light font-medium tracking-wide uppercase">TVO Proposal Agent</p>
            </div>
          </div>
        </div>

        {/* Dynamic sidebar content */}
        <div className="flex-1 overflow-y-auto chat-scroll flex flex-col divide-y divide-gray-800/60 p-6">
          <PhaseIndicator currentPhase={proposal.phase} proposal={proposal} onPhaseClick={handlePhaseClick} />
        </div>
      </aside>

      {/* Main area */}
      <main className="flex-1 flex flex-col bg-gray-950 relative overflow-hidden z-0">
        {/* Subtle background glow effect based on phase */}
        {!isIntakePhase && (
          <div
            className="absolute top-[-20%] right-[-10%] w-[600px] h-[600px] rounded-full blur-[120px] pointer-events-none opacity-20 z-[-1] transition-colors duration-1000"
            style={{ backgroundColor: `var(--color-phase-${proposal.phase})` }}
          />
        )}

        {isIntakePhase ? (
          <IntakeForm onSubmit={submitPersona} isSubmitting={isStreaming} initialData={proposal.persona} />
        ) : (
          <WizardContainer
            messages={messages}
            isStreaming={isStreaming}
            onNext={sendMessage}
            onBack={goToPhase}
            proposal={proposal}
            sessionId={sessionId}
            showConfirmation={showConfirmation}
            setShowConfirmation={setShowConfirmation}
            confirmCalculation={confirmCalculation}
            approveAndGenerate={approveAndGenerate}
          />
        )}
      </main>
    </div>
  );
}

export default App;
