import { AgentMessage as AgentMessageType } from '@/types';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';
import { BookCheck, Users, Network, ShieldCheck, Scale, Terminal } from 'lucide-react';

interface AgentMessageProps {
  message: AgentMessageType;
}

// ── Agent metadata ────────────────────────────────────────────────────────────

const AGENT_CONFIG: Record<string, {
  icon: React.ComponentType<{ className?: string }>;
  iconColor: string;
  borderColor: string;
  labelColor: string;
  thinkingText: string;
}> = {
  standards_analyst: {
    icon: BookCheck,
    iconColor: 'text-accent-blue',
    borderColor: 'border-accent-blue',
    labelColor: 'text-accent-blue',
    thinkingText: 'Checking tech radar and pattern compliance…',
  },
  dx_analyst: {
    icon: Users,
    iconColor: 'text-accent-purple',
    borderColor: 'border-accent-purple',
    labelColor: 'text-accent-purple',
    thinkingText: 'Researching community health and adoption metrics…',
  },
  enterprise_architect: {
    icon: Network,
    iconColor: 'text-accent-green',
    borderColor: 'border-accent-green',
    labelColor: 'text-accent-green',
    thinkingText: 'Analysing integration impact and dependencies…',
  },
  security_analyst: {
    icon: ShieldCheck,
    iconColor: 'text-accent-amber',
    borderColor: 'border-accent-amber',
    labelColor: 'text-accent-amber',
    thinkingText: 'Evaluating threat surface and compliance requirements…',
  },
  da_chair: {
    icon: Scale,
    iconColor: 'text-accent-blue',
    borderColor: 'border-accent-blue',
    labelColor: 'text-accent-blue',
    thinkingText: 'Synthesising specialist assessments…',
  },
  system: {
    icon: Terminal,
    iconColor: 'text-text-muted',
    borderColor: 'border-border-muted',
    labelColor: 'text-text-muted',
    thinkingText: 'Initialising review…',
  },
};

const DEFAULT_CONFIG = AGENT_CONFIG.system;

function getConfig(agentId: string) {
  return AGENT_CONFIG[agentId] ?? DEFAULT_CONFIG;
}

// ── JSON detection and formatting ─────────────────────────────────────────────

function maybeWrapJson(content: string): string {
  const trimmed = content.trim();
  if ((trimmed.startsWith('{') || trimmed.startsWith('[')) && !trimmed.startsWith('```')) {
    // Try to pretty-print, fall back to raw if it's not valid JSON
    try {
      const parsed = JSON.parse(trimmed);
      return '```json\n' + JSON.stringify(parsed, null, 2) + '\n```';
    } catch {
      return '```json\n' + trimmed + '\n```';
    }
  }
  return content;
}

// ── Ruling outcome badge ──────────────────────────────────────────────────────

const RULING_BADGE: Record<string, string> = {
  APPROVED: 'bg-accent-green/15 text-accent-green border-accent-green',
  CONDITIONAL: 'bg-accent-amber/15 text-accent-amber border-accent-amber',
  REJECTED: 'bg-accent-red/15 text-accent-red border-accent-red',
  DEFERRED: 'bg-accent-grey/15 text-text-secondary border-border-default',
};

function extractRuling(content: string): string | null {
  const match = content.match(/\b(APPROVED|CONDITIONAL|REJECTED|DEFERRED)\b/i);
  return match ? match[1].toUpperCase() : null;
}

// ── Component ────────────────────────────────────────────────────────────────

