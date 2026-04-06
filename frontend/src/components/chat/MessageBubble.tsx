import type { Message } from '../../types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Props {
  message: Message;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-5`}>
      {/* Container with conditional layout */}
      <div
        className={`max-w-[85%] sm:max-w-[75%] rounded-2xl px-5 py-4 shadow-sm backdrop-blur-md transition-all ${isUser
          ? 'bg-gray-800 text-white rounded-br-sm border border-gray-700'
          : 'bg-gray-800/80 text-gray-100 rounded-bl-sm border border-gray-700/50'
          }`}
      >
        {!isUser && (
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-bold text-gray-400 tracking-wider uppercase">TVO Agent</span>
          </div>
        )}

        <div className="text-sm leading-relaxed text-gray-200">
          {message.content ? (
            <div className="prose prose-sm prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-gray-900 prose-pre:border prose-pre:border-gray-700 prose-th:px-3 prose-th:py-2 prose-td:px-3 prose-td:py-2 prose-tr:border-b prose-tr:border-gray-700/50 prose-table:my-4 prose-th:text-left prose-table:w-full prose-a:text-getac-light hover:prose-a:text-white transition-colors">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          ) : (
            <span className="inline-flex gap-1 h-5 items-center">
              <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
