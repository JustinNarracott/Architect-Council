import HelpSection from '@/components/help/HelpSection';
import HelpTable from '@/components/help/HelpTable';
import HelpCallout from '@/components/help/HelpCallout';
import HelpCode from '@/components/help/HelpCode';
import HelpBreadcrumb from '@/components/help/HelpBreadcrumb';

export default function AgentsHelp() {
  return (
    <>
      <HelpBreadcrumb items={[{ label: 'The Council' }]} />
      <div className="mb-8">
        <h1 className="font-headline text-2xl text-accent-blue tracking-wide mb-2">The Council</h1>
        <p className="text-text-secondary text-sm">
          Five AI agents, each powered by a different language model, providing diverse expert perspectives.
        </p>
      </div>

      <HelpSection id="agent-roles" title="Agent Roles">
        <p>
          Each agent has a specific domain of expertise. They work in parallel during a review,
          and their individual reports are synthesised by the DA Chair into a final ruling.
        </p>
        <HelpTable
          headers={['Agent', 'Focus Area', 'What They Assess']}
          rows={[
            [
              'Standards Analyst',
              'Compliance & Patterns',
              'Technology radar alignment, design pattern usage, API naming conventions, anti-pattern detection, dependency management',
            ],
            [
              'DX Analyst',
              'Developer Experience',
              'Documentation quality, testing coverage, onboarding friction, CI/CD setup, developer tooling, adoption barriers',
            ],
            [
              'Enterprise Architect',
              'Strategic Architecture',
              'Service coupling, bounded contexts, API surface area, data layer design, integration patterns, scalability, strategic alignment',
            ],
            [
              'Security & Resilience',
              'Security & Ops',
              'Hardcoded secrets, dependency vulnerabilities, authentication mechanisms, input validation, error handling, resilience patterns',
            ],
            [
              'DA Chair',
              'Synthesis & Ruling',
              'Reads all four agent reports, identifies agreements and disagreements, produces a final ruling (APPROVED / CONDITIONAL / REJECTED) with conditions and next steps',
            ],
          ]}
        />
      </HelpSection>

      <HelpSection id="model-assignments" title="Model Assignments">
        <HelpCallout type="note">
          The model assignments below are the default reference configuration. Every agent can
          be configured to use any compatible LLM — cloud or local — by updating the environment
          variables and agent config files. You don&apos;t need these specific models or providers
          to run the Architecture Council.
        </HelpCallout>
        <p>
          The default configuration pairs each agent with a model chosen for its strengths in
          that domain. Using multiple providers also reduces single-vendor dependency.
        </p>
        <HelpTable
          headers={['Agent', 'Default Model', 'Default Provider', 'Type']}
          rows={[
            ['Standards Analyst', 'GPT-4.1', 'OpenAI', 'Cloud API'],
            ['DX Analyst', 'Sonar Pro', 'Perplexity', 'Cloud API'],
            ['Enterprise Architect', 'Claude Sonnet 4', 'Anthropic', 'Cloud API'],
            ['Security & Resilience', 'Qwen3 Coder 30B', 'Ollama (Local)', 'On-premises'],
            ['DA Chair', 'GPT-5.1', 'OpenAI', 'Cloud API'],
          ]}
        />
        <p>
          See <strong>Changing Models</strong> below for instructions on swapping any agent to
          a different model or provider.
        </p>
      </HelpSection>

      <HelpSection id="ollama-setup" title="Ollama Setup">
        <HelpCallout type="note">
          Ollama is only required if you&apos;re using the default Security Analyst configuration
          (Qwen3 Coder 30B). If you prefer, you can point the Security Analyst at any cloud
          provider instead — edit <code className="px-1 py-0.5 bg-bg-surface border border-border-default sharp-corners font-mono text-xs">backend/agents/security_analyst.py</code> and
          replace the Ollama LLM config with your preferred provider.
        </HelpCallout>
        <p>
          To use the default local model, run Ollama with Qwen3 Coder 30B. This can be on
          the same machine or a separate GPU server on your network.
        </p>

        <p className="font-mono text-xs text-text-muted mt-4 mb-1">1. Install Ollama</p>
        <p>
          Download from{' '}
          <code className="px-1 py-0.5 bg-bg-surface border border-border-default sharp-corners font-mono text-xs">
            https://ollama.com
          </code>{' '}
          and install for your platform.
        </p>

        <p className="font-mono text-xs text-text-muted mt-4 mb-1">2. Pull the model</p>
        <HelpCode language="bash">{`ollama pull qwen3-coder:30b`}</HelpCode>

        <p className="font-mono text-xs text-text-muted mt-4 mb-1">3. Verify it&apos;s running</p>
        <HelpCode language="bash">{`curl http://localhost:11434/api/tags`}</HelpCode>

        <p className="font-mono text-xs text-text-muted mt-4 mb-1">4. Configure the address</p>
        <p>
          If Ollama runs on a different machine, set <code className="px-1 py-0.5 bg-bg-surface border border-border-default sharp-corners font-mono text-xs">OLLAMA_API_BASE</code> in
          your <code className="px-1 py-0.5 bg-bg-surface border border-border-default sharp-corners font-mono text-xs">.env</code> file:
        </p>
        <HelpCode language="bash">{`OLLAMA_API_BASE=http://localhost:11434`}</HelpCode>

        <HelpCallout type="important">
          Qwen3 Coder 30B is a 30.5 billion parameter MoE model (Q4_K_M quantisation). It
          requires approximately 20 GB of VRAM. A GPU with at least 24 GB VRAM is recommended
          (e.g. RTX 3090, RTX 4090, A5000).
        </HelpCallout>
      </HelpSection>

      <HelpSection id="changing-models" title="Changing Models">
        <p>
          Model assignments are configured in the backend agent files. To change an agent&apos;s
          model, edit the corresponding file in <code className="px-1 py-0.5 bg-bg-surface border border-border-default sharp-corners font-mono text-xs">backend/agents/</code> and
          update the <code className="px-1 py-0.5 bg-bg-surface border border-border-default sharp-corners font-mono text-xs">LLM()</code> configuration.
        </p>
        <HelpTable
          headers={['Agent', 'Config File']}
          rows={[
            ['Standards Analyst', 'backend/agents/standards_analyst.py'],
            ['DX Analyst', 'backend/agents/dx_analyst.py'],
            ['Enterprise Architect', 'backend/agents/enterprise_architect.py'],
            ['Security & Resilience', 'backend/agents/security_analyst.py'],
            ['DA Chair', 'backend/agents/da_chair.py'],
          ]}
        />
        <p>
          After changing a model, also update the display label
          in <code className="px-1 py-0.5 bg-bg-surface border border-border-default sharp-corners font-mono text-xs">frontend/lib/agents.ts</code> so
          the UI reflects the correct model name, then rebuild the Docker containers.
        </p>
      </HelpSection>
    </>
  );
}
