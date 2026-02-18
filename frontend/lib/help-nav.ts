export interface HelpNavSection {
  id: string;
  label: string;
}

export interface HelpNavItem {
  label: string;
  href: string;
  sections: HelpNavSection[];
}

export const HELP_NAV: HelpNavItem[] = [
  {
    label: 'Getting Started',
    href: '/help',
    sections: [
      { id: 'what-is-this', label: 'What Is This?' },
      { id: 'quick-start', label: 'Quick Start' },
      { id: 'requirements', label: 'Requirements' },
      { id: 'environment-variables', label: 'Environment Variables' },
    ],
  },
  {
    label: 'ADR Review',
    href: '/help/adr-review',
    sections: [
      { id: 'submitting', label: 'Submitting an ADR' },
      { id: 'form-fields', label: 'Form Fields' },
      { id: 'review-process', label: 'Review Process' },
      { id: 'understanding-output', label: 'Understanding Output' },
      { id: 'rulings', label: 'Rulings Explained' },
    ],
  },
  {
    label: 'Codebase Review',
    href: '/help/codebase-review',
    sections: [
      { id: 'local-repos', label: 'Local Repositories' },
      { id: 'remote-repos', label: 'Remote Repositories' },
      { id: 'what-agents-check', label: 'What Agents Check' },
      { id: 'governance-rules', label: 'Governance Rules' },
    ],
  },
  {
    label: 'RAG Chat',
    href: '/help/rag-chat',
    sections: [
      { id: 'what-is-rag', label: 'What Is RAG Chat?' },
      { id: 'asking-questions', label: 'Asking Questions' },
      { id: 'how-indexing-works', label: 'How Indexing Works' },
    ],
  },
  {
    label: 'Governance Config',
    href: '/help/governance',
    sections: [
      { id: 'overview', label: 'Overview' },
      { id: 'tech-radar', label: 'Technology Radar' },
      { id: 'coding-standards', label: 'Coding Standards' },
      { id: 'architecture', label: 'Architecture' },
      { id: 'security', label: 'Security' },
      { id: 'yaml-format', label: 'YAML Format Tips' },
    ],
  },
  {
    label: 'The Council',
    href: '/help/agents',
    sections: [
      { id: 'agent-roles', label: 'Agent Roles' },
      { id: 'model-assignments', label: 'Model Assignments' },
      { id: 'ollama-setup', label: 'Ollama Setup' },
      { id: 'changing-models', label: 'Changing Models' },
    ],
  },
  {
    label: 'Export & Sharing',
    href: '/help/export',
    sections: [
      { id: 'markdown-export', label: 'Markdown Export' },
      { id: 'what-is-exported', label: 'What Is Exported' },
    ],
  },
];
