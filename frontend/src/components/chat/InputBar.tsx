import { useState, useRef } from 'react';
import type { KeyboardEvent } from 'react';

interface Props {
  onSend: (message: string) => void;
  disabled: boolean;
  placeholder?: string;
  quickChips?: string[];
  accentClass?: string;
}

export default function InputBar({ onSend, disabled, placeholder, quickChips, accentClass = 'text-getac-light' }: Props) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input);
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
    }
  };

  const handleChipClick = (chip: string) => {
    if (disabled) return;
    onSend(chip);
  };

  return (
    <div className="border-t border-gray-700 bg-gray-900 px-4 pb-4 pt-2">
      <div className="max-w-4xl mx-auto flex flex-col gap-2">
        {/* Quick action chips */}
        {quickChips && quickChips.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-1 animate-slide-down">
            {quickChips.map((chip, idx) => (
              <button
                key={idx}
                onClick={() => handleChipClick(chip)}
                disabled={disabled}
                className={`text-xs px-3 py-1.5 rounded-full border border-gray-700 bg-gray-800 hover:bg-gray-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed ${accentClass} hover:border-current`}
              >
                {chip}
              </button>
            ))}
          </div>
        )}

        {/* Input box */}
        <div className="flex gap-3 items-end">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => { setInput(e.target.value); handleInput(); }}
            onKeyDown={handleKeyDown}
            placeholder={placeholder || 'Type your message...'}
            disabled={disabled}
            rows={1}
            className="flex-1 bg-gray-800 text-white rounded-xl px-4 py-3 resize-none focus:outline-none focus:ring-2 focus:ring-gray-600 placeholder-gray-500 disabled:opacity-50 text-sm"
          />
          <button
            onClick={handleSend}
            disabled={disabled || !input.trim()}
            style={{ backgroundColor: 'var(--color-current)' }} // dynamic bg handled via wrapper class, actually we can just use the generic button styling
            className={`bg-gray-700 hover:bg-gray-600 text-white rounded-xl px-5 py-3 font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed text-sm`}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
