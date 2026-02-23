'use client';

import { useState, useMemo, useEffect } from 'react';
import Link from 'next/link';
import { submitCodebaseReview, fetchGovernanceConfig } from '@/lib/api';
import { useAnalysisStream } from '@/hooks/useAnalysisStream';
import TabNav from '@/components/TabNav';
import RepoSubmissionForm, { RepoFormData } from '@/components/RepoSubmissionForm';
import AgentPanel from '@/components/AgentPanel';
import TabbedAgentOutput from '@/components/TabbedAgentOutput';
import FindingsPanel from '@/components/FindingsPanel';
import CodebaseChat from '@/components/CodebaseChat';
import ExportButton from '@/components/ExportButton';
import { CodebaseRequest, CodebaseRuling, RepoMetadata } from '@/types';
import { Code2, MessageSquare } from 'lucide-react';

export default function CodebasePage() {
  const [streamUrl, setStreamUrl] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(false);
  const [repoUrl, setRepoUrl] = useState<string>('');
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [showChat, setShowChat] = useState(false);
  // Track whether analysis has ever completed for this session
  const [analysisComplete, setAnalysisComplete] = useState(false);
  // Governance status indicator
  const [governanceConfigured, setGovernanceConfigured] = useState<boolean | null>(null);

  const { messages, agentStates, agentSteps, isConnected, error, elapsedSeconds } = useAnalysisStream(streamUrl);

  // Mark analysis as complete once the stream disconnects after starting
  useEffect(() => {
    if (streamUrl && !isConnected && !error && messages.length > 0) {
      setAnalysisComplete(true);
    }
  }, [isConnected, streamUrl, error, messages.length]);

  // Load governance status on mount
  useEffect(() => {
    fetchGovernanceConfig()
      .then(overview => setGovernanceConfigured(overview.is_configured))
      .catch(() => setGovernanceConfigured(false));
  }, []);

  const handleSubmitRepo = async (formData: RepoFormData) => {
    try {
      setIsInitializing(true);
      // Display label: local path or repo URL
      setRepoUrl(formData.local_path ?? formData.repo_url ?? '');
      setAnalysisComplete(false);
      setShowChat(false);

      const request: CodebaseRequest = {
        repo_url: formData.repo_url,
        local_path: formData.local_path,
        auth_token: formData.auth_token,
        branch: formData.branch,
      };

      const response = await submitCodebaseReview(request);
      setStreamUrl(response.stream_url);
      setAnalysisId(response.analysis_id);
    } catch (err) {
      console.error('Failed to submit codebase review:', err);
      alert('Failed to submit codebase review. Please check the backend connection.');
    } finally {
      setIsInitializing(false);
    }
  };

  // Extract repo metadata from system message if present
  const repoMetadata = useMemo((): RepoMetadata | null => {
    const metaMsg = messages.find(m => m.agent_id === 'system' && m.metadata?.repo_metadata);
    if (metaMsg?.metadata?.repo_metadata) {
      return metaMsg.metadata.repo_metadata as RepoMetadata;
    }
    return null;
  }, [messages]);

  // Extract final codebase ruling
  const codebaseRuling = useMemo((): CodebaseRuling | null => {
    const rulingMsg = messages.find(m => m.message_type === 'ruling' && m.metadata?.codebase_ruling);
    if (rulingMsg?.metadata?.codebase_ruling) {
      return rulingMsg.metadata.codebase_ruling as CodebaseRuling;
    }
    return null;
  }, [messages]);

  // Status bar text
  const statusText = isConnected
    ? `ANALYSING — ${Math.floor(elapsedSeconds / 60).toString().padStart(2, '0')}:${(elapsedSeconds % 60).toString().padStart(2, '0')}`
    : error ? 'ERROR — RESUBMIT TO RETRY'
    : analysisComplete ? 'ANALYSIS COMPLETE'
    : 'AWAITING SUBMISSION';

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
            <div className={`w-1.5 h-1.5 rounded-full ${
              isConnected ? 'bg-accent-green animate-pulse'
              : error ? 'bg-accent-red'
              : analysisComplete ? 'bg-accent-green'
              : 'bg-accent-grey'
            }`} />
            {statusText}
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
        {/* Sidebar */}
        <div className="w-80 flex-none border-r border-border-default bg-bg-surface flex flex-col">
          <div className="p-4 border-b border-border-muted">
            <h2 className="font-headline text-xl text-accent-blue tracking-wide">Review Panel</h2>
          </div>
          <AgentPanel agentStates={agentStates} />
        </div>

        {/* Centre Panel */}
        <div className="flex-1 flex flex-col min-w-0 bg-bg-primary relative">

          {/* Form or review header */}
          {!streamUrl ? (
            <div className="p-6 border-b border-border-default bg-bg-surface">
              <RepoSubmissionForm onSubmit={handleSubmitRepo} isLoading={isInitializing} />
              {/* Governance status indicator */}
              {governanceConfigured !== null && (
                <div className="mt-4 flex items-center gap-2 font-mono text-xs">
                  <div className={`w-1.5 h-1.5 rounded-full flex-none ${governanceConfigured ? 'bg-accent-green' : 'bg-accent-grey'}`} />
                  {governanceConfigured ? (
                    <span className="text-accent-green">Governance rules active — agents will evaluate against your organisation standards.</span>
                  ) : (
                    <span className="text-text-muted">
                      No governance rules configured.{' '}
                      <Link href="/governance" className="text-accent-blue hover:underline">Configure now</Link>
                      {' '}to evaluate against your organisation standards.
                    </span>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="px-6 py-3 border-b border-border-default bg-bg-surface flex items-center justify-between">
              <div className="font-mono text-sm">
                <span className="text-text-muted">ANALYSING:</span>{' '}
                <span className="text-text-primary font-semibold break-all">{repoUrl}</span>
              </div>
              <div className="flex items-center gap-2 ml-4 flex-none">
                {/* Export — only after analysis completes */}
                {analysisComplete && analysisId && (
                  <ExportButton messages={messages} repoUrl={repoUrl} analysisId={analysisId} />
                )}
                {/* Chat toggle — only shown after analysis completes */}
                {analysisComplete && analysisId && (
                  <button
                    onClick={() => setShowChat(v => !v)}
                    className={`flex items-center gap-1.5 text-xs font-mono px-3 py-1 sharp-corners border transition-colors ${
                      showChat
                        ? 'bg-accent-blue text-white border-accent-blue'
                        : 'text-accent-blue border-accent-blue hover:bg-accent-blue/10'
                    }`}
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                    {showChat ? 'HIDE CHAT' : 'ASK QUESTIONS'}
                  </button>
                )}
                <button
                  onClick={() => { setStreamUrl(null); setRepoUrl(''); setAnalysisId(null); setAnalysisComplete(false); setShowChat(false); }}
                  className="text-xs font-mono text-accent-blue hover:text-accent-blue/80 border border-accent-blue px-3 py-1 sharp-corners transition-colors"
                >
                  NEW REVIEW
                </button>
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mx-6 mt-4 p-4 sharp-corners bg-accent-red/10 border-l-2 border-accent-red text-accent-red font-mono text-sm flex items-start justify-between gap-4">
              <div>
                <span className="font-bold">SYSTEM ERROR:</span> {error}
                <div className="mt-1 text-xs text-text-secondary">Submit a new request to start a fresh review.</div>
              </div>
            </div>
          )}

          {/* Content area — split between stream and chat when chat is shown */}
          <div className={`flex-1 flex min-h-0 ${showChat ? 'flex-row' : 'flex-col'}`}>

            {/* Tabbed stream panel */}
            <div className={`relative flex flex-col min-h-0 ${showChat ? 'flex-1 min-w-0 border-r border-border-default' : 'flex-1'}`}>
              <TabbedAgentOutput
                messages={messages}
                agentSteps={agentSteps}
                repoMetadata={repoMetadata}
                isAnalysing={isConnected}
              />

              {/* Findings Panel Overlay */}
              {codebaseRuling && (
                <div className="absolute bottom-4 left-4 right-4 animate-in slide-in-from-bottom-10 fade-in duration-500 z-20">
                  <FindingsPanel ruling={codebaseRuling} />
                </div>
              )}
            </div>

            {/* Chat panel — shown after analysis completes */}
            {showChat && analysisId && (
              <div className="w-96 flex-none flex flex-col min-h-0">
                <CodebaseChat analysisId={analysisId} />
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
