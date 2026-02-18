import { ReactNode } from 'react';

interface HelpCodeProps {
  children: ReactNode;
  language?: string;
}

export default function HelpCode({ children, language }: HelpCodeProps) {
  return (
    <div className="my-4 sharp-corners overflow-hidden border border-border-default">
      {language && (
        <div className="bg-bg-surface px-4 py-1.5 border-b border-border-default">
          <span className="font-mono text-xs text-text-muted uppercase">{language}</span>
        </div>
      )}
      <pre className="bg-bg-elevated p-4 overflow-x-auto">
        <code className="font-mono text-sm text-text-primary leading-relaxed">{children}</code>
      </pre>
    </div>
  );
}
