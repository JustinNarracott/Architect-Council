import { useState } from 'react';
import { Search, Loader2, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TickerInputProps {
  onAnalyze: (ticker: string) => void;
  isLoading: boolean;
}

export default function TickerInput({ onAnalyze, isLoading }: TickerInputProps) {
  const [ticker, setTicker] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (ticker.trim()) {
      onAnalyze(ticker.trim().toUpperCase());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full relative z-10 font-mono">
      <div className="relative group flex items-center bg-bg-primary border-b-2 border-gold-muted/30 focus-within:border-gold-primary transition-colors duration-300">
        <div className="pl-4 text-gold-muted group-focus-within:text-gold-primary transition-colors">
          <Search className="w-5 h-5" />
        </div>
        
        <input
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          placeholder="ENTER TICKER SYMBOL..."
          className="flex-1 bg-transparent border-none outline-none text-2xl text-gold-primary placeholder:text-gold-muted/30 px-6 py-4 uppercase tracking-widest selection:bg-gold-primary selection:text-bg-primary"
          disabled={isLoading}
          autoFocus
        />

        <button
          type="submit"
          disabled={isLoading || !ticker.trim()}
          className={cn(
            "relative overflow-hidden px-8 py-4 font-bold tracking-wider transition-all duration-300 sharp-corners border-l border-gold-muted/30",
            isLoading || !ticker.trim()
              ? "text-gold-muted/30 cursor-not-allowed bg-transparent"
              : "text-bg-primary bg-gold-muted hover:text-bg-primary group/btn"
          )}
        >
          {/* Fill Animation Layer */}
          <div className={cn(
            "absolute inset-0 bg-gold-primary transform -translate-x-full transition-transform duration-300 ease-out group-hover/btn:translate-x-0",
            isLoading ? "translate-x-0 animate-pulse" : ""
          )} />

          <span className="relative z-10 flex items-center gap-2">
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>INITIALIZING SYSTEM...</span>
              </>
            ) : (
              <>
                <span>INITIATE ANALYSIS</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </span>
        </button>
      </div>
      
      {/* Decorative corners */}
      <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-gold-muted pointer-events-none" />
      <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-gold-muted pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-gold-muted pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-gold-muted pointer-events-none" />
    </form>
  );
}
