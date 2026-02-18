import { useState } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ADRSubmissionFormProps {
  onSubmit: (data: ADRFormData) => void;
  isLoading: boolean;
}

export interface ADRFormData {
  title: string;
  technology: string;
  reason: string;
  affected_services: string;
  data_classification: string;
  proposer: string;
}

const DATA_CLASSIFICATIONS = [
  'PUBLIC',
  'OFFICIAL',
  'OFFICIAL-SENSITIVE',
  'SECRET'
];

export default function ADRSubmissionForm({ onSubmit, isLoading }: ADRSubmissionFormProps) {
  const [formData, setFormData] = useState<ADRFormData>({
    title: '',
    technology: '',
    reason: '',
    affected_services: '',
    data_classification: 'OFFICIAL',
    proposer: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.title.trim() && formData.technology.trim()) {
      onSubmit(formData);
    }
  };

  const handleChange = (field: keyof ADRFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const isValid = formData.title.trim() && formData.technology.trim();

  return (
    <form onSubmit={handleSubmit} className="w-full relative z-10 font-mono">
      <div className="grid grid-cols-2 gap-4 mb-4">
        {/* Title - Full Width */}
        <div className="col-span-2">
          <label className="block text-xs text-text-secondary mb-2 font-mono uppercase tracking-wider">
            Decision Title *
          </label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) => handleChange('title', e.target.value)}
            placeholder="e.g. Add Redis caching to Customer API"
            className="w-full bg-bg-primary border border-border-default focus:border-accent-blue text-text-primary placeholder:text-text-muted px-4 py-2 sharp-corners outline-none transition-colors font-mono text-sm"
            disabled={isLoading}
            required
          />
        </div>

        {/* Technology */}
        <div>
          <label className="block text-xs text-text-secondary mb-2 font-mono uppercase tracking-wider">
            Technology *
          </label>
          <input
            type="text"
            value={formData.technology}
            onChange={(e) => handleChange('technology', e.target.value)}
            placeholder="e.g. Redis 7.x"
            className="w-full bg-bg-primary border border-border-default focus:border-accent-blue text-text-primary placeholder:text-text-muted px-4 py-2 sharp-corners outline-none transition-colors font-mono text-sm"
            disabled={isLoading}
            required
          />
        </div>

        {/* Data Classification */}
        <div>
          <label className="block text-xs text-text-secondary mb-2 font-mono uppercase tracking-wider">
            Data Classification
          </label>
          <select
            value={formData.data_classification}
            onChange={(e) => handleChange('data_classification', e.target.value)}
            className="w-full bg-bg-primary border border-border-default focus:border-accent-blue text-text-primary px-4 py-2 sharp-corners outline-none transition-colors font-mono text-sm"
            disabled={isLoading}
          >
            {DATA_CLASSIFICATIONS.map(classification => (
              <option key={classification} value={classification}>{classification}</option>
            ))}
          </select>
        </div>

        {/* Affected Services */}
        <div>
          <label className="block text-xs text-text-secondary mb-2 font-mono uppercase tracking-wider">
            Affected Services
          </label>
          <input
            type="text"
            value={formData.affected_services}
            onChange={(e) => handleChange('affected_services', e.target.value)}
            placeholder="customer-api, order-service"
            className="w-full bg-bg-primary border border-border-default focus:border-accent-blue text-text-primary placeholder:text-text-muted px-4 py-2 sharp-corners outline-none transition-colors font-mono text-sm"
            disabled={isLoading}
          />
        </div>

        {/* Proposer */}
        <div>
          <label className="block text-xs text-text-secondary mb-2 font-mono uppercase tracking-wider">
            Proposer
          </label>
          <input
            type="text"
            value={formData.proposer}
            onChange={(e) => handleChange('proposer', e.target.value)}
            placeholder="Platform Team"
            className="w-full bg-bg-primary border border-border-default focus:border-accent-blue text-text-primary placeholder:text-text-muted px-4 py-2 sharp-corners outline-none transition-colors font-mono text-sm"
            disabled={isLoading}
          />
        </div>

        {/* Reason - Full Width */}
        <div className="col-span-2">
          <label className="block text-xs text-text-secondary mb-2 font-mono uppercase tracking-wider">
            Reason
          </label>
          <textarea
            value={formData.reason}
            onChange={(e) => handleChange('reason', e.target.value)}
            placeholder="e.g. Reduce p95 latency by 40%"
            rows={3}
            className="w-full bg-bg-primary border border-border-default focus:border-accent-blue text-text-primary placeholder:text-text-muted px-4 py-2 sharp-corners outline-none transition-colors resize-none font-mono text-sm"
            disabled={isLoading}
          />
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading || !isValid}
        className={cn(
          "w-full flex items-center justify-center gap-2 px-6 py-3 font-bold tracking-wider transition-all duration-300 sharp-corners border font-mono text-sm",
          isLoading || !isValid
            ? "text-text-muted cursor-not-allowed bg-bg-elevated border-border-muted"
            : "text-bg-primary bg-accent-blue hover:bg-accent-purple border-accent-blue hover:border-accent-purple"
        )}
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>SUBMITTING FOR REVIEW...</span>
          </>
        ) : (
          <>
            <Send className="w-4 h-4" />
            <span>SUBMIT FOR REVIEW</span>
          </>
        )}
      </button>
    </form>
  );
}
