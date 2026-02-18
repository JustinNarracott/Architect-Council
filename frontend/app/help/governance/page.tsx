import HelpSection from '@/components/help/HelpSection';
import HelpTable from '@/components/help/HelpTable';
import HelpCallout from '@/components/help/HelpCallout';
import HelpCode from '@/components/help/HelpCode';
import HelpBreadcrumb from '@/components/help/HelpBreadcrumb';

export default function GovernanceHelp() {
  return (
    <>
      <HelpBreadcrumb items={[{ label: 'Governance Config' }]} />
      <div className="mb-8">
        <h1 className="font-headline text-2xl text-accent-blue tracking-wide mb-2">Governance Configuration</h1>
        <p className="text-text-secondary text-sm">
          Define your organisation&apos;s standards so agents evaluate against your rules, not generic best practices.
        </p>
      </div>

      <HelpSection id="overview" title="Overview">
        <p>
          The Governance Config tab lets you define four YAML configuration files. These rules are
          injected into every codebase review — agents read your specific standards and evaluate
          the repository against them.
        </p>
        <p>
          If all files are left empty, agents fall back to generic industry best practices. Once
          you configure even one file, agents will reference your rules in their reports.
        </p>
        <HelpTable
          headers={['File', 'Purpose']}
          rows={[
            ['Technology Radar', 'Classify technologies by adoption status (adopt, trial, assess, hold)'],
            ['Coding Standards', 'Naming conventions, required patterns, quality thresholds'],
            ['Architecture', 'Approved styles, constraints, API standards, data layer rules'],
            ['Security', 'Secrets policy, authentication, dependency scanning, input validation'],
          ]}
        />
      </HelpSection>

      <HelpSection id="tech-radar" title="Technology Radar">
        <p>
          Classify technologies into four tiers. The Standards Analyst uses this to flag
          dependencies that are on hold or not yet assessed.
        </p>
        <HelpCode language="yaml">{`adopt:
  description: "Approved for production use. Preferred choices."
  technologies:
    - PostgreSQL
    - Redis
    - Python 3.11+
    - TypeScript
    - React

trial:
  description: "Approved for non-critical use. Evaluate actively."
  technologies:
    - Kafka
    - GraphQL

assess:
  description: "Under evaluation. Not approved for production."
  technologies:
    - Deno
    - Bun

hold:
  description: "Do not use. Migrate away where possible."
  technologies:
    - jQuery
    - CoffeeScript`}</HelpCode>
      </HelpSection>

      <HelpSection id="coding-standards" title="Coding Standards">
        <p>
          Define naming conventions, required patterns, and quality thresholds. The Standards
          Analyst and DX Analyst both reference these.
        </p>
        <HelpCode language="yaml">{`naming:
  files: kebab-case
  classes: PascalCase
  functions: camelCase
  constants: UPPER_SNAKE_CASE

required_patterns:
  - Error boundaries in React components
  - Type annotations on all public functions
  - Unit tests for business logic

prohibited_patterns:
  - console.log in production code
  - any type in TypeScript
  - Hardcoded URLs or ports`}</HelpCode>
      </HelpSection>

      <HelpSection id="architecture" title="Architecture">
        <p>
          Define approved architecture styles, API conventions, and data layer rules. The
          Enterprise Architect uses these to assess structural decisions.
        </p>
        <HelpCode language="yaml">{`styles:
  approved:
    - Microservices
    - Event-driven
    - Modular monolith
  hold:
    - Monolithic (legacy)

api_standards:
  versioning: URI-based (e.g. /v1/resource)
  naming: Plural nouns, RESTful
  pagination: Cursor-based preferred

data_layer:
  orm_required: true
  raw_sql: Discouraged except for migrations`}</HelpCode>
      </HelpSection>

      <HelpSection id="security" title="Security">
        <p>
          Define secrets handling, authentication requirements, and compliance rules. The
          Security Analyst evaluates the codebase against these policies.
        </p>
        <HelpCode language="yaml">{`secrets:
  scanning: required
  allowed_storage:
    - Environment variables
    - Secret manager (AWS SSM, Vault, etc.)
  never_in_code:
    - API keys
    - Database credentials
    - JWT signing keys

authentication:
  required: true
  approved_methods:
    - OAuth 2.0 / OIDC
    - API key with rotation policy

dependencies:
  scanning: required
  max_critical_vulnerabilities: 0
  max_high_vulnerabilities: 3`}</HelpCode>
      </HelpSection>

      <HelpSection id="yaml-format" title="YAML Format Tips">
        <p>
          Governance files use standard YAML. A few tips to avoid common issues:
        </p>
        <ul className="list-disc list-inside space-y-1 text-text-secondary ml-2">
          <li>Use consistent indentation (2 spaces recommended).</li>
          <li>Strings with special characters should be quoted.</li>
          <li>Lists start with a dash and a space (<code className="px-1 py-0.5 bg-bg-surface border border-border-default sharp-corners font-mono text-xs">- item</code>).</li>
          <li>Comments start with <code className="px-1 py-0.5 bg-bg-surface border border-border-default sharp-corners font-mono text-xs">#</code> and are ignored by the parser.</li>
          <li>The editor validates YAML on save — invalid syntax will show an error message.</li>
        </ul>
        <HelpCallout type="tip">
          Start with the default examples provided in the governance directory, then customise
          them to match your organisation. You don&apos;t need to fill in all four files — configure
          only the areas you care about.
        </HelpCallout>
      </HelpSection>
    </>
  );
}
