import { BookCheck, Users, Network, ShieldCheck, Scale, type LucideIcon } from 'lucide-react';

export interface AgentConfig {
  id: string;
  name: string;
  Icon: LucideIcon;
  llm: string;           // Display label for the model
  color: string;         // Tailwind text colour class
  accentColor: string;
  borderColor: string;
  bgColor: string;
  headingColor: string;
  subtitle: string;
}

export const AGENTS: AgentConfig[] = [
  {
    id: 'standards_analyst',
    name: 'Standards Analyst',
    Icon: BookCheck,
    llm: 'GPT-4.1',
    color: 'text-accent-blue',
    accentColor: 'text-accent-blue',
    borderColor: 'border-accent-blue',
    bgColor: 'bg-accent-blue/10',
    headingColor: 'prose-headings:text-accent-blue',
    subtitle: 'Tech radar, patterns, naming, dependencies',
  },
  {
    id: 'dx_analyst',
    name: 'DX Analyst',
    Icon: Users,
    llm: 'Perplexity',
    color: 'text-accent-purple',
    accentColor: 'text-accent-purple',
    borderColor: 'border-accent-purple',
    bgColor: 'bg-accent-purple/10',
    headingColor: 'prose-headings:text-accent-purple',
    subtitle: 'Documentation, testing, onboarding, developer tooling',
  },
  {
    id: 'enterprise_architect',
    name: 'Enterprise Architect',
    Icon: Network,
    llm: 'Claude Sonnet 4',
    color: 'text-accent-blue',
    accentColor: 'text-accent-green',
    borderColor: 'border-accent-green',
    bgColor: 'bg-accent-green/10',
    headingColor: 'prose-headings:text-accent-green',
    subtitle: 'Coupling, boundaries, API surface, integration',
  },
  {
    id: 'security_analyst',
    name: 'Security & Resilience',
    Icon: ShieldCheck,
    llm: 'Qwen3 Coder 30B (Local)',
    color: 'text-accent-amber',
    accentColor: 'text-accent-amber',
    borderColor: 'border-accent-amber',
    bgColor: 'bg-accent-amber/10',
    headingColor: 'prose-headings:text-accent-amber',
    subtitle: 'Secrets, vulnerabilities, auth, error handling',
  },
  {
    id: 'da_chair',
    name: 'DA Chair',
    Icon: Scale,
    llm: 'GPT-5.1',
    color: 'text-accent-green',
    accentColor: 'text-accent-blue',
    borderColor: 'border-accent-blue',
    bgColor: 'bg-accent-blue/10',
    headingColor: 'prose-headings:text-accent-blue',
    subtitle: 'Synthesis, ruling, prioritised roadmap',
  },
];

// Helper to look up an agent by ID
export const getAgent = (id: string): AgentConfig | undefined =>
  AGENTS.find(a => a.id === id);

// Map for quick access
export const AGENT_MAP: Record<string, AgentConfig> = Object.fromEntries(
  AGENTS.map(a => [a.id, a])
);
