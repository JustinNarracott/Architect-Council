'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { FileCode2, GitBranch, Settings2, HelpCircle, type LucideIcon } from 'lucide-react';

interface Tab {
  label: string;
  href: string;
  icon: LucideIcon;
  description: string;
  pushRight?: boolean;
}

const TABS: Tab[] = [
  {
    label: 'ADR Review',
    href: '/',
    icon: FileCode2,
    description: 'Architecture Decision Records',
  },
  {
    label: 'Codebase Review',
    href: '/codebase',
    icon: GitBranch,
    description: 'Live Repository Analysis',
  },
  {
    label: 'Governance Config',
    href: '/governance',
    icon: Settings2,
    description: 'Organisation Standards & Policies',
  },
  {
    label: 'Help',
    href: '/help',
    icon: HelpCircle,
    description: 'Documentation & Guides',
    pushRight: true,
  },
];

export default function TabNav() {
  const pathname = usePathname();

  return (
    <nav className="flex items-end gap-0 border-b border-border-default bg-[#161B22]">
      {TABS.map((tab) => {
        const pushRight = tab.pushRight;
        const isActive = tab.href === '/'
          ? pathname === '/'
          : pathname.startsWith(tab.href);
        const Icon = tab.icon;

        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={cn(
              pushRight && 'ml-auto',
              'group flex items-center gap-2 px-6 py-3 font-mono text-sm tracking-wide transition-all duration-200 border-b-2 -mb-px',
              isActive
                ? 'text-[#58A6FF] border-[#58A6FF] bg-bg-surface'
                : 'text-[#8B949E] border-transparent hover:text-[#58A6FF] hover:border-[#58A6FF]/50 hover:bg-bg-surface/50'
            )}
          >
            <Icon className={cn(
              'w-4 h-4 transition-colors',
              isActive ? 'text-[#58A6FF]' : 'text-[#8B949E] group-hover:text-[#58A6FF]'
            )} />
            <span>{tab.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
