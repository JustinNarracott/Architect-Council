import { useRef, useEffect } from 'react';
import { AgentMessage as AgentMessageType } from '@/types';
import AgentMessage from './AgentMessage';
import { FileQuestion } from 'lucide-react';

interface ConversationStreamProps {
  messages: AgentMessageType[];
}

export default function ConversationStream({ messages }: ConversationStreamProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto px-8 py-6 custom-scrollbar relative">
      {/* Timeline Line */}
      {messages.length > 0 && (
          <div className="absolute left-8 top-6 bottom-6 w-[1px] bg-border-muted" />
      )}

      {messages.length === 0 ? (
        <div className="h-full flex flex-col items-center justify-center text-text-muted">
          <div className="w-16 h-16 border border-border-default sharp-corners flex items-center justify-center mb-4 bg-bg-elevated">
            <FileQuestion className="w-8 h-8 text-accent-blue" />
          </div>
          <p className="text-xl font-mono font-semibold tracking-wide text-accent-blue">AWAITING SUBMISSION</p>
          <p className="text-xs font-mono tracking-wide mt-2">Submit an Architecture Decision Request to begin review</p>
        </div>
      ) : (
        <div className="pl-8">
            {messages.map((msg, index) => (
            <AgentMessage key={`${msg.agent_id}-${index}`} message={msg} />
            ))}
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
