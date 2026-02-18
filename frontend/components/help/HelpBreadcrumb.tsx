import Link from 'next/link';
import { ChevronRight } from 'lucide-react';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface HelpBreadcrumbProps {
  items: BreadcrumbItem[];
}

export default function HelpBreadcrumb({ items }: HelpBreadcrumbProps) {
  return (
    <nav className="flex items-center gap-1.5 font-mono text-xs text-text-muted mb-6">
      <Link href="/help" className="hover:text-accent-blue transition-colors">
        Help
      </Link>
      {items.map((item, i) => (
        <span key={i} className="flex items-center gap-1.5">
          <ChevronRight className="w-3 h-3" />
          {item.href ? (
            <Link href={item.href} className="hover:text-accent-blue transition-colors">
              {item.label}
            </Link>
          ) : (
            <span className="text-text-secondary">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
