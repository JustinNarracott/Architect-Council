import HelpSection from '@/components/help/HelpSection';
import HelpTable from '@/components/help/HelpTable';
import HelpCallout from '@/components/help/HelpCallout';
import HelpBreadcrumb from '@/components/help/HelpBreadcrumb';

export default function ExportHelp() {
  return (
    <>
      <HelpBreadcrumb items={[{ label: 'Export & Sharing' }]} />
      <div className="mb-8">
        <h1 className="font-headline text-2xl text-accent-blue tracking-wide mb-2">Export &amp; Sharing</h1>
        <p className="text-text-secondary text-sm">
          Download review results as Markdown for documentation, stakeholder reports, or audit trails.
        </p>
      </div>

      <HelpSection id="markdown-export" title="Markdown Export">
        <p>
          Once a review completes and the DA Chair has issued a ruling, an <strong>EXPORT</strong> button
          appears in the review header bar. Clicking it downloads a complete Markdown file
          containing all agent reports and the Chair&apos;s ruling.
        </p>
        <p>
          The file is named <code className="px-1 py-0.5 bg-bg-surface border border-border-default sharp-corners font-mono text-xs">architecture-review-{'<id>'}.md</code> where
          the ID is derived from the analysis session.
        </p>
        <HelpCallout type="tip">
          The exported Markdown renders well in GitHub, Notion, Confluence, and most documentation
          platforms. Paste it directly into a pull request description or architecture wiki page.
        </HelpCallout>
      </HelpSection>

      <HelpSection id="what-is-exported" title="What Is Exported">
        <p>The exported file includes:</p>
        <HelpTable
          headers={['Section', 'Contents']}
          rows={[
            ['Header', 'Document title, date, repository URL (if codebase review), analysis ID'],
            ['Standards Analyst Assessment', 'Full structured report with score, tech radar status, pattern compliance, anti-patterns, violations, recommendations'],
            ['Developer Experience Assessment', 'Full report with score, adoption friction, documentation quality, testing, tooling assessment'],
            ['Enterprise Architecture Assessment', 'Full report with score, coupling analysis, boundary assessment, strategic alignment, integration review'],
            ['Security & Resilience Assessment', 'Full report with score, secrets scan, vulnerability findings, auth review, error handling assessment'],
            ['Design Authority Ruling', 'Chair\'s synthesis including ruling (APPROVED / CONDITIONAL / REJECTED), agreements, disagreements, conditions, dissenting opinions, rationale, and next steps'],
          ]}
        />
        <HelpCallout type="note">
          The export captures the complete agent output — the same content shown in the
          tabbed view during the review. Nothing is summarised or truncated.
        </HelpCallout>
      </HelpSection>
    </>
  );
}
