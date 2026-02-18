'use client';

import { Download } from 'lucide-react';
import { AgentMessage } from '@/types';

interface ExportButtonProps {
  messages: AgentMessage[];
  repoUrl?: string;
  analysisId?: string;
  /** Override the document title in the exported markdown header */
  title?: string;
}

const AGENT_SECTION_LABELS: Record<string, string> = {
  standards_analyst:    'Standards Analyst Assessment',
  dx_analyst:           'Developer Experience Assessment',
  enterprise_architect: 'Enterprise Architecture Assessment',
  security_analyst:     'Security & Resilience Assessment',
  da_chair:             'Design Authority Ruling',
};

const AGENT_ORDER = [
  'standards_analyst',
  'dx_analyst',
  'enterprise_architect',
  'security_analyst',
  'da_chair',
];

export default function ExportButton({ messages, repoUrl, analysisId, title }: ExportButtonProps) {
  // Only visible when at least one ruling exists
  const hasRuling = messages.some(m => m.message_type === 'ruling');
  if (!hasRuling) return null;

  const handleExport = () => {
    const date = new Date().toISOString();
    const fileId = analysisId ? analysisId.slice(0, 8) : Date.now().toString().slice(-8);
    const docTitle = title ?? (repoUrl ? 'Architecture Council — Codebase Review' : 'Architecture Council — ADR Review');

    const sections: string[] = [
      `# ${docTitle}`,
    ];

    if (repoUrl) {
      sections.push(`**Repository:** ${repoUrl}`);
    }
    sections.push(`**Date:** ${date}`);
    if (analysisId) {
      sections.push(`**Analysis ID:** ${analysisId}`);
    }
    sections.push('', '---', '');

    for (const agentId of AGENT_ORDER) {
      const label = AGENT_SECTION_LABELS[agentId];
      const agentMessages = messages.filter(
        m => m.agent_id === agentId && (m.message_type === 'analysis' || m.message_type === 'ruling')
      );

      if (agentMessages.length > 0) {
        sections.push(`## ${label}`);
        sections.push('');
        for (const msg of agentMessages) {
          sections.push(msg.content);
          sections.push('');
        }
        sections.push('---');
        sections.push('');
      }
    }

    const markdown = sections.join('\n');
    const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `architecture-review-${fileId}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <button
      onClick={handleExport}
      className="flex items-center gap-1.5 text-xs font-mono px-3 py-1 sharp-corners border border-accent-blue text-accent-blue hover:bg-accent-blue/10 transition-colors"
      title="Export analysis as Markdown"
    >
      <Download className="w-3.5 h-3.5" />
      EXPORT
    </button>
  );
}
