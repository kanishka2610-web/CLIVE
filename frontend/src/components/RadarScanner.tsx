import React from 'react';
import type { RadarStats } from '../types';
import { Zap, Layers } from 'lucide-react';

interface RadarScannerProps {
  stats?: RadarStats;
  isScanning?: boolean;
}

export const RadarScanner: React.FC<RadarScannerProps> = ({
  stats,
  isScanning = false,
}) => {
  return (
    <div className="relative w-full flex items-center justify-between p-3.5 rounded-2xl bg-surface-glass border border-white/10 backdrop-blur-xl overflow-hidden select-none">
      {/* Background Animated Radar Grid */}
      <div className="flex items-center space-x-3">
        {/* Animated Radar Sweep Widget */}
        <div className="relative w-11 h-11 rounded-full border border-electric/40 bg-surface-light/80 flex items-center justify-center overflow-hidden flex-shrink-0 shadow-[0_0_15px_rgba(16,231,96,0.15)]">
          {/* Inner concentric rings */}
          <div className="absolute inset-2 rounded-full border border-electric/20" />
          <div className="absolute inset-4 rounded-full border border-electric/30" />
          
          {/* Radar Sweep Needle */}
          <div className="absolute inset-0 radar-sweep-gradient animate-radar-sweep opacity-75 origin-center" />
          
          {/* Center Blip */}
          <div className="relative w-2 h-2 rounded-full bg-electric shadow-[0_0_8px_#10E760] z-10" />
          
          {/* Random Radar Target Blip */}
          <div className="absolute top-2 right-2.5 w-1 h-1 rounded-full bg-signal-cyan animate-ping" />
        </div>

        {/* Live Status Label */}
        <div>
          <div className="flex items-center space-x-1.5 font-mono text-xs font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-electric animate-pulse shadow-[0_0_6px_#10E760]" />
            <span className="text-white tracking-wide">
              {isScanning || stats?.is_scanning ? 'RADAR ACTIVE (SCANNING)' : 'AI RADAR ACTIVE'}
            </span>
          </div>
          <p className="text-[11px] text-gray-400 font-mono mt-0.5">
            {stats ? `${stats.active_sources} Feeds Monitoring` : 'Scanning Reputable Feeds'}
          </p>
        </div>
      </div>

      {/* Mini telemetry stats badges */}
      <div className="flex items-center space-x-2 font-mono">
        <div className="text-right">
          <div className="flex items-center justify-end space-x-1 text-xs font-bold text-white">
            <Layers className="w-3 h-3 text-electric" />
            <span>{stats?.total_stories || 0}</span>
          </div>
          <span className="text-[9px] uppercase tracking-wider text-gray-400">Signals</span>
        </div>

        {stats?.breaking_stories_count ? (
          <div className="text-right border-l border-white/10 pl-2">
            <div className="flex items-center justify-end space-x-1 text-xs font-bold text-signal-red">
              <Zap className="w-3 h-3 fill-signal-red" />
              <span>{stats.breaking_stories_count}</span>
            </div>
            <span className="text-[9px] uppercase tracking-wider text-signal-red/80">Breaking</span>
          </div>
        ) : null}
      </div>
    </div>
  );
};
