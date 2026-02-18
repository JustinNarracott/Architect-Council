'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { HELP_NAV } from '@/lib/help-nav';

export default function HelpSidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:block w-64 flex-none border-r border-border-default bg-bg-surface overflow-y-auto">
      <div className="p-4 border-b border-border-muted">
        <h2 className="font-headline text-sm text-accent-blue tracking-wide uppercase">Documentation</h2>
      </div>
      <nav className="p-3">
        {HELP_NAV.map((item) => {
          const isActive = item.href === '/help'
            ? pathname === '/help'
            : pathname.startsWith(item.href);

          return (
            <div key={item.href} className="mb-1">
              <Link
                href={item.href}
                className={cn(
                  'block px-3 py-2 font-mono text-sm sharp-corners transition-colors',
                  isActive
                    ? 'text-accent-blue bg-accent-blue/5 font-semibold'
                    : 'text-text-secondary hover:text-text-primary hover:bg-bg-hover'
                )}
              >
                {item.label}
              </Link>
              {isActive && item.sections.length > 0 && (
                <div className="ml-3 border-l border-border-muted pl-2 mt-1 mb-2">
                  {item.sections.map((section) => (
                    <a
                      key={section.id}
                      href={`#${section.id}`}
                      className="block px-2 py-1 font-mono text-xs text-text-muted hover:text-accent-blue transition-colors"
                    >
                      {section.label}
                    </a>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </nav>
    </aside>
  );
}
