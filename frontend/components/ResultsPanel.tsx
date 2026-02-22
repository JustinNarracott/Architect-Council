import { ArchitectureRuling, RulingOutcome } from "@/types";
import { cn } from "@/lib/utils";
import { AlertTriangle, CheckCircle2 } from "lucide-react";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface ResultsPanelProps {
  report: ArchitectureRuling;
}

const getRulingStyle = (ruling: RulingOutcome) => {
  switch (ruling) {
    case "approved":
      return { color: "text-accent-green", label: "APPROVED", border: "border-accent-green", bg: "bg-accent-green/10" };
    case "conditional":
      return { color: "text-accent-amber", label: "CONDITIONAL", border: "border-accent-amber", bg: "bg-accent-amber/10" };
    case "rejected":
      return { color: "text-accent-red", label: "REJECTED", border: "border-accent-red", bg: "bg-accent-red/10" };
    case "deferred":
    default:
      return { color: "text-accent-grey", label: "DEFERRED", border: "border-accent-grey", bg: "bg-accent-grey/10" };
  }
};

export default function ResultsPanel({ report }: ResultsPanelProps) {
  const [expandedScore, setExpandedScore] = useState<string | null>(null);

  if (!report) return null;

  const rulingStyle = getRulingStyle(report.ruling);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="mt-8 space-y-6 pb-12"
    >
      {/* Architecture Ruling Card */}
      <div className={cn("bg-bg-surface border-2 p-6 sharp-corners relative", rulingStyle.border)}>
        <div className="flex flex-col md:flex-row gap-8 mb-6">
          {/* Ruling Badge */}
          <div className={cn(
            "flex-none flex flex-col items-center justify-center p-6 border-2 sharp-corners min-w-[180px]",
            rulingStyle.border,
            rulingStyle.bg
          )}>
            <span className={cn("text-3xl font-mono font-bold tracking-wide leading-none mb-2", rulingStyle.color)}>
              {rulingStyle.label}
            </span>
            <div className="w-full h-[1px] bg-current opacity-30 my-2" />
            <span className="text-xs font-mono text-text-muted uppercase tracking-wider">
              Architecture Ruling
            </span>
          </div>

          {/* Metrics */}
          <div className="flex-1 grid grid-cols-2 gap-4">
            <div className="p-4 border border-border-default sharp-corners bg-bg-elevated">
              <div className="text-xs font-mono text-text-secondary uppercase tracking-wider mb-1">Confidence</div>
              <div className="text-2xl font-mono font-semibold text-accent-blue">{report.confidence.toUpperCase()}</div>
            </div>
            <div className="p-4 border border-border-default sharp-corners bg-bg-elevated">
              <div className="text-xs font-mono text-text-secondary uppercase tracking-wider mb-1">Technology</div>
              <div className="text-2xl font-mono font-semibold text-accent-blue">{report.technology}</div>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-accent-blue font-mono text-lg font-semibold mb-3">Rationale</h3>
          <p className="text-base leading-relaxed font-mono text-text-primary border-l-2 border-accent-blue pl-4">
            {report.rationale}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Panel Assessments */}
        <div className="bg-bg-surface border border-border-default p-6 sharp-corners">
          <h3 className="text-lg font-mono font-semibold text-accent-blue mb-6 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5" />
            PANEL ASSESSMENTS
          </h3>
          <div className="space-y-3">
            {report.agent_scores.map((agent) => (
              <div
                key={agent.agent_name}
                className="group border border-border-default bg-bg-elevated sharp-corners overflow-hidden hover:border-accent-blue transition-colors cursor-pointer"
                onClick={() => setExpandedScore(expandedScore === agent.agent_name ? null : agent.agent_name)}
              >
                <div className="p-3 flex items-center justify-between">
                  <span className="font-mono text-sm text-text-primary group-hover:text-accent-blue transition-colors">{agent.agent_name}</span>
                  <div className="flex items-center gap-4">
                    <div className="w-32 h-1.5 bg-bg-primary">
                      <div
                        className="h-full bg-accent-blue transition-all duration-1000 ease-out"
                        style={{ width: `${agent.score}%` }}
                      />
                    </div>
                    <span className="font-mono font-bold w-8 text-right text-accent-purple">{agent.score}</span>
                  </div>
                </div>
                <AnimatePresence>
                  {expandedScore === agent.agent_name && (
                    <motion.div
                      initial={{ height: 0 }}
                      animate={{ height: "auto" }}
                      exit={{ height: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="p-3 pt-0 text-sm font-mono text-text-secondary border-t border-border-muted bg-bg-primary">
                        <div className="pt-2 text-text-muted">Rationale:</div>
                        {agent.rationale}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        </div>

        {/* Agreements, Disagreements & Conditions */}
        <div className="bg-bg-surface border border-border-default p-6 sharp-corners">
          <h3 className="text-lg font-mono font-semibold text-accent-amber mb-6 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            KEY FINDINGS
          </h3>

          <div className="space-y-6">
            {report.key_agreements.length > 0 && (
              <div>
                <h4 className="text-xs font-mono font-bold text-accent-green uppercase tracking-wider mb-3 border-b border-border-muted pb-2">Agreements</h4>
                <ul className="space-y-2">
                  {report.key_agreements.map((item, i) => (
                    <li key={i} className="text-sm font-mono text-text-primary flex items-start gap-3">
                      <span className="text-accent-green mt-0.5 text-xs">●</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {report.key_disagreements.length > 0 && (
              <div>
                <h4 className="text-xs font-mono font-bold text-accent-red uppercase tracking-wider mb-3 border-b border-border-muted pb-2">Disagreements</h4>
                <ul className="space-y-2">
                  {report.key_disagreements.map((item, i) => (
                    <li key={i} className="text-sm font-mono text-text-primary flex items-start gap-3">
                      <span className="text-accent-red mt-0.5 text-xs">▲</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {report.conditions && report.conditions.length > 0 && (
              <div>
                <h4 className="text-xs font-mono font-bold text-accent-amber uppercase tracking-wider mb-3 border-b border-border-muted pb-2">Conditions</h4>
                <ul className="space-y-2">
                  {report.conditions.map((item, i) => (
                    <li key={i} className="text-sm font-mono text-text-primary flex items-start gap-3">
                      <span className="text-accent-amber mt-0.5 text-xs">◆</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {report.dissenting_opinions && report.dissenting_opinions.length > 0 && (
              <div>
                <h4 className="text-xs font-mono font-bold text-accent-purple uppercase tracking-wider mb-3 border-b border-border-muted pb-2">Dissenting Opinions</h4>
                <ul className="space-y-2">
                  {report.dissenting_opinions.map((item, i) => (
                    <li key={i} className="text-sm font-mono text-text-primary flex items-start gap-3">
                      <span className="text-accent-purple mt-0.5 text-xs">◈</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
