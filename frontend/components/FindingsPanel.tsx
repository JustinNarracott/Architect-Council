'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Finding, FindingSeverity, CodebaseRuling } from '@/types';
import { ChevronDown, ChevronRight, AlertTriangle, AlertOctagon, Info, Zap, FileCode2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface FindingsPanelProps {
  ruling: CodebaseRuling;
}

// ── Severity config ──────────────────────────────────────────────────────────

const SEVERITY_CONFIG: Record<FindingSeverity, {
  label: string;
  color: string;
  bg: string;
  border: string;
  icon: React.ComponentType<{ className?: string }>;
  order: number;
}> = {
  CRITICAL: {
    label: 'CRITICAL',
    color: 'text-accent-red',
    bg: 'bg-accent-red/10',
    border: 'border-accent-red',
    icon: AlertOctagon,
    order: 0,
  },
  HIGH: {
    label: 'HIGH',
    color: 'text-accent-amber',
    bg: 'bg-accent-amber/10',
    border: 'border-accent-amber',
    icon: AlertTriangle,
    order: 1,
  },
  MEDIUM: {
    label: 'MEDIUM',
    color: 'text-[#9A6700]',
    bg: 'bg-amber-50',
    border: 'border-[#9A6700]',
    icon: Zap,
    order: 2,
  },
  LOW: {
    label: 'LOW',
    color: 'text-accent-blue',
    bg: 'bg-accent-blue/10',
    border: 'border-accent-blue',
    icon: Info,
    order: 3,
  },
};

// ── Score display ─────────────────────────────────────────────────────────────

function ScoreGauge({ score }: { score: number }) {
  const pct = Math.max(0, Math.min(100, score));
  const color = pct >= 80 ? 'text-accent-green' : pct >= 60 ? 'text-accent-amber' : 'text-accent-red';
  const barColor = pct >= 80 ? 'bg-accent-green' : pct >= 60 ? 'bg-accent-amber' : 'bg-accent-red';

  return (
    <div className="flex items-center gap-4">
      <div className={cn('text-4xl font-mono font-bold', color)}>{pct}</div>
      <div className="flex-1">
        <div className="h-2 bg-bg-elevated sharp-corners overflow-hidden mb-1">
          <motion.div
            className={cn('h-full', barColor)}
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
          />
        </div>
        <div className="text-xs font-mono text-text-muted">Overall Health Score</div>
      </div>
    </div>
  );
}

// ── Single finding row ────────────────────────────────────────────────────────

function FindingRow({ finding }: { finding: Finding }) {
  const [expanded, setExpanded] = useState(false);
  const config = SEVERITY_CONFIG[finding.severity];
  const SeverityIcon = config.icon;

  return (
    <div className={cn('border sharp-corners overflow-hidden', config.border)}>
      <button
        onClick={() => setExpanded(!expanded)}
        className={cn(
          'w-full flex items-start gap-3 p-3 text-left transition-colors',
          config.bg,
          'hover:opacity-90'
        )}
      >
        <SeverityIcon className={cn('w-4 h-4 mt-0.5 flex-none', config.color)} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className="font-mono text-sm font-semibold text-text-primary leading-tight">
              {finding.title}
            </span>
            <div className="flex items-center gap-2 flex-none">
              <span className="text-xs font-mono text-text-muted">{finding.agent_source}</span>
              {expanded
                ? <ChevronDown className="w-3.5 h-3.5 text-text-muted" />
                : <ChevronRight className="w-3.5 h-3.5 text-text-muted" />
              }
            </div>
          </div>
          {!expanded && (
            <p className="text-xs font-mono text-text-secondary mt-1 line-clamp-1">{finding.description}</p>
          )}
        </div>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            className="overflow-hidden"
          >
            <div className="p-4 pt-3 space-y-3 border-t border-border-muted bg-bg-surface">
              {/* Description */}
              <div>
                <div className="text-xs font-mono text-text-muted uppercase tracking-wider mb-1">Description</div>
                <p className="text-sm font-mono text-text-primary leading-relaxed">{finding.description}</p>
              </div>

              {/* Evidence */}
              {finding.evidence && finding.evidence.length > 0 && (
                <div>
                  <div className="text-xs font-mono text-text-muted uppercase tracking-wider mb-1">Evidence</div>
                  <div className="space-y-1.5">
                    {finding.evidence.map((ev, i) => (
                      <div key={i} className="flex items-start gap-2 text-xs font-mono bg-bg-elevated border border-border-muted sharp-corners p-2">
                        <FileCode2 className="w-3.5 h-3.5 text-accent-blue mt-0.5 flex-none" />
                        <div className="min-w-0">
                          <span className="text-accent-blue break-all">{ev.file}</span>
                          {ev.line != null && (
                            <span className="text-text-muted ml-1">:{ev.line}</span>
                          )}
                          {ev.snippet && (
                            <pre className="mt-1 text-text-secondary whitespace-pre-wrap break-all">{ev.snippet}</pre>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendation */}
              <div>
                <div className="text-xs font-mono text-text-muted uppercase tracking-wider mb-1">Recommendation</div>
                <p className="text-sm font-mono text-text-primary leading-relaxed border-l-2 border-accent-blue pl-3">
                  {finding.recommendation}
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Severity group ────────────────────────────────────────────────────────────

function SeverityGroup({ severity, findings }: { severity: FindingSeverity; findings: Finding[] }) {
  const [collapsed, setCollapsed] = useState(false);
  const config = SEVERITY_CONFIG[severity];
  const SeverityIcon = config.icon;

  if (findings.length === 0) return null;

  return (
    <div className="mb-4">
      <button
        onClick={() => setCollapsed(!collapsed)}
        className={cn(
          'w-full flex items-center justify-between px-3 py-2 sharp-corners border mb-2 transition-colors',
          config.border, config.bg
        )}
      >
        <div className="flex items-center gap-2">
          <SeverityIcon className={cn('w-4 h-4', config.color)} />
          <span className={cn('font-mono text-xs font-bold uppercase tracking-widest', config.color)}>
            {config.label}
          </span>
          <span className={cn('font-mono text-xs px-1.5 py-0.5 sharp-corners border', config.border, config.color)}>
            {findings.length}
          </span>
        </div>
        {collapsed
          ? <ChevronRight className="w-3.5 h-3.5 text-text-muted" />
          : <ChevronDown className="w-3.5 h-3.5 text-text-muted" />
        }
      </button>

      <AnimatePresence>
        {!collapsed && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-2"
          >
            {findings.map((f) => (
              <FindingRow key={f.id} finding={f} />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Main panel ────────────────────────────────────────────────────────────────

export default function FindingsPanel({ ruling }: FindingsPanelProps) {
  const SEVERITIES: FindingSeverity[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

  const grouped = SEVERITIES.reduce<Record<FindingSeverity, Finding[]>>(
    (acc, sev) => {
      acc[sev] = ruling.findings.filter(f => f.severity === sev);
      return acc;
    },
    { CRITICAL: [], HIGH: [], MEDIUM: [], LOW: [] }
  );

  const totalFindings = ruling.findings.length;
  const criticalCount = grouped.CRITICAL.length;
  const highCount = grouped.HIGH.length;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="mt-6 space-y-4 pb-12"
    >
      {/* Summary card */}
      <div className="border-2 border-accent-blue bg-bg-surface sharp-corners p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="font-mono text-xs text-accent-blue font-bold uppercase tracking-widest">
            Analysis Complete
          </div>
          <div className="font-mono text-xs text-text-muted">
            {new Date(ruling.timestamp).toLocaleString()}
          </div>
        </div>

        <ScoreGauge score={ruling.overall_score} />

        <div className="mt-4 p-3 bg-bg-elevated sharp-corners border border-border-muted">
          <p className="text-sm font-mono text-text-primary leading-relaxed">{ruling.summary}</p>
        </div>

        {/* Counts */}
        <div className="mt-4 flex gap-3">
          {SEVERITIES.map((sev) => {
            const cfg = SEVERITY_CONFIG[sev];
            const count = grouped[sev].length;
            if (count === 0) return null;
            return (
              <div key={sev} className={cn('flex items-center gap-1.5 px-2 py-1 sharp-corners border', cfg.border, cfg.bg)}>
                <cfg.icon className={cn('w-3 h-3', cfg.color)} />
                <span className={cn('font-mono text-xs font-bold', cfg.color)}>{count}</span>
                <span className="font-mono text-xs text-text-muted">{cfg.label}</span>
              </div>
            );
          })}
        </div>

        {/* Priority actions */}
        {ruling.priority_actions.length > 0 && (
          <div className="mt-4">
            <div className="text-xs font-mono text-text-muted uppercase tracking-wider mb-2">Priority Actions</div>
            <ol className="space-y-1">
              {ruling.priority_actions.map((action, i) => (
                <li key={i} className="flex items-start gap-2 text-sm font-mono text-text-primary">
                  <span className="text-accent-blue font-bold w-4 flex-none">{i + 1}.</span>
                  <span>{action}</span>
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>

      {/* Findings by severity */}
      {totalFindings === 0 ? (
        <div className="text-center py-8 font-mono text-text-muted text-sm">
          No findings recorded.
        </div>
      ) : (
        SEVERITIES.map((sev) => (
          <SeverityGroup key={sev} severity={sev} findings={grouped[sev]} />
        ))
      )}
    </motion.div>
  );
}
