export interface ResourceStats {
  cpu: number;
  memory: number;
  memoryTotal: number;
  gpuTemp?: number;
}

export enum NodeStatus {
  ONLINE = 'online',
  OFFLINE = 'offline',
  BUSY = 'busy',
  ERROR = 'error'
}

export interface FileNode {
  id: string;
  name: string;
  type: 'folder' | 'file';
  path: string;
}

export enum MessageType {
  USER = 'user',
  AGENT = 'agent'
}

export interface ExecutionLog {
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'success';
  message: string;
}

export interface AnalysisResult {
  title: string;
  type: 'bar' | 'pie';
  data: Array<{ name: string; value: number }>;
}

export interface AgentMessageState {
  isThinking: boolean;
  thoughts: string[];
  generatedCode?: {
    language: string;
    content: string;
  };
  executionStatus: 'idle' | 'running' | 'completed' | 'failed';
  logs: ExecutionLog[];
  result?: AnalysisResult;
}

export interface ChatMessage {
  id: string;
  type: MessageType;
  content: string;
  agentState?: AgentMessageState;
  timestamp: Date;
}