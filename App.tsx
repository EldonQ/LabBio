import React, { useState, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import { WORK_DIRS, MOCK_SCRIPT, MOCK_ANALYSIS_DATA } from './constants';
import { ChatMessage, MessageType, AgentMessageState, ExecutionLog } from './types';

const App: React.FC = () => {
  const [currentDir, setCurrentDir] = useState(WORK_DIRS[0].path);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // Helper to add simulated logs
  const addLog = useCallback((msgId: string, message: string, level: 'info' | 'success' | 'warn' | 'error' = 'info') => {
    const timestamp = new Date().toISOString().split('T')[1].slice(0, 8);
    setMessages(prev => prev.map(msg => {
      if (msg.id === msgId && msg.agentState) {
        return {
          ...msg,
          agentState: {
            ...msg.agentState,
            logs: [...msg.agentState.logs, { timestamp, level, message }]
          }
        };
      }
      return msg;
    }));
  }, []);

  // Simulator for the "Run" action
  const handleRunScript = async (msgId: string) => {
    // Set status to running
    setMessages(prev => prev.map(msg => 
      msg.id === msgId && msg.agentState 
        ? { ...msg, agentState: { ...msg.agentState, executionStatus: 'running' } } 
        : msg
    ));

    // Simulate async execution logs coming from Ubuntu
    const logs = [
      { t: 500, m: "Connection established to Ubuntu Muscle (192.168.1.50)..." },
      { t: 1200, m: "Environment activated: obi3" },
      { t: 2000, m: "Scanning Z:/BioData/2023_11 for pattern 'GZ*'" },
      { t: 3500, m: "Aligning paired ends for sample JC1 (Threads: 16)..." },
      { t: 5000, m: "Alignment complete: 145,203 reads processed" },
      { t: 5500, m: "Filtering low quality reads (score > 0.8)..." },
      { t: 7000, m: "Generating statistics..." },
      { t: 8000, m: "Batch processing completed successfully. Output saved." }
    ];

    for (const log of logs) {
      await new Promise(r => setTimeout(r, log.t - (logs[logs.indexOf(log)-1]?.t || 0)));
      addLog(msgId, log.m, log.m.includes('success') ? 'success' : 'info');
    }

    // Mark completed and show result chart
    setMessages(prev => prev.map(msg => 
      msg.id === msgId && msg.agentState 
        ? { 
            ...msg, 
            agentState: { 
              ...msg.agentState, 
              executionStatus: 'completed',
              result: {
                title: "Results",
                type: "bar",
                data: MOCK_ANALYSIS_DATA
              }
            } 
          } 
        : msg
    ));
  };

  const handleSendMessage = async (text: string) => {
    const newMsg: ChatMessage = {
      id: Date.now().toString(),
      type: MessageType.USER,
      content: text,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newMsg]);
    setIsProcessing(true);

    // Initial Agent Placeholder
    const agentMsgId = (Date.now() + 1).toString();
    const initialAgentMsg: ChatMessage = {
      id: agentMsgId,
      type: MessageType.AGENT,
      content: "", // Start empty, fill later
      timestamp: new Date(),
      agentState: {
        isThinking: true,
        thoughts: ["Initializing Planner Agent..."],
        executionStatus: 'idle',
        logs: []
      }
    };
    setMessages(prev => [...prev, initialAgentMsg]);

    // Simulate Planner Steps (Section 3.2.1)
    const thoughts = [
      "Analyzing user intent: 'Bioinformatics Pipeline Request'",
      `Scanning directory ${currentDir} for FASTQ files...`,
      "Found 20 matching files (GZ24...)",
      "Consulting RAG Memory: Retrieved 'OBITools3 Standard Protocol' (Score: 0.92)",
      "Checking resource availability on Muscle Node: 256GB RAM available",
      "Generating execution plan: Import -> Align -> Filter",
      "Drafting shell script..."
    ];

    for (let i = 0; i < thoughts.length; i++) {
      await new Promise(r => setTimeout(r, 1200));
      setMessages(prev => prev.map(msg => {
        if (msg.id === agentMsgId && msg.agentState) {
          // Remove previous '...' thought if exists
          const currentThoughts = msg.agentState.thoughts.filter(t => !t.includes('...'));
          return {
            ...msg,
            agentState: {
              ...msg.agentState,
              thoughts: [...currentThoughts, thoughts[i]]
            }
          };
        }
        return msg;
      }));
    }

    // Finalize Thinking and Present Code
    setMessages(prev => prev.map(msg => {
      if (msg.id === agentMsgId && msg.agentState) {
        return {
          ...msg,
          content: "I've generated an OBITools3 processing script based on the files found in the Z: drive. I've optimized it for the Ubuntu node's memory capacity. Please review and run it.",
          agentState: {
            ...msg.agentState,
            isThinking: false,
            generatedCode: {
              language: 'bash',
              content: MOCK_SCRIPT
            }
          }
        };
      }
      return msg;
    }));

    setIsProcessing(false);
  };

  return (
    <div className="flex h-screen w-full overflow-hidden bg-slate-50">
      <Sidebar 
        currentDir={currentDir} 
        onDirChange={setCurrentDir} 
      />
      <main className="flex-1 flex flex-col h-full min-w-0 bg-white">
        <ChatInterface 
          messages={messages}
          isProcessing={isProcessing}
          onSendMessage={handleSendMessage}
          onRunScript={handleRunScript}
        />
      </main>
    </div>
  );
};

export default App;