'use client';

import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { AgentMessage, RepoMetadata } from '@/types';
import CodebaseStream from './CodebaseStream';
import ConversationStream from './ConversationStream';
import { cn } from '@/lib/utils';
import { PROSE_CLASSES } from '@/lib/prose';
import { AGENT_MAP } from '@/lib/agents';

interface TabbedAgentOutputProps {
  messages: AgentMessage[];
  repoMetadata?: RepoMetadata | null;
  isAnalysing: boolean;
  mode?: 'adr' | 'codebase';
}

type TabId = 'live' | 'standards' | 'dx' | 'architecture' | 'security' | 'ruling';

interface TabConfig {
  id: TabId;
  label: string;
  agentId?: string;  // undefined = live feed
}

const TABS: TabConfig[] = [
  { id: 'live',         label: 'LIVE FEED' },
  { id: 'standards',   label: 'STANDARDS',    agentId: 'standards_analyst' },
  { id: 'dx',          label: 'DX',           agentId: 'dx_analyst' },
  { id: 'architecture',label: 'ARCHITECTURE', agentId: 'enterprise_architect' },
  { id: 'security',    label: 'SECURITY',     agentId: 'security_analyst' },
  { id: 'ruling',      label: 'RULING',       agentId: 'da_chair' },
];

// Tailwind JIT-safe active tab styles — full class strings required (no interpolation)
const TAB_ACTIVE_STYLES: Record<TabId, string> = {
  live:         'text-accent-blue border-b-2 border-accent-blue',
  standards:    'text-accent-blue border-b-2 border-accent-blue',
  dx:           'text-accent-purple border-b-2 border-accent-purple',
  architecture: 'text-accent-green border-b-2 border-accent-green',
  security:     'text-accent-amber border-b-2 border-accent-amber',
  ruling:       'text-accent-blue border-b-2 border-accent-blue',
};

// Agent theme configuration is now sourced from the shared AGENT_MAP in @/lib/agents
// to keep model labels and colours in a single place.

type DotState = 'idle' | 'thinking' | 'done';

function getDotState(messages: AgentMessage[], agentId: string): DotState {
  const agentMsgs = messages.filter(m => m.agent_id === agentId);
  if (agentMsgs.some(m => m.message_type === 'analysis' || m.message_type === 'ruling')) {
    return 'done';
  }
  if (agentMsgs.some(m => m.message_type === 'thinking')) {
    return 'thinking';
  }
  return 'idle';
}

function DotIndicator({ state }: { state: DotState }) {
  return (
    <span
      className={cn(
        'inline-block w-1.5 h-1.5 rounded-full ml-1.5',
        state === 'idle'    && 'bg-text-muted',
        state === 'thinking'&& 'bg-accent-blue animate-pulse',
        state === 'done'    && 'bg-accent-green',
      )}
    />
  );
}

function AgentTabContent({ messages, agentId }: { messages: AgentMessage[]; agentId: string }) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const agent = AGENT_MAP[agentId];

  const agentMessages = messages.filter(
    m => m.agent_id === agentId && (m.message_type === 'analysis' || m.message_type === 'ruling')
  );

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (agentMessages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-text-muted">
        <p className="text-sm font-mono tracking-wide">Awaiting agent output...</p>
      </div>
    );
  }

  // Build agent-specific prose classes: replace the default heading colour
  // with this agent's accent colour
  const agentProseClasses = agent
    ? PROSE_CLASSES.replace('prose-headings:text-accent-blue', agent.headingColor)
    : PROSE_CLASSES;

  return (
    <div className="flex-1 overflow-y-auto custom-scrollbar">
      {/* Agent header banner */}
      {agent && (
        <div className={cn(
          'sticky top-0 z-10 px-6 py-3 border-b flex items-center gap-3',
          agent.bgColor, agent.borderColor
        )}>
          <div className={cn('font-mono text-sm font-bold uppercase tracking-wider', agent.accentColor)}>
            {agent.name}
          </div>
          <div className="text-text-muted font-mono text-xs">
            {agent.subtitle}
          </div>
        </div>
      )}

      {/* Report content */}
      <div className="px-6 py-4">
        {agentMessages.map((msg, i) => (
          <div key={i} className={agentProseClasses}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {msg.content}
            </ReactMarkdown>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

export default function TabbedAgentOutput({ messages, repoMetadata, isAnalysing, mode = 'codebase' }: TabbedAgentOutputProps) {
  const [activeTab, setActiveTab] = useState<TabId>('live');
  const wasAnalysingRef = useRef(isAnalysing);

  // Auto-switch to RULING tab when analysis completes
  useEffect(() => {
    if (wasAnalysingRef.current && !isAnalysing) {
      // Just transitioned from analysing -> done
      const hasRuling = messages.some(m => m.agent_id === 'da_chair' && m.message_type === 'ruling');
      if (hasRuling) {
        setActiveTab('ruling');
      }
    }
    wasAnalysingRef.current = isAnalysing;
  }, [isAnalysing, messages]);

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Sticky tab bar */}
      <div className="flex-none flex gap-0 border-b border-border-default bg-bg-surface sticky top-0 z-10">
        {TABS.map(tab => {
          const dotState = tab.agentId ? getDotState(messages, tab.agentId) : 'idle';
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'px-3 py-2 text-xs font-mono uppercase tracking-wider transition-colors flex items-center whitespace-nowrap',
                isActive
                  ? TAB_ACTIVE_STYLES[tab.id]
                  : 'text-text-muted hover:text-text-secondary border-b-2 border-transparent'
              )}
            >
              {tab.label}
              {tab.agentId && <DotIndicator state={dotState} />}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div className="flex-1 flex flex-col min-h-0">
        {activeTab === 'live' && (
          mode === 'adr'
            ? <ConversationStream messages={messages} />
            : <CodebaseStream messages={messages} repoMetadata={repoMetadata} />
        )}
        {TABS.filter(t => t.agentId).map(tab => (
          activeTab === tab.id && tab.agentId ? (
            <AgentTabContent key={tab.id} messages={messages} agentId={tab.agentId} />
          ) : null
        ))}
      </div>
    </div>
  );
}
