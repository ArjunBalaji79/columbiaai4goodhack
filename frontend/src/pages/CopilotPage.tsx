import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { MessageSquare, Send, Loader2, Bot, User, Zap } from 'lucide-react';
import { useSituationGraph } from '../hooks/useSituationGraph';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

const SUGGESTED_PROMPTS = [
  "What's our biggest risk right now?",
  "Which resources are still available?",
  "Explain the bridge contradiction",
  "Where should I send the next ambulance?",
  "What happens if we wait 10 more minutes?",
  "Which hospital has the most capacity?",
];

function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user';
  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-amber-500/20 border border-amber-500/30 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Bot className="w-4 h-4 text-amber-400" />
        </div>
      )}
      <div
        className={`max-w-2xl px-4 py-3 rounded-xl text-sm leading-relaxed ${
          isUser
            ? 'bg-zinc-700/60 text-zinc-100 rounded-br-sm'
            : 'bg-[#1a1a25] border border-[#27272a] text-zinc-200 rounded-bl-sm'
        }`}
      >
        {msg.content}
        <div className="text-xs text-zinc-600 mt-1.5">
          {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
      {isUser && (
        <div className="w-7 h-7 rounded-full bg-zinc-700/60 border border-zinc-600/30 flex items-center justify-center flex-shrink-0 mt-0.5">
          <User className="w-4 h-4 text-zinc-400" />
        </div>
      )}
    </div>
  );
}

export function CopilotPage() {
  const { graph } = useSituationGraph();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  async function sendMessage(question: string) {
    if (!question.trim() || isLoading) return;

    const userMsg: Message = {
      role: 'user',
      content: question.trim(),
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const history = messages.map(m => ({ role: m.role, content: m.content }));
      const res = await fetch('/api/copilot/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question.trim(), history }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const assistantMsg: Message = {
        role: 'assistant',
        content: data.answer,
        timestamp: data.timestamp ?? new Date().toISOString(),
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Connection error. Make sure the backend is running at localhost:8000.',
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  }

  const incidentCount = graph ? Object.keys(graph.incidents).length : 0;
  const contradictionCount = graph ? Object.values(graph.contradictions).filter(c => !c.resolved).length : 0;

  return (
    <div className="flex flex-col h-full bg-[#0a0a0f]">
      {/* Sub-header */}
      <div className="border-b border-[#27272a] px-6 py-3 flex items-center justify-between flex-shrink-0 bg-[#0d0d14]">
        <div className="flex items-center gap-3">
          <MessageSquare className="w-4 h-4 text-amber-400" />
          <span className="text-zinc-200 text-sm font-semibold">Operator Co-Pilot</span>
          <span className="text-zinc-600 text-xs">— AI-powered</span>
        </div>
        <div className="flex items-center gap-3 text-xs text-zinc-600">
          {incidentCount > 0 && <span>{incidentCount} incidents in context</span>}
          {contradictionCount > 0 && <span className="text-amber-500">{contradictionCount} unresolved contradictions</span>}
          {!graph && <span className="text-zinc-600">No active scenario — start simulation first</span>}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-3xl mx-auto space-y-4">

          {messages.length === 0 && (
            <div className="flex flex-col items-center gap-6 py-8">
              {/* Empty state */}
              <div className="text-center">
                <div className="w-16 h-16 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mx-auto mb-4">
                  <Bot className="w-8 h-8 text-amber-400" />
                </div>
                <h2 className="text-zinc-200 font-semibold mb-1">Operator Co-Pilot</h2>
                <p className="text-zinc-500 text-sm max-w-sm">
                  Ask me anything about the current situation. I have full access to the incident graph,
                  resources, contradictions, and pending decisions.
                </p>
              </div>

              {/* Suggested prompts */}
              <div className="w-full max-w-2xl">
                <p className="text-zinc-600 text-xs mb-3 text-center">Suggested questions:</p>
                <div className="grid grid-cols-2 gap-2">
                  {SUGGESTED_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      onClick={() => sendMessage(prompt)}
                      className="text-left px-3 py-2.5 rounded-lg border border-[#27272a] bg-[#1a1a25] hover:bg-[#22222f] hover:border-zinc-600 text-zinc-400 hover:text-zinc-200 text-xs transition-colors flex items-start gap-2"
                    >
                      <Zap className="w-3 h-3 text-amber-500/50 mt-0.5 flex-shrink-0" />
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Message history */}
          {messages.map((msg, i) => (
            <MessageBubble key={i} msg={msg} />
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex gap-3 justify-start">
              <div className="w-7 h-7 rounded-full bg-amber-500/20 border border-amber-500/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Bot className="w-4 h-4 text-amber-400" />
              </div>
              <div className="bg-[#1a1a25] border border-[#27272a] px-4 py-3 rounded-xl rounded-bl-sm">
                <div className="flex items-center gap-1.5">
                  <Loader2 className="w-3 h-3 animate-spin text-amber-400" />
                  <span className="text-zinc-500 text-xs">Analyzing the situation…</span>
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-[#27272a] px-6 py-4 flex-shrink-0 bg-[#0d0d14]">
        <div className="max-w-3xl mx-auto flex gap-3 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about the situation… (Enter to send, Shift+Enter for new line)"
            rows={2}
            className="flex-1 bg-[#1a1a25] border border-[#27272a] focus:border-zinc-500 rounded-xl px-4 py-3 text-sm text-zinc-200 placeholder-zinc-600 resize-none outline-none transition-colors"
            disabled={isLoading}
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || isLoading}
            className="p-3 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex-shrink-0"
            title="Send (Enter)"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="text-zinc-700 text-xs mt-2 max-w-3xl mx-auto">
          AI has access to the full situation graph including all incidents, resources, and contradictions.
        </p>
      </div>
    </div>
  );
}
