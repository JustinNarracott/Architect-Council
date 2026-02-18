'use client';

import { useState, useMemo } from 'react';
import { submitReview } from '@/lib/api';
import { useAnalysisStream } from '@/hooks/useAnalysisStream';
import ADRSubmissionForm, { ADRFormData } from '@/components/ADRSubmissionForm';
import { ADRRequest } from '@/types';
import AgentPanel from '@/components/AgentPanel';
import TabbedAgentOutput from '@/components/TabbedAgentOutput';
import ResultsPanel from '@/components/ResultsPanel';
import { ArchitectureRuling } from '@/types';
import { Code2 } from 'lucide-react';
import TabNav from '@/components/TabNav';
import ExportButton from '@/components/ExportButton';

export default function Home() {
  const [streamUrl, setStreamUrl] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(false);

  const { messages, agentStates, isConnected, error, elapsedSeconds } = useAnalysisStream(streamUrl);

  const handleSubmitADR = async (formData: ADRFormData) => {
    try {
      setIsInitializing(true);

      // Map form data (strings) to API contract (typed)
      const request: ADRRequest = {
        title: formData.title,
        technology: formData.technology,
        reason: formData.reason || "No reason provided",
        affected_services: formData.affected_services
          ? formData.affected_services.split(",").map(s => s.trim()).filter(Boolean)
          : [],
        data_classification: formData.data_classification || "OFFICIAL",
        proposer: formData.proposer || "Unknown",
      };

      const response = await submitReview(request);
      setStreamUrl(response.stream_url);
    } catch (err) {
      console.error('Failed to submit ADR:', err);
      alert('Failed to submit ADR. Please check backend connection.');
    } finally {
      setIsInitializing(false);
    }
  };

  const finalReport = useMemo(() => {
    const rulingMsg = messages.find(m => m.message_type === 'ruling');
    if (rulingMsg?.metadata) {
      return rulingMsg.metadata as unknown as ArchitectureRuling;
    }
    return null;
  }, [messages]);

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
          <div className="flex items-center gap-2 px-3 py-1 border border-border-default bg-bg-elevated sharp-corners text-text-secondary">
            <div className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-accent-green animate-pulse' : error ? 'bg-accent-red' : 'bg-accent-grey'}`} />
            {isConnected
              ? `REVIEW IN PROGRESS — ${Math.floor(elapsedSeconds / 60).toString().padStart(2, '0')}:${(elapsedSeconds % 60).toString().padStart(2, '0')}`
              : error ? 'ERROR — RESUBMIT TO RETRY'
              : 'AWAITING SUBMISSION'}
          </div>
          <div className="text-text-muted">
             {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }).toUpperCase()}
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <TabNav />

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - Review Panel */}
        <div className="w-80 flex-none border-r border-border-default bg-bg-surface flex flex-col">
            <div className="p-4 border-b border-border-muted">
                <h2 className="font-headline text-xl text-accent-blue tracking-wide">Review Panel</h2>
            </div>
            <AgentPanel agentStates={agentStates} />
        </div>

        {/* Center Panel */}
        <div className="flex-1 flex flex-col min-w-0 bg-bg-primary relative">

            {/* ADR Submission Form — collapses after submission to give stream full space */}
            {!streamUrl ? (
              <div className="p-6 border-b border-border-default bg-bg-surface">
                  <ADRSubmissionForm onSubmit={handleSubmitADR} isLoading={isInitializing} />
              </div>
            ) : (
              <div className="px-6 py-3 border-b border-border-default bg-bg-surface flex items-center justify-between">
                  <div className="font-mono text-sm">
                    <span className="text-text-muted">REVIEWING:</span>{' '}
                    <span className="text-text-primary font-semibold">{messages[0]?.content?.match(/for '([^']+)'/)?.[1] || 'Architecture Decision'}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <ExportButton messages={messages} />
                    <button
                      onClick={() => { setStreamUrl(null); }}
                      className="text-xs font-mono text-accent-blue hover:text-accent-blue/80 border border-accent-blue px-3 py-1 sharp-corners transition-colors"
                    >
                      NEW REVIEW
                    </button>
                  </div>
              </div>
            )}

            {/* Error Display */}
            {error && (
                <div className="mx-6 mt-4 p-4 sharp-corners bg-accent-red/10 border-l-2 border-accent-red text-accent-red font-mono text-sm flex items-start justify-between gap-4">
                    <div>
                      <span className="font-bold">SYSTEM ERROR:</span> {error}
                      <div className="mt-1 text-xs text-text-secondary">Submit a new request to start a fresh review.</div>
                    </div>
                </div>
            )}

            {/* Content Area — tabbed output fills all available space */}
            <div className="flex-1 flex flex-col min-h-0 relative">
                <TabbedAgentOutput
                  messages={messages}
                  isAnalysing={isConnected}
                  mode="adr"
                />

                {/* Results Panel Overlay — compact ruling summary above tabbed detail */}
                {finalReport && (
                    <div className="absolute bottom-4 left-4 right-4 animate-in slide-in-from-bottom-10 fade-in duration-500 z-20">
                        <ResultsPanel report={finalReport} />
                    </div>
                )}
            </div>
        </div>
      </div>
    </main>
  );
}
