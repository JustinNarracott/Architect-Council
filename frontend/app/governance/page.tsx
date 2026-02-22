'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Settings2, Code2, ChevronDown, ChevronRight } from 'lucide-react';
import TabNav from '@/components/TabNav';
import { fetchGovernanceConfig, updateGovernanceFile, GovernanceFile } from '@/lib/api';

const FILE_LABELS: Record<string, string> = {
  'tech-radar.yaml': 'Technology Radar',
  'coding-standards.yaml': 'Coding Standards',
  'architecture.yaml': 'Architecture Standards',
  'security.yaml': 'Security Policies',
};

const FILE_DESCRIPTIONS: Record<string, string> = {
  'tech-radar.yaml': 'Classify technologies by adoption status (adopt, trial, assess, hold).',
  'coding-standards.yaml': 'Naming conventions, required/prohibited patterns, and quality thresholds.',
  'architecture.yaml': 'Approved architecture styles, constraints, API standards, and data layer rules.',
  'security.yaml': 'Secrets policy, authentication requirements, dependency scanning, and input validation.',
};

interface EditorState {
  expanded: boolean;
  yaml: string;
  saving: boolean;
  saved: boolean;
  error: string | null;
}

export default function GovernancePage() {
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [files, setFiles] = useState<GovernanceFile[]>([]);
  const [isConfigured, setIsConfigured] = useState(false);
  const [editorStates, setEditorStates] = useState<Record<string, EditorState>>({});

  useEffect(() => {
    loadConfig();
  }, []);

  async function loadConfig() {
    try {
      setIsLoading(true);
      setLoadError(null);
      const overview = await fetchGovernanceConfig();
      setFiles(overview.files);
      setIsConfigured(overview.is_configured);

      // Initialise editor states
      const states: Record<string, EditorState> = {};
      for (const file of overview.files) {
        states[file.filename] = {
          expanded: false,
          yaml: file.raw_yaml,
          saving: false,
          saved: false,
          error: null,
        };
      }
      setEditorStates(states);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : 'Failed to load governance config');
    } finally {
      setIsLoading(false);
    }
  }

  function toggleExpanded(filename: string) {
    setEditorStates(prev => ({
      ...prev,
      [filename]: { ...prev[filename], expanded: !prev[filename].expanded },
    }));
  }

  function handleYamlChange(filename: string, value: string) {
    setEditorStates(prev => ({
      ...prev,
      [filename]: { ...prev[filename], yaml: value, error: null, saved: false },
    }));
  }

  async function handleSave(filename: string) {
    const state = editorStates[filename];
    if (!state) return;

    setEditorStates(prev => ({
      ...prev,
      [filename]: { ...prev[filename], saving: true, error: null, saved: false },
    }));

    try {
      await updateGovernanceFile(filename, state.yaml);
      setEditorStates(prev => ({
        ...prev,
        [filename]: { ...prev[filename], saving: false, saved: true },
      }));
      // Update configured status
      setIsConfigured(true);
      // Auto-clear "Saved" after 3 seconds
      setTimeout(() => {
        setEditorStates(prev => ({
          ...prev,
          [filename]: { ...prev[filename], saved: false },
        }));
      }, 3000);
    } catch (err) {
      setEditorStates(prev => ({
        ...prev,
        [filename]: {
          ...prev[filename],
          saving: false,
          error: err instanceof Error ? err.message : 'Failed to save',
        },
      }));
    }
  }

  const hasContent = (file: GovernanceFile) => file.raw_yaml.trim().length > 0;

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
            <div className={`w-1.5 h-1.5 rounded-full ${isConfigured ? 'bg-accent-green' : 'bg-accent-grey'}`} />
            {isConfigured ? 'GOVERNANCE ACTIVE' : 'NO GOVERNANCE RULES'}
          </div>
          <div className="text-text-muted">
            {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }).toUpperCase()}
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <TabNav />

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto bg-bg-primary">
        <div className="max-w-4xl mx-auto px-6 py-8">

          {/* Page header */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <Settings2 className="w-6 h-6 text-accent-blue" />
              <h2 className="font-headline text-2xl text-accent-blue tracking-wide">Governance Configuration</h2>
            </div>
            <p className="text-text-secondary font-mono text-sm">
              Define your organisation&apos;s technology standards, coding rules, architecture patterns, and security policies.
              These rules are injected into every codebase review — agents evaluate against YOUR specific standards.
            </p>
          </div>

          {/* Load error */}
          {loadError && (
            <div className="mb-6 p-4 sharp-corners bg-accent-red/10 border-l-2 border-accent-red text-accent-red font-mono text-sm">
              <span className="font-bold">ERROR:</span> {loadError}
            </div>
          )}

          {/* Loading state */}
          {isLoading && (
            <div className="flex items-center gap-3 text-text-muted font-mono text-sm py-12 justify-center">
              <div className="w-1.5 h-1.5 rounded-full bg-accent-blue animate-pulse" />
              Loading governance config...
            </div>
          )}

          {/* Config file editors */}
          {!isLoading && files.map((file) => {
            const state = editorStates[file.filename];
            if (!state) return null;
            const label = FILE_LABELS[file.filename] ?? file.filename;
            const description = FILE_DESCRIPTIONS[file.filename] ?? '';
            const configured = hasContent(file) || state.yaml.trim().length > 0;

            return (
              <div key={file.filename} className="mb-4 border border-border-default sharp-corners bg-bg-surface">
                {/* Section header */}
                <button
                  onClick={() => toggleExpanded(file.filename)}
                  className="w-full flex items-center justify-between px-5 py-4 hover:bg-bg-elevated transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full flex-none ${configured ? 'bg-accent-green' : 'bg-accent-grey'}`} />
                    <div className="text-left">
                      <div className="font-mono text-sm font-semibold text-text-primary">{label}</div>
                      <div className="font-mono text-xs text-text-muted mt-0.5">{description}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 flex-none ml-4">
                    <span className={`font-mono text-xs px-2 py-0.5 sharp-corners ${
                      configured
                        ? 'text-accent-green border border-accent-green/40 bg-accent-green/10'
                        : 'text-text-muted border border-border-muted'
                    }`}>
                      {configured ? 'CONFIGURED' : 'EMPTY'}
                    </span>
                    {state.expanded
                      ? <ChevronDown className="w-4 h-4 text-text-secondary" />
                      : <ChevronRight className="w-4 h-4 text-text-secondary" />
                    }
                  </div>
                </button>

                {/* Expanded editor */}
                {state.expanded && (
                  <div className="border-t border-border-muted">
                    <div className="p-4">
                      <div className="mb-2 flex items-center justify-between">
                        <span className="font-mono text-xs text-text-muted">{file.filename}</span>
                        <span className="font-mono text-xs text-text-muted">YAML</span>
                      </div>
                      <textarea
                        value={state.yaml}
                        onChange={(e) => handleYamlChange(file.filename, e.target.value)}
                        className="bg-bg-elevated border border-border-default font-mono text-sm text-text-primary p-4 w-full min-h-[300px] resize-y sharp-corners focus:outline-none focus:border-accent-blue/50 transition-colors"
                        spellCheck={false}
                        placeholder={`# ${label}\n# Paste your YAML configuration here`}
                      />

                      {/* Feedback */}
                      {state.error && (
                        <div className="mt-2 p-3 sharp-corners bg-accent-red/10 border-l-2 border-accent-red text-accent-red font-mono text-xs">
                          <span className="font-bold">YAML ERROR:</span> {state.error}
                        </div>
                      )}
                      {state.saved && (
                        <div className="mt-2 p-3 sharp-corners bg-accent-green/10 border-l-2 border-accent-green text-accent-green font-mono text-xs">
                          Saved successfully.
                        </div>
                      )}

                      {/* Save button */}
                      <div className="mt-3 flex justify-end">
                        <button
                          onClick={() => handleSave(file.filename)}
                          disabled={state.saving}
                          className="bg-accent-blue text-bg-primary font-mono text-xs px-5 py-2 sharp-corners hover:bg-accent-blue/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          {state.saving ? 'SAVING...' : 'SAVE'}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}

          {/* Bottom info */}
          {!isLoading && (
            <div className="mt-8 p-4 sharp-corners border border-border-muted bg-bg-surface">
              <p className="font-mono text-xs text-text-muted">
                <span className="text-text-secondary font-semibold">How this works:</span>{' '}
                Governance rules are loaded each time a codebase review starts. Changes take effect on the next review.
                If all files are empty, agents fall back to generic best-practice evaluation.
              </p>
              <p className="font-mono text-xs text-text-muted mt-2">
                Go to the{' '}
                <Link href="/codebase" className="text-accent-blue hover:underline">Codebase Review</Link>
                {' '}tab to run a review with your configured rules.
              </p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
