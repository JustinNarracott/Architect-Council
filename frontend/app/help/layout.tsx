import type { Metadata } from 'next';
import { Code2 } from 'lucide-react';
import TabNav from '@/components/TabNav';
import HelpSidebar from '@/components/help/HelpSidebar';

export const metadata: Metadata = {
  title: 'Help — The Architecture Council',
  description: 'Documentation and guides for the Architecture Council',
};

export default function HelpLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex h-screen w-full flex-col overflow-hidden bg-background relative selection:bg-accent-blue selection:text-white">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-border-default bg-bg-surface z-10">
        <div className="flex items-center gap-4">
          <div className="p-2 border border-accent-blue bg-bg-elevated sharp-corners">
            <Code2 className="w-6 h-6 text-accent-blue" />
          </div>
          <div>
            <h1 className="text-3xl font-headline tracking-wider text-accent-blue leading-none mb-1">THE ARCHITECTURE COUNCIL</h1>
            <p className="text-xs text-text-secondary font-mono tracking-wide">AI-Powered Design Authority</p>
          </div>
        </div>
        <div className="flex items-center gap-6 font-mono text-xs">
          <div className="text-text-muted">
            {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }).toUpperCase()}
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <TabNav />

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        <HelpSidebar />
        <div className="flex-1 overflow-y-auto bg-bg-primary">
          <div className="max-w-3xl mx-auto px-8 py-8">
            {children}
          </div>
        </div>
      </div>
    </main>
  );
}
