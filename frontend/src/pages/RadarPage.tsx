import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import type { Story } from '../types';
import { RadarScanner } from '../components/RadarScanner';
import { RadarDeck } from '../components/RadarDeck';
import { StoryDetailModal } from '../components/StoryDetailModal';
import { Loader2 } from 'lucide-react';

export const RadarPage: React.FC = () => {
  const [selectedStory, setSelectedStory] = useState<Story | null>(null);

  const {
    data: deckStories = [],
    isLoading: isDeckLoading,
    refetch: refetchDeck,
    isRefetching,
  } = useQuery({
    queryKey: ['radarDeck'],
    queryFn: () => api.getRadarDeck(25),
  });

  const { data: radarStats } = useQuery({
    queryKey: ['radarStats'],
    queryFn: api.getRadarStats,
    refetchInterval: 15000,
  });

  return (
    <div className="flex-1 flex flex-col px-3 py-2 overflow-hidden justify-between h-full">
      {/* Real-time Radar Pulse Header */}
      <div className="shrink-0">
        <RadarScanner stats={radarStats} isScanning={isRefetching} />
      </div>

      {/* Swipe Cards Deck */}
      {isDeckLoading ? (
        <div className="flex-1 flex flex-col items-center justify-center space-y-3">
          <Loader2 className="w-8 h-8 text-electric animate-spin" />
          <p className="text-xs font-mono text-gray-400">Locking onto AI signals...</p>
        </div>
      ) : (
        <RadarDeck
          stories={deckStories}
          onOpenDetail={(story) => setSelectedStory(story)}
          onRefresh={() => refetchDeck()}
          isLoading={isRefetching}
        />
      )}

      {/* Story Detail Briefing Modal */}
      <StoryDetailModal
        story={selectedStory}
        isOpen={!!selectedStory}
        onClose={() => setSelectedStory(null)}
      />
    </div>
  );
};