export default function AgentMessage({ message }: AgentMessageProps) {
  const isThinking = message.message_type === 'thinking';
  const isRuling = message.message_type === 'ruling';
  const config = getConfig(message.agent_id);
  const IconComponent = config.icon;

  // Prepare content for rendering
  const renderedContent = isThinking ? '' : maybeWrapJson(message.content);
  const rulingOutcome = isRuling ? extractRuling(message.content) : null;

  if (isRuling) {
    // ── Ruling card — prominent treatment ─────────────────────────────────
    return (
      <div className="relative mb-6 animate-slide-in">
        {/* Connector */}
        <div className="absolute left-[-29px] top-6 w-6 h-[1px] bg-border-muted" />
        <div className="absolute left-[-32px] top-5 w-2 h-2 rounded-full border border-accent-blue bg-bg-primary" />

        <div className="border-2 border-accent-blue bg-bg-surface sharp-corners overflow-hidden">
          {/* Ruling header bar */}
          <div className="flex items-center justify-between px-5 py-3 bg-accent-blue/10 border-b-2 border-accent-blue">
            <div className="flex items-center gap-3">
              <div className="p-1.5 border border-accent-blue bg-bg-elevated sharp-corners">
                <IconComponent className={cn('w-5 h-5', config.iconColor)} />
              </div>
              <div>
                <div className="font-mono text-xs text-accent-blue font-bold uppercase tracking-widest">
                  Architecture Ruling
                </div>
                <div className="font-mono text-sm font-semibold text-text-primary leading-none mt-0.5">
                  {message.agent_name}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {rulingOutcome && (
                <span className={cn(
                  'font-mono text-xs font-bold uppercase tracking-widest px-3 py-1 sharp-corners border',
                  RULING_BADGE[rulingOutcome] ?? RULING_BADGE.DEFERRED
                )}>
                  {rulingOutcome}
                </span>
              )}
              <div className="font-mono text-xs text-text-muted">
                {new Date(message.timestamp).toLocaleTimeString([], { hour12: false })}
              </div>
            </div>
          </div>

          {/* Ruling body */}
          <div className="p-5">
            <div className="prose prose-sm max-w-none
              prose-p:my-2 prose-p:text-text-primary
              prose-headings:text-accent-blue prose-headings:font-mono prose-headings:font-semibold
              prose-strong:text-text-primary
              prose-ul:list-disc prose-li:marker:text-text-muted
              prose-code:text-accent-purple prose-code:bg-bg-elevated prose-code:px-1 prose-code:py-0.5 prose-code:rounded-sm prose-code:font-mono
              prose-pre:bg-bg-elevated prose-pre:border prose-pre:border-border-default prose-pre:sharp-corners
            ">
              <ReactMarkdown>{renderedContent}</ReactMarkdown>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ── Standard message card ─────────────────────────────────────────────────
  return (
    <div className={cn(
      "relative mb-4 animate-slide-in group",
      isThinking ? "opacity-70" : "opacity-100"
    )}>
      {/* Connector */}
      <div className="absolute left-[-29px] top-6 w-6 h-[1px] bg-border-muted" />
      <div className="absolute left-[-32px] top-5 w-2 h-2 rounded-full border border-border-default bg-bg-primary" />

      <div className={cn(
        "border-l-2 bg-bg-surface p-4 sharp-corners hover:bg-bg-elevated transition-colors",
        config.borderColor
      )}>
        {/* Header */}
        <div className="flex items-center justify-between mb-3 pb-2 border-b border-border-muted">
          <div className="flex items-center gap-3">
            <div className="p-1.5 border border-border-default bg-bg-elevated sharp-corners">
              <IconComponent className={cn('w-5 h-5', config.iconColor)} />
            </div>
            <div>
              <div className="font-mono text-sm font-semibold text-text-primary leading-none">
                {message.agent_name}
              </div>
              <div className={cn("font-mono text-[10px] uppercase tracking-wider mt-1", config.labelColor)}>
                {isThinking ? 'Evaluating' : 'Assessment'}
              </div>
            </div>
          </div>
          <div className="font-mono text-xs text-text-muted">
            {new Date(message.timestamp).toLocaleTimeString([], { hour12: false })}
          </div>
        </div>

        {/* Content */}
        <div className="font-mono text-sm text-text-primary leading-relaxed">
          {isThinking ? (
            <div className="flex items-center gap-2 text-text-secondary animate-pulse">
              <span className={cn("w-2 h-2 rounded-full", config.iconColor.replace('text-', 'bg-'))} />
              <span className="tracking-wide text-xs">{config.thinkingText}</span>
            </div>
          ) : (
            <div className="prose prose-sm max-w-none
              prose-p:my-2 prose-p:text-text-primary
              prose-headings:text-accent-blue prose-headings:font-mono prose-headings:font-semibold
              prose-strong:text-text-primary
              prose-ul:list-disc prose-li:marker:text-text-muted
              prose-code:text-accent-purple prose-code:bg-bg-elevated prose-code:px-1 prose-code:py-0.5 prose-code:rounded-sm prose-code:font-mono
              prose-pre:bg-bg-elevated prose-pre:border prose-pre:border-border-default prose-pre:sharp-corners
            ">
              <ReactMarkdown>{renderedContent}</ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
