import { ReactNode } from 'react';
import { Lightbulb, AlertTriangle, Info, AlertCircle } from 'lucide-react';

type CalloutType = 'tip' | 'warning' | 'note' | 'important';

const CALLOUT_STYLES: Record<CalloutType, { border: string; bg: string; text: string; icon: typeof Info; label: string }> = {
  tip: {
    border: 'border-accent-green',
    bg: 'bg-accent-green/5',
    text: 'text-accent-green',
    icon: Lightbulb,
    label: 'TIP',
  },
  warning: {
    border: 'border-accent-amber',
    bg: 'bg-accent-amber/5',
    text: 'text-accent-amber',
    icon: AlertTriangle,
    label: 'WARNING',
  },
  note: {
    border: 'border-accent-blue',
    bg: 'bg-accent-blue/5',
    text: 'text-accent-blue',
    icon: Info,
    label: 'NOTE',
  },
  important: {
    border: 'border-accent-red',
    bg: 'bg-accent-red/5',
    text: 'text-accent-red',
    icon: AlertCircle,
    label: 'IMPORTANT',
  },
};

interface HelpCalloutProps {
  type: CalloutType;
  children: ReactNode;
}

export default function HelpCallout({ type, children }: HelpCalloutProps) {
  const style = CALLOUT_STYLES[type];
  const Icon = style.icon;

  return (
    <div className={`my-4 p-4 sharp-corners ${style.bg} border-l-2 ${style.border}`}>
      <div className="flex items-start gap-3">
        <Icon className={`w-4 h-4 mt-0.5 flex-none ${style.text}`} />
        <div>
          <span className={`font-mono text-xs font-bold ${style.text}`}>{style.label}</span>
          <div className="text-text-primary text-sm mt-1 leading-relaxed">{children}</div>
        </div>
      </div>
    </div>
  );
}
