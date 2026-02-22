import { useState, useEffect } from 'react';
import { GitBranch, Loader2, Lock, Link as LinkIcon, FolderOpen } from 'lucide-react';
import { cn } from '@/lib/utils';
import { fetchLocalRepos } from '@/lib/api';

interface RepoSubmissionFormProps {
  onSubmit: (data: RepoFormData) => void;
  isLoading: boolean;
}

export interface RepoFormData {
  repo_url?: string;
  local_path?: string;
  auth_token?: string;
  branch?: string;
}

type SourceMode = 'github' | 'local';

const REPO_URL_PATTERN = /^https?:\/\/(github\.com|gitlab\.com|bitbucket\.org)\/.+\/.+/;

function validateRepoUrl(url: string): string | null {
  if (!url.trim()) return 'Repository URL is required';
  if (!REPO_URL_PATTERN.test(url.trim())) {
    return 'Must be a valid GitHub, GitLab, or Bitbucket URL (e.g. https://github.com/org/repo)';
  }
  return null;
}

export default function RepoSubmissionForm({ onSubmit, isLoading }: RepoSubmissionFormProps) {
  const [sourceMode, setSourceMode] = useState<SourceMode>('github');
  const [repoUrl, setRepoUrl] = useState('');
  const [selectedFolder, setSelectedFolder] = useState('');
  const [authToken, setAuthToken] = useState('');
  const [branch, setBranch] = useState('');
  const [urlError, setUrlError] = useState<string | null>(null);
  const [showToken, setShowToken] = useState(false);
  const [localRepos, setLocalRepos] = useState<string[]>([]);
  const [localReposLoading, setLocalReposLoading] = useState(false);

  // Fetch available local repos whenever LOCAL PATH mode is active
  useEffect(() => {
    if (sourceMode !== 'local') return;
    setLocalReposLoading(true);
    fetchLocalRepos()
      .then((repos) => {
        setLocalRepos(repos);
        setSelectedFolder('');
      })
      .finally(() => setLocalReposLoading(false));
  }, [sourceMode]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (sourceMode === 'github') {
      const error = validateRepoUrl(repoUrl);
      if (error) { setUrlError(error); return; }
      setUrlError(null);
      onSubmit({
        repo_url: repoUrl.trim(),
        auth_token: authToken.trim() || undefined,
        branch: branch.trim() || undefined,
      });
    } else {
      if (!selectedFolder) return;
      onSubmit({
        local_path: `/repos/${selectedFolder}`,
        branch: branch.trim() || undefined,
      });
    }
  };

  const isValid =
    sourceMode === 'github'
      ? Boolean(repoUrl.trim()) && !validateRepoUrl(repoUrl)
      : Boolean(selectedFolder);

  const switchMode = (mode: SourceMode) => {
    setSourceMode(mode);
    setUrlError(null);
  };

  return (
    <form onSubmit={handleSubmit} className="w-full relative z-10 font-mono">

      {/* Source Toggle */}
      <div className="flex mb-4 border border-border-default sharp-corners overflow-hidden">
        <button
          type="button"
          onClick={() => switchMode('github')}
          className={cn(
            'flex-1 px-4 py-2 text-xs font-mono uppercase tracking-wider transition-colors',
            sourceMode === 'github'
              ? 'bg-accent-blue text-white'
              : 'bg-bg-primary text-text-muted hover:text-text-secondary'
          )}
          disabled={isLoading}
        >
          <LinkIcon className="inline w-3.5 h-3.5 mr-1.5 -mt-0.5" />
          GITHUB URL
        </button>
        <button
          type="button"
          onClick={() => switchMode('local')}
          className={cn(
            'flex-1 px-4 py-2 text-xs font-mono uppercase tracking-wider transition-colors border-l border-border-default',
            sourceMode === 'local'
              ? 'bg-accent-blue text-white'
              : 'bg-bg-primary text-text-muted hover:text-text-secondary'
          )}
          disabled={isLoading}
        >
          <FolderOpen className="inline w-3.5 h-3.5 mr-1.5 -mt-0.5" />
          LOCAL PATH
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">

        {sourceMode === 'github' ? (
          <>
            {/* Repo URL — full width */}
            <div className="col-span-2">
              <label className="block text-xs text-text-secondary mb-2 font-mono uppercase tracking-wider">
                Repository URL *
              </label>
              <div className="relative">
                <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
                  <LinkIcon className="w-4 h-4 text-text-muted" />
                </div>
                <input
                  type="url"
                  value={repoUrl}
                  onChange={(e) => { setRepoUrl(e.target.value); if (urlError) setUrlError(null); }}
                  placeholder="https://github.com/org/repository"
                  className={cn(
                    'w-full bg-bg-primary border text-text-primary placeholder:text-text-muted pl-10 pr-4 py-2 sharp-corners outline-none transition-colors font-mono text-sm',
                    urlError
                      ? 'border-accent-red focus:border-accent-red'
                      : 'border-border-default focus:border-accent-blue'
                  )}
                  disabled={isLoading}
                  required
                />
              </div>
              {urlError && (
                <p className="mt-1.5 text-xs font-mono text-accent-red">{urlError}</p>
              )}
            </div>

            {/* Branch */}
            <div>
              <label className="block text-xs text-text-secondary mb-2 font-mono uppercase tracking-wider">
                Branch
              </label>
              <div className="relative">
                <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
                  <GitBranch className="w-4 h-4 text-text-muted" />
                </div>
                <input
                  type="text"
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  placeholder="main"
                  className="w-full bg-bg-primary border border-border-default focus:border-accent-blue text-text-primary placeholder:text-text-muted pl-10 pr-4 py-2 sharp-corners outline-none transition-colors font-mono text-sm"
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* Auth Token */}
            <div>
              <label className="block text-xs text-text-secondary mb-2 font-mono uppercase tracking-wider">
                Auth Token <span className="text-text-muted normal-case">(private repos)</span>
              </label>
              <div className="relative">
                <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
                  <Lock className="w-4 h-4 text-text-muted" />
                </div>
                <input
                  type={showToken ? 'text' : 'password'}
                  value={authToken}
                  onChange={(e) => setAuthToken(e.target.value)}
                  placeholder="ghp_••••••••••••"
                  className="w-full bg-bg-primary border border-border-default focus:border-accent-blue text-text-primary placeholder:text-text-muted pl-10 pr-16 py-2 sharp-corners outline-none transition-colors font-mono text-sm"
                  disabled={isLoading}
                  autoComplete="off"
                />
                {authToken && (
                  <button
                    type="button"
                    onClick={() => setShowToken(!showToken)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-mono text-text-muted hover:text-accent-blue transition-colors"
                    tabIndex={-1}
                  >
                    {showToken ? 'HIDE' : 'SHOW'}
                  </button>
                )}
              </div>
            </div>
          </>
        ) : (
          <>
            {/* Local project dropdown — full width */}
            <div className="col-span-2">
              <label className="block text-xs text-text-secondary mb-2 font-mono uppercase tracking-wider">
                Project <span className="text-text-muted normal-case">(under D:\Projects)</span> *
              </label>
              <div className="relative">
                <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none z-10">
                  <FolderOpen className="w-4 h-4 text-text-muted" />
                </div>
                {localReposLoading ? (
                  <div className="w-full bg-bg-primary border border-border-default text-text-muted pl-10 pr-4 py-2 sharp-corners font-mono text-sm flex items-center gap-2">
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Loading projects...
                  </div>
                ) : localRepos.length === 0 ? (
                  <div className="w-full bg-bg-primary border border-border-default text-text-muted pl-10 pr-4 py-2 sharp-corners font-mono text-sm">
                    No projects found in D:\Projects mount
                  </div>
                ) : (
                  <select
                    value={selectedFolder}
                    onChange={(e) => setSelectedFolder(e.target.value)}
                    className="w-full bg-bg-primary border border-border-default focus:border-accent-blue text-text-primary pl-10 pr-4 py-2 sharp-corners outline-none transition-colors font-mono text-sm appearance-none cursor-pointer"
                    disabled={isLoading}
                  >
                    <option value="" disabled>Select a project...</option>
                    {localRepos.map((repo) => (
                      <option key={repo} value={repo}>{repo}</option>
                    ))}
                  </select>
                )}
              </div>
              <p className="mt-1.5 text-xs font-mono text-text-muted">
                Will be mapped to <span className="text-accent-blue">/repos/{selectedFolder || '<folder>'}</span> inside the container
              </p>
            </div>

            {/* Branch — still visible for local */}
            <div className="col-span-2">
              <label className="block text-xs text-text-secondary mb-2 font-mono uppercase tracking-wider">
                Branch <span className="text-text-muted normal-case">(optional, for display only)</span>
              </label>
              <div className="relative">
                <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
                  <GitBranch className="w-4 h-4 text-text-muted" />
                </div>
                <input
                  type="text"
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  placeholder="main"
                  className="w-full bg-bg-primary border border-border-default focus:border-accent-blue text-text-primary placeholder:text-text-muted pl-10 pr-4 py-2 sharp-corners outline-none transition-colors font-mono text-sm"
                  disabled={isLoading}
                />
              </div>
            </div>
          </>
        )}
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={isLoading || !isValid}
        className={cn(
          'w-full flex items-center justify-center gap-2 px-6 py-3 font-bold tracking-wider transition-all duration-300 sharp-corners border font-mono text-sm',
          isLoading || !isValid
            ? 'text-text-muted cursor-not-allowed bg-bg-elevated border-border-muted'
            : 'text-bg-primary bg-accent-blue hover:bg-accent-purple border-accent-blue hover:border-accent-purple'
        )}
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>{sourceMode === 'local' ? 'INDEXING...' : 'CLONING & INDEXING...'}</span>
          </>
        ) : (
          <>
            {sourceMode === 'local' ? <FolderOpen className="w-4 h-4" /> : <GitBranch className="w-4 h-4" />}
            <span>ANALYSE {sourceMode === 'local' ? 'LOCAL PROJECT' : 'REPOSITORY'}</span>
          </>
        )}
      </button>
    </form>
  );
}
