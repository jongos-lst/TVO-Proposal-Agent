import { useEffect, useRef } from 'react';
import type { Message, Phase } from '../../types';
import MessageBubble from './MessageBubble';
import InputBar from './InputBar';
import { PHASE_CONFIG } from '../../config/PhaseConfig';

interface Props {
  messages: Message[];
  isStreaming: boolean;
  onSend: (message: string) => void;
  currentPhase: Phase;
}

export default function ChatContainer({ messages, isStreaming, onSend, currentPhase }: Props) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentPhase]);

  const config = PHASE_CONFIG[currentPhase];

  return (
    <div className="flex flex-col h-full bg-gray-950">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 chat-scroll relative">
        <div className="max-w-4xl mx-auto flex flex-col gap-2">

          {/* Top Phase Header for Context */}
          {currentPhase !== 'intake' && (
            <div className={`mb-8 p-4 rounded-xl border border-gray-800 bg-gray-900/50 backdrop-blur-sm shadow-sm flex items-start gap-4 animate-slide-down relative overflow-hidden`}>
              <div className={`absolute top-0 bottom-0 left-0 w-1.5 ${config.bgAccentClass}`} />

              <div className={`text-3xl bg-gray-800 p-3 rounded-lg border border-gray-700/50 shadow-sm`}>
                {config.icon}
              </div>
              <div className="pt-1">
                <div className={`text-xs font-bold uppercase tracking-wider mb-1 ${config.accentClass}`}>
                  Phase {['intake', 'recommendation', 'calculation', 'review', 'generation', 'complete'].indexOf(currentPhase)}
                </div>
                <h2 className="text-xl font-bold text-white mb-1.5">{config.label}</h2>
                <p className="text-sm text-gray-400">{config.description}</p>
              </div>
            </div>
          )}

          {/* Empty State Help */}
          {messages.length === 0 && (
            <div className="text-center text-gray-500 mt-10">
              <p className="text-sm max-w-md mx-auto">
                No messages yet. Send a message to start working on the {config.label.toLowerCase()}.
              </p>
            </div>
          )}

          {/* Message List */}
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          <div ref={messagesEndRef} className="h-4" />
        </div>
      </div>

      {/* Input Form with specific Config Data */}
      <InputBar
        onSend={onSend}
        disabled={isStreaming || currentPhase === 'complete'}
        placeholder={isStreaming ? 'Agent is responding...' : config.placeholder}
        quickChips={config.chips}
        accentClass={config.accentClass.replace('text-', 'text-white bg-').replace('phase-', 'phase-')}
      />
    </div>
  );
}
