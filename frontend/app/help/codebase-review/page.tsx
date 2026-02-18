import HelpSection from '@/components/help/HelpSection';
import HelpTable from '@/components/help/HelpTable';
import HelpCallout from '@/components/help/HelpCallout';
import HelpBreadcrumb from '@/components/help/HelpBreadcrumb';

export default function CodebaseReviewHelp() {
  return (
    <>
      <HelpBreadcrumb items={[{ label: 'Codebase Review' }]} />
      <div className="mb-8">
        <h1 className="font-headline text-2xl text-accent-blue tracking-wide mb-2">Codebase Review</h1>
        <p className="text-text-secondary text-sm">
          Point the council at a Git repository for a full architecture and security review.
        </p>
      </div>

      <HelpSection id="local-repos" title="Local Repositories">
        <p>
          Local repositories are folders mounted into the Docker container via the volume
          mapping in <code className="px-1 py-0.5 bg-bg-surface border border-border-default sharp-corners font-mono text-xs">docker-compose.yml</code>.
          By default, the compose file mounts a parent directory as read-only
          at <code className="px-1 py-0.5 bg-bg-surface border border-border-default sharp-corners font-mono text-xs">/repos</code>.
        </p>
        <p>
          On the <strong>Codebase Review</strong> tab, select <strong>Local Path</strong> mode. The
          dropdown will list all Git repositories found in the mounted directory. Select one and
          submit.
        </p>
        <HelpCallout type="tip">
          Local repos are available instantly — no cloning required. This is the fastest way to
          review your own projects.
        </HelpCallout>
      </HelpSection>

      <HelpSection id="remote-repos" title="Remote Repositories">
        <p>
          Remote repositories are cloned from GitHub, GitLab, or Bitbucket. Enter the full
          HTTPS URL (e.g. <code className="px-1 py-0.5 bg-bg-surface border border-border-default sharp-corners font-mono text-xs">https://github.com/org/repo</code>).
        </p>
        <HelpTable
          headers={['Field', 'Required', 'Description']}
          rows={[
            ['Repository URL', 'Yes', 'Full HTTPS URL to the Git repository.'],
            ['Auth Token', 'No', 'Personal access token for private repositories. Never stored — used only for the clone operation.'],
            ['Branch', 'No', 'Branch to review. Defaults to the repository\'s default branch if not specified.'],
          ]}
        />
        <HelpCallout type="note">
          Remote repos are cloned into a temporary directory inside the container. The clone is
          shallow (depth 1) to minimise download time.
        </HelpCallout>
      </HelpSection>

      <HelpSection id="what-agents-check" title="What Agents Check">
        <p>
          A codebase review runs all five agents against the actual source code. Each agent reads
          the repository&apos;s file structure, key files, and indexed content to produce their report.
        </p>
        <HelpTable
          headers={['Agent', 'Checks']}
          rows={[
            ['Standards Analyst', 'Naming conventions, design patterns, dependency management, API structure, anti-patterns'],
            ['DX Analyst', 'README quality, test coverage, CI/CD setup, onboarding friction, developer tooling'],
            ['Enterprise Architect', 'Service boundaries, coupling, API surface area, data layer design, scalability'],
            ['Security & Resilience', 'Hardcoded secrets, dependency vulnerabilities, authentication, input validation, error handling'],
            ['DA Chair', 'Synthesis across all agents with prioritised recommendations'],
          ]}
        />
      </HelpSection>

      <HelpSection id="governance-rules" title="Governance Rules">
        <p>
          If you have configured governance rules on the <strong>Governance Config</strong> tab,
          they are automatically injected into every codebase review. Agents evaluate the
          repository against your specific organisational standards rather than generic best
          practices.
        </p>
        <p>
          For example, if your tech radar lists React as ADOPT and Angular as HOLD, the Standards
          Analyst will flag an Angular dependency accordingly.
        </p>
        <HelpCallout type="note">
          Governance rules only apply to Codebase Reviews, not ADR Reviews. ADR Reviews use the
          information provided in the submission form.
        </HelpCallout>
      </HelpSection>
    </>
  );
}
