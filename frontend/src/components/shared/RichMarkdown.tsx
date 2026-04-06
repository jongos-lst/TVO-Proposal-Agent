import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Components } from 'react-markdown';
import type { Phase } from '../../types';

interface Props {
  content: string;
  phase?: Phase;
}

/**
 * Rich markdown renderer that transforms standard markdown into styled UI panels.
 * Tables become bordered cards, headings become section headers, lists become styled items.
 */
export default function RichMarkdown({ content, phase }: Props) {
  const accentColor = phase ? `var(--color-phase-${phase})` : 'var(--color-phase-recommendation)';

  const components: Components = {
    // Tables rendered as styled cards
    table: ({ children }) => (
      <div className="my-4 rounded-xl border border-gray-700/60 bg-gray-800/40 overflow-hidden shadow-sm">
        <table className="w-full text-sm">
          {children}
        </table>
      </div>
    ),
    thead: ({ children }) => (
      <thead className="bg-gray-800/80 border-b border-gray-700/50">
        {children}
      </thead>
    ),
    th: ({ children }) => (
      <th className="px-4 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
        {children}
      </th>
    ),
    tbody: ({ children }) => (
      <tbody className="divide-y divide-gray-800/60">
        {children}
      </tbody>
    ),
    tr: ({ children }) => (
      <tr className="hover:bg-gray-800/40 transition-colors">
        {children}
      </tr>
    ),
    td: ({ children }) => {
      const text = String(children ?? '');
      // Highlight savings/positive values
      const isPositive = /^\+?\$[\d,]+/.test(text) || /^\d+(\.\d+)?%$/.test(text);
      const isCurrency = /^\$[\d,]+/.test(text);
      return (
        <td className={`px-4 py-3 ${isCurrency ? 'font-mono' : ''} ${isPositive ? 'text-green-400 font-semibold' : 'text-gray-200'}`}>
          {children}
        </td>
      );
    },

    // Headings as section dividers with accent
    h3: ({ children }) => (
      <div className="flex items-center gap-2 mt-6 mb-3">
        <div
          className="w-1 h-5 rounded-full"
          style={{ backgroundColor: accentColor }}
        />
        <h3 className="text-base font-bold text-white">{children}</h3>
      </div>
    ),
    h4: ({ children }) => (
      <h4 className="text-sm font-semibold text-gray-300 mt-4 mb-2 uppercase tracking-wide">
        {children}
      </h4>
    ),

    // Paragraphs
    p: ({ children }) => (
      <p className="text-sm text-gray-300 leading-relaxed my-2">{children}</p>
    ),

    // Unordered lists as styled items
    ul: ({ children }) => (
      <ul className="my-3 space-y-1.5">{children}</ul>
    ),
    li: ({ children }) => (
      <li className="flex items-start gap-2 text-sm text-gray-300">
        <span className="mt-1.5 w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: accentColor }} />
        <span>{children}</span>
      </li>
    ),

    // Ordered lists
    ol: ({ children }) => (
      <ol className="my-3 space-y-1.5 counter-reset-item">{children}</ol>
    ),

    // Bold text with accent
    strong: ({ children }) => (
      <strong className="font-semibold text-white">{children}</strong>
    ),

    // Inline code
    code: ({ children, className }) => {
      const isBlock = className?.includes('language-');
      if (isBlock) {
        return (
          <code className={`${className} block bg-gray-900 border border-gray-700 rounded-lg p-4 text-xs text-gray-300 overflow-x-auto my-3`}>
            {children}
          </code>
        );
      }
      return (
        <code className="bg-gray-700/60 text-gray-200 px-1.5 py-0.5 rounded text-xs font-mono">
          {children}
        </code>
      );
    },

    // Blockquotes as highlight cards
    blockquote: ({ children }) => (
      <div
        className="my-4 rounded-xl border-l-4 bg-gray-800/30 px-4 py-3"
        style={{ borderColor: accentColor }}
      >
        {children}
      </div>
    ),

    // Horizontal rules as subtle dividers
    hr: () => (
      <hr className="my-4 border-gray-700/40" />
    ),
  };

  return (
    <div className="rich-markdown">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
