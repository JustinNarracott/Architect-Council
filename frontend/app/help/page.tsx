import HelpSection from '@/components/help/HelpSection';
import HelpTable from '@/components/help/HelpTable';
import HelpCallout from '@/components/help/HelpCallout';
import HelpCode from '@/components/help/HelpCode';

export default function HelpPage() {
  return (
    <>
      <div className="mb-8">
        <h1 className="font-headline text-2xl text-accent-blue tracking-wide mb-2">Getting Started</h1>
        <p className="text-text-secondary text-sm">
          Everything you need to set up and run the Architecture Council.
        </p>
      </div>

      <HelpSection id="what-is-this" title="What Is This?">
        <p>
          The Architecture Council is an AI-powered Design Authority that reviews architecture
          decisions and codebases using a panel of five specialised AI agents. Each agent uses
          a different large language model, providing diverse perspectives on standards compliance,
          developer experience, enterprise architecture, security, and overall governance.
        </p>
        <p>
          Submit an Architecture Decision Record (ADR) or point it at a Git repository, and the
          council produces structured reports with scores, findings, and a synthesised ruling from
          the DA Chair.
        </p>
      </HelpSection>

      <HelpSection id="quick-start" title="Quick Start">
        <p>Get the Architecture Council running in under five minutes:</p>

        <p className="font-mono text-xs text-text-muted mt-4 mb-1">1. Clone and configure</p>
        <HelpCode language="bash">{`git clone <repo-url> Architect-Council
cd Architect-Council
cp .env.example .env
# Edit .env and add your API keys (see Requirements below)`}</HelpCode>

        <p className="font-mono text-xs text-text-muted mt-4 mb-1">2. Build and start</p>
        <HelpCode language="bash">{`docker compose -f docker/docker-compose.yml up --build -d`}</HelpCode>

        <p className="font-mono text-xs text-text-muted mt-4 mb-1">3. Open the app</p>
        <p>
          Navigate to{' '}
          <code className="px-1.5 py-0.5 bg-bg-surface border border-border-default sharp-corners font-mono text-xs">
            http://localhost:3011
          </code>{' '}
          in your browser.
        </p>

        <p className="font-mono text-xs text-text-muted mt-4 mb-1">4. Submit your first ADR</p>
        <p>
          On the ADR Review tab, enter a title like{' '}
          <em>&quot;Should we adopt Redis for session caching?&quot;</em>, fill in the technology and
          affected services, and click Submit. The five agents will stream their analysis in
          real time.
        </p>

        <HelpCallout type="tip">
          The Redis caching ADR is a great first test — it exercises all five agents well and
          produces a CONDITIONAL ruling with realistic conditions.
        </HelpCallout>
      </HelpSection>

      <HelpSection id="requirements" title="Requirements">
        <HelpCallout type="note">
          The API keys listed below correspond to the default model assignments. All agents are
          configurable — you only need the keys for the providers you actually use. See{' '}
          <a href="/help/agents#model-assignments" className="text-accent-blue hover:underline">
            The Council &rarr; Model Assignments
          </a>{' '}
          for details on changing providers.
        </HelpCallout>
        <HelpTable
          headers={['Requirement', 'Details']}
          rows={[
            ['Docker', 'Docker Desktop or Docker Engine with Compose v2'],
            ['OpenAI API key', 'Required for default config — Standards Analyst (GPT-4.1) and DA Chair (GPT-5.1)'],
            ['Anthropic API key', 'Required for default config — Enterprise Architect (Claude Sonnet 4)'],
            ['Perplexity API key', 'Required for default config — DX Analyst (Sonar Pro)'],
            ['Ollama', 'Required for default config — Security Analyst (Qwen3 Coder 30B, local). Optional if you reconfigure the Security Agent to use a cloud provider.'],
          ]}
        />
        <HelpCallout type="warning">
          If you use the default Ollama configuration, Ollama must be running with{' '}
          <code className="px-1 py-0.5 bg-bg-surface border border-border-default sharp-corners font-mono text-xs">
            qwen3-coder:30b
          </code>{' '}
          pulled before starting a review. Run{' '}
          <code className="px-1 py-0.5 bg-bg-surface border border-border-default sharp-corners font-mono text-xs">
            ollama pull qwen3-coder:30b
          </code>{' '}
          on your Ollama host. If you&apos;d rather skip Ollama entirely, reconfigure the Security
          Analyst to use a cloud provider instead.
        </HelpCallout>
      </HelpSection>

      <HelpSection id="environment-variables" title="Environment Variables">
        <p>
          Copy <code className="px-1 py-0.5 bg-bg-surface border border-border-default sharp-corners font-mono text-xs">.env.example</code> to{' '}
          <code className="px-1 py-0.5 bg-bg-surface border border-border-default sharp-corners font-mono text-xs">.env</code> and
          fill in the keys for whichever providers you use. Only keys for your configured
          model assignments are needed.
        </p>
        <HelpTable
          headers={['Variable', 'Used By (default config)', 'Default']}
          rows={[
            [
              <code key="openai" className="text-xs">OPENAI_API_KEY</code>,
              'Standards Analyst (GPT-4.1) + DA Chair (GPT-5.1)',
              '—',
            ],
            [
              <code key="anthropic" className="text-xs">ANTHROPIC_API_KEY</code>,
              'Enterprise Architect (Claude Sonnet 4)',
              '—',
            ],
            [
              <code key="perplexity" className="text-xs">PERPLEXITY_API_KEY</code>,
              'DX Analyst (Perplexity Sonar Pro)',
              '—',
            ],
            [
              <code key="ollama" className="text-xs">OLLAMA_API_BASE</code>,
              'Security Analyst — Ollama endpoint (default config only)',
              <code key="ollama-default" className="text-xs">http://localhost:11434</code>,
            ],
            [
              <code key="host" className="text-xs">HOST</code>,
              'Backend bind address',
              <code key="host-default" className="text-xs">0.0.0.0</code>,
            ],
            [
              <code key="port" className="text-xs">PORT</code>,
              'Backend port',
              <code key="port-default" className="text-xs">8000</code>,
            ],
          ]}
        />
        <HelpCallout type="note">
          The <code className="px-1 py-0.5 bg-bg-surface border border-border-default sharp-corners font-mono text-xs">GOOGLE_API_KEY</code> is
          no longer required. The Security Analyst was migrated from Gemini to a local Ollama model
          in the reference configuration.
        </HelpCallout>
      </HelpSection>
    </>
  );
}
