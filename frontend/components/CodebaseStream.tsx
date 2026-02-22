'use client';

import { useRef, useEffect } from 'react';
import { AgentMessage as AgentMessageType, RepoMetadata } from '@/types';
import AgentMessage from './AgentMessage';
import { GitBranch, FileCode2, Package, Layers, FileQuestion } from 'lucide-react';

interface CodebaseStreamProps {
  messages: AgentMessageType[];
  repoMetadata?: RepoMetadata | null;
}

function LanguageBar({ breakdown }: { breakdown: Record<string, number> }) {
  const total = Object.values(breakdown).reduce((a, b) => a + b, 0);
  if (total === 0) return null;

  const LANG_COLORS: Record<string, string> = {
    TypeScript: 'bg-[#3178C6]',
    JavaScript: 'bg-[#F7DF1E]',
    Python: 'bg-[#3572A5]',
    Go: 'bg-[#00ADD8]',
    Rust: 'bg-[#DEA584]',
    Java: 'bg-[#B07219]',
    CSS: 'bg-[#563D7C]',
    HTML: 'bg-[#E34C26]',
    Shell: 'bg-[#89E051]',
    Dockerfile: 'bg-[#384D54]',
  };

  const sorted = Object.entries(breakdown)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 6);

  return (
    <div>
      <div className="flex h-2 sharp-corners overflow-hidden mb-2">
        {sorted.map(([lang, count]) => (
          <div
            key={lang}
            className={`${LANG_COLORS[lang] || 'bg-accent-grey'} transition-all duration-700`}
            style={{ width: `${(count / total) * 100}%` }}
            title={`${lang}: ${((count / total) * 100).toFixed(1)}%`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-3">
        {sorted.map(([lang, count]) => (
          <div key={lang} className="flex items-center gap-1.5 text-xs font-mono text-text-secondary">
            <span className={`w-2 h-2 rounded-full inline-block ${LANG_COLORS[lang] || 'bg-accent-grey'}`} />
            <span>{lang}</span>
            <span className="text-text-muted">{((count / total) * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function RepoMetadataCards({ metadata }: { metadata: RepoMetadata }) {
  return (
    <div className="mb-6 space-y-4 animate-slide-in">
      {/* Repo header */}
      <div className="border border-accent-blue bg-accent-blue/5 sharp-corners p-4">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-1.5 border border-accent-blue bg-bg-elevated sharp-corners">
            <GitBranch className="w-4 h-4 text-accent-blue" />
          </div>
          <div>
            <div className="font-mono text-xs text-accent-blue uppercase tracking-widest font-bold">Repository Indexed</div>
            <div className="font-mono text-sm text-text-primary font-semibold mt-0.5 break-all">{metadata.repo_url}</div>
          </div>
        </div>
        <div className="font-mono text-xs text-text-muted">Branch: <span className="text-text-secondary">{metadata.branch || 'main'}</span></div>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-3 gap-3">
        <div className="border border-border-default bg-bg-surface sharp-corners p-3">
          <div className="flex items-center gap-2 mb-2">
            <FileCode2 className="w-4 h-4 text-accent-blue" />
            <span className="text-xs font-mono text-text-muted uppercase tracking-wider">Files</span>
          </div>
          <div className="text-2xl font-mono font-bold text-text-primary">{metadata.file_count.toLocaleString()}</div>
        </div>
        <div className="border border-border-default bg-bg-surface sharp-corners p-3">
          <div className="flex items-center gap-2 mb-2">
            <Package className="w-4 h-4 text-accent-purple" />
            <span className="text-xs font-mono text-text-muted uppercase tracking-wider">Deps</span>
          </div>
          <div className="text-2xl font-mono font-bold text-text-primary">{metadata.dependency_count.toLocaleString()}</div>
        </div>
        <div className="border border-border-default bg-bg-surface sharp-corners p-3">
          <div className="flex items-center gap-2 mb-2">
            <Layers className="w-4 h-4 text-accent-green" />
            <span className="text-xs font-mono text-text-muted uppercase tracking-wider">Languages</span>
          </div>
          <div className="text-2xl font-mono font-bold text-text-primary">
            {Object.keys(metadata.language_breakdown).length}
          </div>
        </div>
      </div>

      {/* Language breakdown */}
      {Object.keys(metadata.language_breakdown).length > 0 && (
        <div className="border border-border-default bg-bg-surface sharp-corners p-4">
          <div className="text-xs font-mono text-text-muted uppercase tracking-wider mb-3">Language Breakdown</div>
          <LanguageBar breakdown={metadata.language_breakdown} />
        </div>
      )}

      {/* Key files */}
      {metadata.key_files.length > 0 && (
        <div className="border border-border-default bg-bg-surface sharp-corners p-4">
          <div className="text-xs font-mono text-text-muted uppercase tracking-wider mb-2">Key Files Detected</div>
          <div className="flex flex-wrap gap-2">
            {metadata.key_files.map((f) => (
              <span key={f} className="text-xs font-mono text-accent-blue bg-accent-blue/10 border border-accent-blue/30 px-2 py-0.5 sharp-corners">
                {f}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function CodebaseStream({ messages, repoMetadata }: CodebaseStreamProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto px-8 py-6 custom-scrollbar relative">
      {/* Timeline Line */}
      {(messages.length > 0 || repoMetadata) && (
        <div className="absolute left-8 top-6 bottom-6 w-[1px] bg-border-muted" />
      )}

      {!repoMetadata && messages.length === 0 ? (
        <div className="h-full flex flex-col items-center justify-center text-text-muted">
          <div className="w-16 h-16 border border-border-default sharp-corners flex items-center justify-center mb-4 bg-bg-elevated">
            <FileQuestion className="w-8 h-8 text-accent-blue" />
          </div>
          <p className="text-xl font-mono font-semibold tracking-wide text-accent-blue">AWAITING SUBMISSION</p>
          <p className="text-xs font-mono tracking-wide mt-2">Submit a repository URL to begin codebase analysis</p>
        </div>
      ) : (
        <div className="pl-8">
          {repoMetadata && <RepoMetadataCards metadata={repoMetadata} />}
          {messages.map((msg, index) => (
            <AgentMessage key={`${msg.agent_id}-${index}`} message={msg} />
          ))}
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
