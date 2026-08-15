import React, { useState } from 'react';
import { Radio, RefreshCw, Moon, Sparkles } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { OvernightModal } from './OvernightModal';
import { AskRadarModal } from './AskRadarModal';
import type { Story } from '../types';

interface HeaderProps {
  isScanning?: boolean;
  onSelectStory?: (story: Story) => void;
}

export const Header: React.FC<HeaderProps> = ({ isScanning, onSelectStory }) => {
  const [showOvernight, setShowOvernight] = useState(false);
  const [showAskRadar, setShowAskRadar] = useState(false);
  const queryClient = useQueryClient();

  const scanMutation = useMutation({
    mutationFn: api.triggerScan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['radarDeck'] });
      queryClient.invalidateQueries({ queryKey: ['forYouFeed'] });
      queryClient.invalidateQueries({ queryKey: ['trendingFeed'] });
      queryClient.invalidateQueries({ queryKey: ['radarStats'] });
      queryClient.invalidateQueries({ queryKey: ['sources'] });
    },
  });

  return (
    <>
      <header className="sticky top-0 z-40 w-full glass-panel border-b border-white/5 px-3 py-2.5 select-none">
        <div className="flex items-center justify-between">
          {/* Brand */}
          <div className="flex items-center space-x-2">
            <div className="relative flex items-center justify-center w-7 h-7 rounded-lg bg-electric-dark/80 border border-electric/40 text-electric">
              <Radio className="w-3.5 h-3.5 animate-pulse text-electric" />
              <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-electric animate-ping" />
            </div>
            <div>
              <div className="flex items-center space-x-1">
                <h1 className="text-base font-extrabold tracking-wider text-white font-mono">
                  CLIVE
                </h1>
                <span className="text-[9px] uppercase font-mono px-1 py-0.2 rounded bg-electric/15 text-electric font-semibold border border-electric/25">
                  RADAR
                </span>
              </div>
            </div>
          </div>

          {/* Quick Intelligence Tool Actions */}
          <div className="flex items-center space-x-1.5">
            {/* Ask RADAR RAG */}
            <button
              onClick={() => setShowAskRadar(true)}
              className="flex items-center space-x-1 px-2.5 py-1.5 rounded-full text-[11px] font-mono font-medium bg-surface-card hover:bg-white/10 border border-white/10 text-gray-200 hover:text-electric transition-all"
              title="Ask RADAR semantic intelligence search"
            >
              <Sparkles className="w-3 h-3 text-electric" />
              <span>Ask</span>
            </button>

            {/* Overnight Morning Briefing */}
            <button
              onClick={() => setShowOvernight(true)}
              className="flex items-center space-x-1 px-2.5 py-1.5 rounded-full text-[11px] font-mono font-medium bg-surface-card hover:bg-white/10 border border-white/10 text-gray-200 hover:text-cyan-400 transition-all"
              title="What Changed Overnight briefing"
            >
              <Moon className="w-3 h-3 text-cyan-400" />
              <span>Overnight</span>
            </button>

            {/* Manual Scan */}
            <button
              onClick={() => scanMutation.mutate()}
              disabled={scanMutation.isPending || isScanning}
              className="p-1.5 rounded-full text-[11px] font-mono bg-surface-card hover:bg-white/10 border border-white/10 text-gray-300 hover:text-white transition-all disabled:opacity-50"
              title="Trigger background scan"
            >
              <RefreshCw
                className={`w-3.5 h-3.5 text-electric ${
                  scanMutation.isPending || isScanning ? 'animate-spin' : ''
                }`}
              />
            </button>
          </div>
        </div>
      </header>

      {/* Unique Feature Modals */}
      <OvernightModal
        isOpen={showOvernight}
        onClose={() => setShowOvernight(false)}
        onSelectStory={onSelectStory}
      />

      <AskRadarModal
        isOpen={showAskRadar}
        onClose={() => setShowAskRadar(false)}
        onSelectStory={onSelectStory}
      />
    </>
  );
};
