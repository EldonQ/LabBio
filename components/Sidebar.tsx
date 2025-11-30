import React, { useEffect, useState } from 'react';
import { Activity, Server, Folder, Cpu, HardDrive, Wifi, WifiOff } from 'lucide-react';
import { ResourceStats, NodeStatus, FileNode } from '../types';
import { WORK_DIRS } from '../constants';

interface SidebarProps {
  currentDir: string;
  onDirChange: (dir: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ currentDir, onDirChange }) => {
  const [muscleStats, setMuscleStats] = useState<ResourceStats>({
    cpu: 12,
    memory: 45,
    memoryTotal: 256,
  });

  const [brainStatus, setBrainStatus] = useState<NodeStatus>(NodeStatus.ONLINE);
  const [muscleStatus, setMuscleStatus] = useState<NodeStatus>(NodeStatus.ONLINE);

  // Simulate telemetry simulation
  useEffect(() => {
    const interval = setInterval(() => {
      setMuscleStats(prev => ({
        ...prev,
        cpu: Math.max(5, Math.min(100, prev.cpu + (Math.random() * 20 - 10))),
        memory: Math.max(40, Math.min(250, prev.memory + (Math.random() * 5 - 2))),
      }));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: NodeStatus) => {
    switch (status) {
      case NodeStatus.ONLINE: return 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]';
      case NodeStatus.BUSY: return 'bg-yellow-500 animate-pulse';
      case NodeStatus.OFFLINE: return 'bg-red-500';
      default: return 'bg-gray-400';
    }
  };

  return (
    <aside className="w-80 bg-slate-900 text-slate-100 flex flex-col border-r border-slate-800 shadow-2xl z-20">
      {/* Header */}
      <div className="p-6 border-b border-slate-700 bg-slate-950">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-bio-400 to-bio-600 flex items-center justify-center">
             <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-tight">Local-IA Bio</h1>
            <p className="text-xs text-slate-400 font-mono">Ver 2.1.0 (Stable)</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-8 scrollbar-thin">
        
        {/* Connection Status */}
        <section>
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Wifi className="w-3 h-3" /> Node Connectivity
          </h3>
          
          <div className="space-y-3">
            {/* Windows Brain */}
            <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-sky-400" />
                  <span className="text-sm font-medium">The Brain (Win)</span>
                </div>
                <div className={`w-2.5 h-2.5 rounded-full ${getStatusColor(brainStatus)}`} />
              </div>
              <div className="text-xs text-slate-400 pl-6">
                WSL2 • RTX 4090 • API: Active
              </div>
            </div>

            {/* Ubuntu Muscle */}
            <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Server className="w-4 h-4 text-orange-400" />
                  <span className="text-sm font-medium">The Muscle (Ubu)</span>
                </div>
                <div className={`w-2.5 h-2.5 rounded-full ${getStatusColor(muscleStatus)}`} />
              </div>
              <div className="text-xs text-slate-400 pl-6">
                FastAPI • P2200 • RAM: 256GB
              </div>
            </div>
          </div>
        </section>

        {/* Resources */}
        <section>
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Activity className="w-3 h-3" /> Real-time Telemetry
          </h3>
          
          <div className="space-y-4 font-mono text-xs">
            <div>
              <div className="flex justify-between mb-1 text-slate-300">
                <span>Muscle CPU</span>
                <span className={muscleStats.cpu > 80 ? 'text-red-400' : 'text-bio-400'}>
                  {muscleStats.cpu.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-1.5 overflow-hidden">
                <div 
                  className={`h-full transition-all duration-500 ${muscleStats.cpu > 80 ? 'bg-red-500' : 'bg-bio-500'}`}
                  style={{ width: `${muscleStats.cpu}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1 text-slate-300">
                <span>Muscle RAM</span>
                <span>{muscleStats.memory.toFixed(0)} / {muscleStats.memoryTotal} GB</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-1.5 overflow-hidden">
                <div 
                  className="h-full bg-purple-500 transition-all duration-500"
                  style={{ width: `${(muscleStats.memory / muscleStats.memoryTotal) * 100}%` }}
                />
              </div>
              <div className="mt-1 text-[10px] text-slate-500 text-right">
                High-mem node active
              </div>
            </div>
          </div>
        </section>

        {/* Directory Selector */}
        <section>
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4 flex items-center gap-2">
            <HardDrive className="w-3 h-3" /> Workspace (Z: Drive)
          </h3>
          <div className="space-y-1">
            {WORK_DIRS.map((dir) => (
              <button
                key={dir.id}
                onClick={() => onDirChange(dir.path)}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors ${
                  currentDir === dir.path 
                    ? 'bg-bio-600/20 text-bio-300 border border-bio-600/30' 
                    : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                }`}
              >
                <Folder className="w-4 h-4" />
                <span className="truncate">{dir.name}</span>
              </button>
            ))}
          </div>
        </section>
      </div>
      
      <div className="p-4 border-t border-slate-800 text-xs text-slate-500 text-center">
        System Status: <span className="text-green-500">Normal</span>
      </div>
    </aside>
  );
};

export default Sidebar;