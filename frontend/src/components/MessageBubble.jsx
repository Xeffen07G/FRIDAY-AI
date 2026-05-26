import { memo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

function MessageBubble({ message, isLatest = false }) {
  const isUser = message.sender === 'user';
  
  const isDeterministic = !isUser && message.text && message.text.includes('[DETERMINISTIC_RESPONSE]');
  const isGenerative = !isUser && message.text && message.text.includes('[GENERATIVE_RESPONSE]');
  
  // Clean text by stripping the prefix for display
  let cleanText = message.text || '';
  if (isDeterministic) {
    cleanText = cleanText.replace('[DETERMINISTIC_RESPONSE]', '').trim();
  } else if (isGenerative) {
    cleanText = cleanText.replace('[GENERATIVE_RESPONSE]', '').trim();
  }

  return (
    <div className={`w-full py-2 select-text animate-in fade-in duration-[240ms] ease-out-calm text-left`}>
      {isUser ? (
        <div className="flex items-start gap-3 font-mono text-sm text-slate-300 select-all font-semibold">
          <span className="text-blue-500 select-none">&gt;</span>
          <div className="whitespace-pre-wrap leading-relaxed tracking-tight">{cleanText}</div>
        </div>
      ) : (
        <div className="font-sans text-[15px] leading-[1.75] text-slate-300 max-w-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ node, inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <div className="my-6 rounded-xl overflow-hidden bg-[#0a0c10] border border-white/[0.05] shadow-xl select-all">
                    <div className="flex items-center justify-between px-4 py-2 bg-[#050608] border-b border-white/[0.02] text-[10px] font-mono text-slate-500">
                      <span>{match[1]}</span>
                    </div>
                    <SyntaxHighlighter
                       style={vscDarkPlus}
                       language={match[1]}
                       PreTag="div"
                       customStyle={{ margin: 0, padding: '1rem', background: 'transparent', fontSize: '13px', fontFamily: "'JetBrains Mono', monospace" }}
                       wrapLongLines={true}
                       {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  </div>
                ) : (
                  <code className="bg-[#101318] text-blue-300/90 px-1.5 py-0.5 rounded text-[12px] font-mono whitespace-pre-wrap border border-white/[0.03]" {...props}>
                    {children}
                  </code>
                );
              },
              p({ children }) {
                return <p className="mb-4 last:mb-0 leading-[1.75] text-slate-300 text-[15px]">{children}</p>;
              },
              ul({ children }) {
                return <ul className="list-disc pl-5 mb-4 space-y-2 marker:text-slate-600 text-slate-300 text-[15px]">{children}</ul>;
              },
              ol({ children }) {
                return <ol className="list-decimal pl-5 mb-4 space-y-2 marker:text-slate-600 text-slate-300 text-[15px]">{children}</ol>;
              },
              h1({ children }) {
                return <h1 className="text-[20px] font-semibold mb-4 mt-8 text-slate-100 tracking-tight font-heading">{children}</h1>;
              },
              h2({ children }) {
                return <h2 className="text-[17px] font-semibold mb-3 mt-6 text-slate-100 tracking-tight font-heading">{children}</h2>;
              },
              h3({ children }) {
                return <h3 className="text-[15px] font-semibold mb-2 mt-4 text-slate-200 font-heading">{children}</h3>;
              },
              a({ children, href }) {
                return <a href={href} target="_blank" rel="noreferrer" className="text-blue-400 hover:text-blue-300 underline underline-offset-4 decoration-blue-500/30 transition-colors">{children}</a>;
              },
              blockquote({ children }) {
                return <blockquote className="border-l-2 border-blue-500/50 pl-4 italic text-slate-400 my-5 py-1">{children}</blockquote>;
              },
              strong({ children }) {
                return <strong className="font-semibold text-slate-200">{children}</strong>;
              }
            }}
          >
            {cleanText}
          </ReactMarkdown>
          {message.streaming && (
            <span className="inline-block w-1.5 h-4 ml-1 bg-slate-400 animate-pulse align-middle rounded-sm"></span>
          )}
        </div>
      )}
    </div>
  );
}

export default memo(MessageBubble);

