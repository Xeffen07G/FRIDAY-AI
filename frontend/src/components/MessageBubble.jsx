import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

export default function MessageBubble({ message }) {
  const isUser = message.sender === 'user';
  
  return (
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div 
        className={`max-w-[85%] p-5 rounded-2xl leading-relaxed text-[15px] shadow-sm overflow-hidden ${
          isUser 
            ? 'bg-blue-600 text-white rounded-br-sm shadow-blue-900/20' 
            : 'bg-slate-800 text-slate-200 border border-slate-700/50 rounded-bl-sm'
        }`}
      >
        {isUser ? (
          <div className="whitespace-pre-wrap">{message.text}</div>
        ) : (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ node, inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <div className="my-5 rounded-xl overflow-hidden bg-[#1e1e1e] border border-slate-700/80 shadow-lg">
                    <div className="flex items-center justify-between px-4 py-2 bg-slate-900/80 border-b border-slate-700/80 text-xs font-mono text-slate-400">
                      <span>{match[1]}</span>
                    </div>
                    <SyntaxHighlighter
                      style={vscDarkPlus}
                      language={match[1]}
                      PreTag="div"
                      customStyle={{ margin: 0, padding: '1.25rem', background: 'transparent' }}
                      wrapLongLines={true}
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  </div>
                ) : (
                  <code className="bg-slate-900/80 text-blue-300 px-1.5 py-0.5 rounded text-sm font-mono whitespace-pre-wrap" {...props}>
                    {children}
                  </code>
                );
              },
              p({ children }) {
                return <p className="mb-4 last:mb-0 leading-loose">{children}</p>;
              },
              ul({ children }) {
                return <ul className="list-disc pl-6 mb-4 space-y-2 marker:text-slate-500">{children}</ul>;
              },
              ol({ children }) {
                return <ol className="list-decimal pl-6 mb-4 space-y-2 marker:text-slate-500">{children}</ol>;
              },
              h1({ children }) {
                return <h1 className="text-2xl font-bold mb-4 mt-6 text-slate-50 tracking-wide">{children}</h1>;
              },
              h2({ children }) {
                return <h2 className="text-xl font-bold mb-3 mt-5 text-slate-50 tracking-wide">{children}</h2>;
              },
              h3({ children }) {
                return <h3 className="text-lg font-bold mb-2 mt-4 text-slate-50">{children}</h3>;
              },
              a({ children, href }) {
                return <a href={href} target="_blank" rel="noreferrer" className="text-blue-400 hover:text-blue-300 underline underline-offset-4 decoration-blue-500/30 transition-colors">{children}</a>;
              },
              blockquote({ children }) {
                return <blockquote className="border-l-4 border-slate-600/70 pl-4 italic text-slate-400 my-5 bg-slate-900/30 py-2 pr-4 rounded-r-lg">{children}</blockquote>;
              },
              strong({ children }) {
                return <strong className="font-semibold text-slate-50">{children}</strong>;
              }
            }}
          >
            {message.text}
          </ReactMarkdown>
        )}
        
        {/* Metadata Footer for Assistant */}
        {!isUser && message.text && (
          <div className="mt-4 pt-3 border-t border-slate-700/50 flex items-center justify-between text-[10px] text-slate-500 font-mono select-none">
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1.5 font-medium text-slate-400">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500/80 shadow-[0_0_4px_#10b981]"></div>
                Qwen2.5:3b
              </span>
              <span className="text-slate-600">•</span>
              <span>~{Math.max(1, Math.ceil(message.text.length / 4))} tkns</span>
            </div>
            { (message.created_at || message.id) && (
              <span className="opacity-75">
                {(() => {
                  try {
                    const date = new Date(message.created_at || message.id);
                    return isNaN(date.getTime()) ? "" : date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                  } catch (e) { return ""; }
                })()}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
