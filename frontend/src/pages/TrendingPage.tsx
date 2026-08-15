import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Flame, TrendingUp, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';
import { StoryCard } from '../components/StoryCard';
import { StoryDetailModal } from '../components/StoryDetailModal';
import type { Story } from '../types';

export const TrendingPage: React.FC = () => {
  const [selectedStory, setSelectedStory] = useState<Story | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['trendingFeed'],
    queryFn: () => api.getTrendingFeed(1, 30),
  });

  const stories = data?.stories || [];
  const breakingStories = stories.filter((s: Story) => s.is_breaking);
  const otherTrending = stories.filter((s: Story) => !s.is_breaking);

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-background h-full">
      {/* Header */}
      <div className="p-4 border-b border-white/5 glass-panel flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-2">
          <Flame className="w-5 h-5 text-signal-red" />
          <h2 className="text-base font-bold text-white font-mono">Trending & Breaking</h2>
        </div>
        <span className="px-2 py-0.5 rounded-full bg-signal-red/10 border border-signal-red/20 text-[11px] font-mono text-signal-red font-semibold">
          High Velocity
        </span>
      </div>

      <div className="flex-1 scroll-touch-area p-4 space-y-5 pb-8">
        {isLoading ? (
          <div className="py-20 flex flex-col items-center justify-center space-y-3">
            <div className="w-8 h-8 rounded-full border-2 border-signal-red border-t-transparent animate-spin" />
            <p className="text-xs font-mono text-gray-400">Tracking high-velocity AI breakthroughs...</p>
          </div>
        ) : (
          <>
            {/* Breaking Alerts Section */}
            {breakingStories.length > 0 && (
              <div className="space-y-2.5">
                <div className="flex items-center space-x-1.5 text-xs font-mono font-bold text-signal-red">
                  <AlertTriangle className="w-3.5 h-3.5 animate-bounce" />
                  <span className="uppercase tracking-wider">Major Breaking Releases</span>
                </div>
                <div className="space-y-3">
                  {breakingStories.map((story: Story) => (
                    <StoryCard
                      key={story.id}
                      story={story}
                      onSelectStory={(st) => setSelectedStory(st)}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* High Impact Signals */}
            <div className="space-y-2.5">
              <div className="flex items-center space-x-1.5 text-xs font-mono font-bold text-gray-400">
                <TrendingUp className="w-3.5 h-3.5 text-electric" />
                <span className="uppercase tracking-wider">Top Velocity Signals</span>
              </div>
              <div className="space-y-3">
                {otherTrending.map((story: Story) => (
                  <StoryCard
                    key={story.id}
                    story={story}
                    onSelectStory={(st) => setSelectedStory(st)}
                  />
                ))}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Story Detail Modal */}
      <StoryDetailModal
        story={selectedStory}
        isOpen={Boolean(selectedStory)}
        onClose={() => setSelectedStory(null)}
      />
    </div>
  );
};
