import { AgentState } from '@/types';
import { cn } from '@/lib/utils';
import { AGENTS } from '@/lib/agents';

interface AgentPanelProps {
  agentStates: Record<string, AgentState['status']>;
}

export default function AgentPanel({ agentStates }: AgentPanelProps) {
  return (
    <div className="flex flex-col flex-1 overflow-y-auto custom-scrollbar">
      {AGENTS.map((agent) => {
        const status = agentStates[agent.id] || 'idle';
        const isThinking = status === 'thinking';
        const isDone = status === 'done';
        const Icon = agent.Icon;

        return (
          <div
            key={agent.id}
            className={cn(
              "group flex items-center gap-4 p-4 border-l-2 transition-all duration-300 relative overflow-hidden",
              isThinking
                ? "border-accent-blue bg-accent-blue/5"
                : isDone
                  ? "border-accent-green bg-accent-green/5"
                  : "border-transparent opacity-60 hover:opacity-100 hover:bg-bg-hover"
            )}
          >
            {/* Active Background Slide */}
            <div className={cn(
              "absolute inset-0 bg-accent-blue/5 transform transition-transform duration-500 origin-left",
              isThinking ? "scale-x-100" : "scale-x-0"
            )} />

            {/* Icon Container */}
            <div className={cn(
              "relative z-10 w-12 h-12 border sharp-corners transition-colors duration-300 flex items-center justify-center bg-bg-elevated",
              isThinking ? "border-accent-blue" : isDone ? "border-accent-green" : "border-border-default group-hover:border-border-default"
            )}>
              <Icon className={cn("w-6 h-6", agent.color)} />
              {isThinking && (
                <div className="absolute inset-0 animate-pulse-blue opacity-50" />
              )}
            </div>

            <div className="flex flex-col relative z-10 flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <span className={cn(
                  "font-mono text-sm tracking-wide transition-colors font-semibold",
                  isThinking ? "text-accent-blue" : "text-text-primary"
                )}>
                  {agent.name}
                </span>
                {/* Status Dot */}
                {isThinking && (
                  <div className="w-2 h-2 rounded-full bg-accent-green animate-pulse" />
                )}
                {isDone && (
                  <div className="w-2 h-2 rounded-full bg-accent-green" />
                )}
              </div>

              {/* LLM Badge */}
              <div className="mb-1">
                <span className="inline-block text-[10px] font-mono text-text-muted bg-bg-primary px-2 py-0.5 sharp-corners border border-border-muted">
                  {agent.llm}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className={cn(
                  "text-xs font-mono uppercase tracking-wider",
                  isThinking ? "text-accent-blue" : isDone ? "text-accent-green" : "text-text-secondary"
                )}>
                  {status === 'thinking' ? 'EVALUATING...' :
                   status === 'done' ? 'COMPLETE' : 'STANDING BY'}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
