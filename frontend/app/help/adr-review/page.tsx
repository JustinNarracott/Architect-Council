import HelpSection from '@/components/help/HelpSection';
import HelpTable from '@/components/help/HelpTable';
import HelpCallout from '@/components/help/HelpCallout';
import HelpBreadcrumb from '@/components/help/HelpBreadcrumb';

export default function ADRReviewHelp() {
  return (
    <>
      <HelpBreadcrumb items={[{ label: 'ADR Review' }]} />
      <div className="mb-8">
        <h1 className="font-headline text-2xl text-accent-blue tracking-wide mb-2">ADR Review</h1>
        <p className="text-text-secondary text-sm">
          How to submit Architecture Decision Records and interpret the council&apos;s ruling.
        </p>
      </div>

      <HelpSection id="submitting" title="Submitting an ADR">
        <p>
          An ADR review evaluates a proposed technology or architecture decision against your
          organisation&apos;s standards. To submit one, navigate to the <strong>ADR Review</strong> tab
          and fill in the submission form.
        </p>
        <p>
          Only the <strong>Decision Title</strong> and <strong>Technology</strong> fields are required.
          The more context you provide, the more specific and useful the agents&apos; analysis will be.
        </p>
        <HelpCallout type="tip">
          Write the title as a question: &quot;Should we adopt Redis for session caching?&quot; rather
          than just &quot;Redis&quot;. This gives the agents clearer context for their analysis.
        </HelpCallout>
      </HelpSection>

      <HelpSection id="form-fields" title="Form Fields">
        <HelpTable
          headers={['Field', 'Required', 'Description']}
          rows={[
            ['Decision Title', 'Yes', 'The architecture decision being proposed. Phrase as a question or statement of intent.'],
            ['Technology', 'Yes', 'The specific technology or tool being evaluated (e.g. "Redis 7.x", "Kafka", "GraphQL").'],
            ['Data Classification', 'No', 'The sensitivity level of data handled by this decision. Options: PUBLIC, OFFICIAL (default), OFFICIAL-SENSITIVE, SECRET. Affects the Security Analyst\'s assessment.'],
            ['Affected Services', 'No', 'Comma-separated list of services impacted (e.g. "customer-api, order-service"). Helps the Enterprise Architect assess coupling and boundaries.'],
            ['Proposer', 'No', 'The team or individual proposing the change. Included in the exported report.'],
            ['Reason', 'No', 'Business or technical justification (e.g. "Reduce p95 latency by 40%"). Gives all agents context for evaluating the decision.'],
          ]}
        />
      </HelpSection>

      <HelpSection id="review-process" title="Review Process">
        <p>
          After submission, the five agents analyse the decision in parallel. Each agent streams
          its findings in real time — you can watch them appear in the conversation stream as
          they work.
        </p>
        <p>A typical review takes 60–120 seconds depending on model response times. The sequence is:</p>
        <HelpTable
          headers={['Order', 'Agent', 'Default Model', 'Focus']}
          rows={[
            ['1', 'Standards Analyst', 'GPT-4.1', 'Tech radar, design patterns, API standards, anti-patterns'],
            ['2', 'DX Analyst', 'Perplexity Sonar Pro', 'Documentation, testing, onboarding friction, developer tooling'],
            ['3', 'Enterprise Architect', 'Claude Sonnet 4', 'Coupling, service boundaries, integration, strategic alignment'],
            ['4', 'Security & Resilience', 'Qwen3 Coder 30B (Local)', 'Secrets, vulnerabilities, auth, error handling, compliance'],
            ['5', 'DA Chair', 'GPT-5.1', 'Synthesis of all reports into a final ruling'],
          ]}
        />
        <p>
          The sidebar <strong>Review Panel</strong> shows each agent&apos;s status — pending, analysing,
          or complete — along with their score and rating once finished.
        </p>
      </HelpSection>

      <HelpSection id="understanding-output" title="Understanding the Output">
        <p>
          Each agent produces a structured report with a numerical score (0–100) and a traffic-light
          rating:
        </p>
        <HelpTable
          headers={['Rating', 'Score Range', 'Meaning']}
          rows={[
            ['🟢 GREEN', '80–100', 'Compliant, no significant concerns'],
            ['🟡 AMBER', '60–79', 'Conditionally acceptable, issues to address'],
            ['🔴 RED', '0–59', 'Non-compliant, significant blockers identified'],
          ]}
        />
        <p>
          Each report includes specific findings, evidence, and recommendations. Click the agent
          tabs above the conversation stream to view individual reports in full.
        </p>
      </HelpSection>

      <HelpSection id="rulings" title="Rulings Explained">
        <p>
          The DA Chair synthesises all five agent reports into a single ruling. There are three
          possible outcomes:
        </p>
        <HelpTable
          headers={['Ruling', 'Meaning']}
          rows={[
            ['APPROVED', 'The decision is endorsed. Proceed with implementation.'],
            ['CONDITIONAL', 'The decision is viable but has conditions that must be met before or during implementation. Conditions are listed with owners and deadlines.'],
            ['REJECTED', 'The decision is not endorsed. Significant blockers were identified across multiple agents.'],
          ]}
        />
        <p>
          The Chair&apos;s ruling also includes key agreements (where agents aligned), key
          disagreements (where agents differed, with resolution), dissenting opinions, and
          a prioritised list of next steps.
        </p>
        <HelpCallout type="note">
          A CONDITIONAL ruling is the most common outcome for well-formed proposals. It means
          the decision is sound but needs guardrails — which is exactly what a Design Authority
          should produce.
        </HelpCallout>
      </HelpSection>
    </>
  );
}
