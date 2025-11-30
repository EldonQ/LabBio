import React, { useRef, useEffect } from 'react';
import { Send, Cpu, User, Play, RefreshCw, Terminal, CheckCircle2, ChevronDown, ChevronRight, BarChart3, AlertCircle } from 'lucide-react';
import { ChatMessage, MessageType, ExecutionLog } from '../types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  isProcessing: boolean;
  onSendMessage: (msg: string) => void;
  onRunScript: (msgId: string) => void;
}

const ThinkingProcess: React.FC<{ thoughts: string[] }> = ({ thoughts }) => {
  const [isOpen, setIsOpen] = React.useState(true);

  return (
    <div className="mb-4 rounded-lg border border-slate-200 bg-slate-50 overflow-hidden text-sm">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 bg-slate-100 hover:bg-slate-200/50 transition-colors"
      >
        <div className="flex items-center gap-2 text-slate-600 font-medium">
          <RefreshCw className={`w-4 h-4 ${thoughts.length > 0 && thoughts[thoughts.length-1].includes('...') ? 'animate-spin' : ''}`} />
          <span>Reasoning Process (Chain of Thought)</span>
        </div>
        {isOpen ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
      </button>
      
      {isOpen && (
        <div className="p-3 space-y-2">
          {thoughts.map((thought, idx) => (
            <div key={idx} className="flex items-start gap-2.5 animate-in fade-in slide-in-from-left-2 duration-300">
              <div className="mt-1 min-w-[16px]">
                 {thought.includes('...') ? (
                   <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                 ) : (
                   <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                 )}
              </div>
              <span className={`font-mono text-xs ${thought.includes('...') ? 'text-slate-500 italic' : 'text-slate-700'}`}>
                {thought}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const TerminalOutput: React.FC<{ logs: ExecutionLog[] }> = ({ logs }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="mt-4 rounded-lg overflow-hidden border border-slate-800 bg-[#0c0c0c] shadow-lg font-mono text-xs">
      <div className="flex items-center justify-between px-3 py-1.5 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center gap-2 text-slate-400">
          <Terminal className="w-3 h-3" />
          <span>ubuntu@muscle-node:~/execution_logs</span>
        </div>
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-slate-600" />
          <div className="w-2.5 h-2.5 rounded-full bg-slate-600" />
        </div>
      </div>
      <div className="p-3 h-48 overflow-y-auto scrollbar-thin text-slate-300 space-y-1">
        {logs.map((log, i) => (
          <div key={i} className={`${
            log.level === 'error' ? 'text-red-400' : 
            log.level === 'success' ? 'text-green-400' : 
            log.level === 'warn' ? 'text-yellow-400' : 'text-slate-300'
          }`}>
            <span className="opacity-50 mr-2">[{log.timestamp}]</span>
            <span>{log.message}</span>
          </div>
        ))}
        {logs.length === 0 && <span className="text-slate-600 italic">Waiting for execution...</span>}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};

const ResultChart: React.FC<{ data: any[] }> = ({ data }) => {
  return (
    <div className="mt-4 p-4 bg-white rounded-lg border border-slate-200 shadow-sm">
      <h4 className="flex items-center gap-2 font-semibold text-slate-800 mb-4">
        <BarChart3 className="w-4 h-4 text-bio-600" />
        Species Abundance Analysis
      </h4>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 40 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
            <XAxis type="number" stroke="#64748b" fontSize={10} />
            <YAxis 
              dataKey="name" 
              type="category" 
              width={120} 
              stroke="#64748b" 
              fontSize={11} 
              tick={{fill: '#334155'}}
            />
            <Tooltip 
              contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
              cursor={{fill: '#f1f5f9'}}
            />
            <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={20}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.name === 'Unassigned' ? '#cbd5e1' : '#22c55e'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

const ChatInterface: React.FC<ChatInterfaceProps> = ({ messages, isProcessing, onSendMessage, onRunScript }) => {
  const [input, setInput] = React.useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, messages[messages.length-1]?.agentState?.logs]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isProcessing) {
      onSendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="flex flex-col h-full bg-white relative">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-8 scrollbar-thin pb-32">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 opacity-60">
            <Cpu className="w-16 h-16 mb-4 stroke-1" />
            <p className="text-lg font-light">Local-IA BioStation Ready</p>
            <p className="text-sm">Connected to Windows Brain & Ubuntu Muscle</p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-4 ${msg.type === MessageType.USER ? 'flex-row-reverse' : ''}`}>
            
            {/* Avatar */}
            <div className={`w-8 h-8 md:w-10 md:h-10 rounded-full flex items-center justify-center shrink-0 border shadow-sm ${
              msg.type === MessageType.AGENT 
                ? 'bg-bio-50 border-bio-200 text-bio-600' 
                : 'bg-slate-100 border-slate-200 text-slate-600'
            }`}>
              {msg.type === MessageType.AGENT ? <Cpu className="w-5 h-5" /> : <User className="w-5 h-5" />}
            </div>

            {/* Content Bubble */}
            <div className={`flex-1 max-w-3xl ${msg.type === MessageType.USER ? 'text-right' : ''}`}>
              <div className={`inline-block text-sm md:text-base ${
                msg.type === MessageType.USER 
                  ? 'bg-slate-100 text-slate-800 px-4 py-2.5 rounded-2xl rounded-tr-sm' 
                  : 'w-full'
              }`}>
                {msg.type === MessageType.USER ? msg.content : (
                  <div className="space-y-4">
                    {/* Thinking Process */}
                    {msg.agentState?.thoughts && msg.agentState.thoughts.length > 0 && (
                       <ThinkingProcess thoughts={msg.agentState.thoughts} />
                    )}

                    {/* Agent Text Response */}
                    {msg.content && <p className="text-slate-700 leading-relaxed">{msg.content}</p>}

                    {/* Code Block */}
                    {msg.agentState?.generatedCode && (
                      <div className="rounded-lg border border-slate-200 overflow-hidden shadow-sm mt-3 bg-white">
                        <div className="flex items-center justify-between px-3 py-2 bg-slate-50 border-b border-slate-200">
                          <span className="text-xs font-mono font-medium text-slate-500 uppercase">
                            {msg.agentState.generatedCode.language}
                          </span>
                          <div className="flex gap-2">
                             <button 
                               className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-200 rounded transition-colors"
                             >
                               Modify
                             </button>
                             {msg.agentState.executionStatus === 'idle' && (
                               <button 
                                 onClick={() => onRunScript(msg.id)}
                                 className="flex items-center gap-1 px-3 py-1 text-xs font-medium bg-bio-600 text-white hover:bg-bio-700 rounded shadow-sm transition-all active:scale-95"
                               >
                                 <Play className="w-3 h-3" /> Run on Muscle
                               </button>
                             )}
                          </div>
                        </div>
                        <div className="p-4 bg-[#f8f9fa] overflow-x-auto">
                          <pre className="text-xs md:text-sm font-mono text-slate-800 leading-relaxed">
                            {msg.agentState.generatedCode.content}
                          </pre>
                        </div>
                      </div>
                    )}

                    {/* Execution Output */}
                    {(msg.agentState?.executionStatus === 'running' || msg.agentState?.executionStatus === 'completed') && msg.agentState?.logs && (
                      <TerminalOutput logs={msg.agentState.logs} />
                    )}

                    {/* Result Visualization */}
                    {msg.agentState?.result && (
                      <ResultChart data={msg.agentState.result.data} />
                    )}
                  </div>
                )}
              </div>
              <div className="mt-1 text-[10px] text-slate-400 px-1">
                {msg.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        <div ref={scrollRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t border-slate-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isProcessing}
            placeholder={isProcessing ? "Agent is working..." : "Ask Bio-Agent to process data..."}
            className="w-full pl-5 pr-12 py-3.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-bio-500/20 focus:border-bio-500 transition-all shadow-inner text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <button 
            type="submit" 
            disabled={!input.trim() || isProcessing}
            className="absolute right-2 top-2 p-1.5 bg-bio-600 text-white rounded-lg hover:bg-bio-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors shadow-md"
          >
            {isProcessing ? (
              <div className="w-5 h-5 flex items-center justify-center">
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              </div>
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </form>
        <p className="text-center text-[10px] text-slate-400 mt-2">
          Local-IA BioStation accesses Z: drive directly. No cloud data transfer.
        </p>
      </div>
    </div>
  );
};

export default ChatInterface;