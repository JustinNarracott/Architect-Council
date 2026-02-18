import { ReactNode } from 'react';

interface HelpSectionProps {
  id: string;
  title: string;
  description?: string;
  children: ReactNode;
}

export default function HelpSection({ id, title, description, children }: HelpSectionProps) {
  return (
    <section id={id} className="scroll-mt-8 mb-10">
      <h2 className="font-headline text-xl text-accent-blue tracking-wide mb-1">
        <a href={`#${id}`} className="hover:underline decoration-accent-blue/30 underline-offset-4">
          {title}
        </a>
      </h2>
      {description && (
        <p className="text-text-secondary font-mono text-sm mb-4">{description}</p>
      )}
      <div className="text-text-primary text-sm leading-relaxed space-y-3">
        {children}
      </div>
    </section>
  );
}
