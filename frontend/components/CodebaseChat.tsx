'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { queryChatStream } from '@/lib/api';
import { MessageSquare, Send, Loader2, FileCode2, ChevronDown, ChevronUp } from 'lucide-react';

// ── Types ─────────────────────────────────────────────────────────────────────

interface ChatSource {
  file: string;
  lines: string;
  type: string;
  name: string;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: ChatSource[];
  isStreaming?: boolean;
}

interface CodebaseChatProps {
  analysisId: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function SourceBadge({ source }: { source: ChatSource }) {
  const label = source.name
    ? `${source.file}:${source.lines} (${source.name})`
    : `${source.file}:${source.lines}`;

  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 bg-bg-elevated border border-border-muted
                 text-text-muted font-mono text-xs sharp-corners"
      title={`${source.type} — ${label}`}
    >
      <FileCode2 className="w-3 h-3" />
      {label}
    </span>
  );
}

function SourcesList({ sources }: { sources: ChatSource[] }) {
  const [expanded, setExpanded] = useState(false);
  if (!sources.length) return null;

  return (
    <div className="mt-2">
      <button
        onClick={() => setExpanded(v => !v)}
        className="flex items-center gap-1 text-xs font-mono text-text-muted hover:text-text-secondary transition-colors"
      >
        {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        {sources.length} source{sources.length !== 1 ? 's' : ''}
      </button>
      {expanded && (
        <div className="mt-1 flex flex-wrap gap-1">
          {sources.map((s, i) => (
            <SourceBadge key={i} source={s} />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Very lightweight markdown renderer for code blocks and inline code.
 * Does not depend on remark/rehype to keep bundle size small.
 */
function RenderMarkdown({ text }: { text: string }) {
  const parts: React.ReactNode[] = [];
  // Split on fenced code blocks
  const segments = text.split(/(```[\s\S]*?```)/g);

  segments.forEach((seg, i) => {
    if (seg.startsWith('```')) {
      const firstNewline = seg.indexOf('\n');
      const lang = seg.slice(3, firstNewline).trim() || 'text';
      const code = seg.slice(firstNewline + 1, -3);
      parts.push(
        <pre
          key={i}
          className="my-2 p-3 bg-bg-elevated border border-border-muted sharp-corners overflow-x-auto text-xs font-mono text-text-primary"
        >
          <code data-lang={lang}>{code}</code>
        </pre>
      );
    } else {
      // Process inline code, bold, and line breaks
      const lines = seg.split('\n');
      lines.forEach((line, li) => {
        const inlineParts = line.split(/(`[^`]+`)/g).map((chunk, ci) => {
          if (chunk.startsWith('`') && chunk.endsWith('`')) {
            return (
              <code
                key={ci}
                className="px-1 py-0.5 bg-bg-elevated border border-border-muted font-mono text-xs text-accent-blue sharp-corners"
              >
                {chunk.slice(1, -1)}
              </code>
            );
          }
          // Bold
          const boldParts = chunk.split(/(\*\*[^*]+\*\*)/g).map((b, bi) => {
            if (b.startsWith('**') && b.endsWith('**')) {
              return <strong key={bi} className="font-semibold text-text-primary">{b.slice(2, -2)}</strong>;
            }
            return <span key={bi}>{b}</span>;
          });
          return <span key={ci}>{boldParts}</span>;
        });

        parts.push(
          <span key={`${i}-${li}`}>
            {inlineParts}
            {li < lines.length - 1 && <br />}
          </span>
        );
      });
    }
  });

  return <>{parts}</>;
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] px-4 py-3 sharp-corners text-sm leading-relaxed ${
          isUser
            ? 'bg-accent-blue/20 border border-accent-blue/40 text-text-primary'
            : 'bg-bg-elevated border border-border-default text-text-primary'
        }`}
      >
        {isUser ? (
          <span className="font-mono">{message.content}</span>
        ) : (
          <div className="font-mono text-xs leading-relaxed">
            <RenderMarkdown text={message.content} />
            {message.isStreaming && (
              <span className="inline-block w-1.5 h-3.5 bg-accent-blue animate-pulse ml-0.5" />
            )}
          </div>
        )}
        {!isUser && message.sources && message.sources.length > 0 && (
          <SourcesList sources={message.sources} />
        )}
      </div>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function CodebaseChat({ analysisId }: CodebaseChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const msgIdCounter = useRef(0);

  const nextId = () => `msg-${++msgIdCounter.current}`;

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = useCallback(async () => {
    const question = input.trim();
    if (!question || isLoading) return;

    setInput('');
    setError(null);
    setIsLoading(true);

    const userMsg: ChatMessage = {
      id: nextId(),
      role: 'user',
      content: question,
    };

    const assistantMsgId = nextId();
    const assistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      sources: [],
      isStreaming: true,
    };

    setMessages(prev => [...prev, userMsg, assistantMsg]);

    try {
      let accumulated = '';
      let sources: ChatSource[] = [];

      await queryChatStream(
        analysisId,
        question,
        (eventType, data) => {
          if (eventType === 'sources') {
            sources = (data.sources as ChatSource[]) ?? [];
            setMessages(prev =>
              prev.map(m =>
                m.id === assistantMsgId ? { ...m, sources } : m
              )
            );
          } else if (eventType === 'token') {
            accumulated += (data.token as string) ?? '';
            setMessages(prev =>
              prev.map(m =>
                m.id === assistantMsgId
                  ? { ...m, content: accumulated, isStreaming: true }
                  : m
              )
            );
          } else if (eventType === 'error') {
            setError((data.error as string) ?? 'An error occurred');
          } else if (eventType === 'done') {
            setMessages(prev =>
              prev.map(m =>
                m.id === assistantMsgId ? { ...m, isStreaming: false } : m
              )
            );
          }
        }
      );
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Query failed';
      setError(errMsg);
      setMessages(prev => prev.filter(m => m.id !== assistantMsgId));
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }, [analysisId, input, isLoading]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full border-t border-border-default bg-bg-surface">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border-default bg-bg-elevated">
        <MessageSquare className="w-4 h-4 text-accent-blue" />
        <h3 className="font-headline text-sm tracking-wide text-accent-blue">CODEBASE CHAT</h3>
        <span className="ml-auto text-xs font-mono text-text-muted">
          Ask questions about the analysed codebase
        </span>
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 min-h-0"
      >
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-text-muted">
            <MessageSquare className="w-8 h-8 mb-3 opacity-30" />
            <p className="font-mono text-xs leading-relaxed max-w-xs">
              Analysis complete. Ask questions about the codebase — architecture,
              security findings, specific files, or anything you want to explore.
            </p>
            <div className="mt-4 space-y-2 text-left">
              {[
                'How is authentication handled?',
                'Where are the API endpoints defined?',
                'What are the main security issues?',
              ].map(suggestion => (
                <button
                  key={suggestion}
                  onClick={() => { setInput(suggestion); inputRef.current?.focus(); }}
                  className="block w-full text-left px-3 py-2 text-xs font-mono border border-border-muted
                             bg-bg-elevated hover:border-accent-blue/50 hover:text-text-primary
                             sharp-corners transition-colors text-text-secondary"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map(msg => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
      </div>

      {/* Error bar */}
      {error && (
        <div className="mx-4 mb-2 px-3 py-2 bg-accent-red/10 border-l-2 border-accent-red text-accent-red font-mono text-xs sharp-corners">
          {error}
        </div>
      )}

      {/* Input */}
      <div className="px-4 py-3 border-t border-border-default bg-bg-elevated flex items-end gap-2">
        <textarea
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about the codebase… (Enter to send, Shift+Enter for newline)"
          rows={2}
          disabled={isLoading}
          className="flex-1 resize-none bg-bg-primary border border-border-default text-text-primary
                     font-mono text-xs px-3 py-2 sharp-corners placeholder:text-text-muted
                     focus:outline-none focus:border-accent-blue/60 disabled:opacity-50 transition-colors"
        />
        <button
          onClick={sendMessage}
          disabled={isLoading || !input.trim()}
          className="flex items-center justify-center w-10 h-10 bg-accent-blue text-white
                     sharp-corners hover:bg-accent-blue/80 disabled:opacity-40 disabled:cursor-not-allowed
                     transition-colors flex-none"
          aria-label="Send"
        >
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </button>
      </div>
    </div>
  );
}
