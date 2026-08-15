import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Bookmark, Search } from 'lucide-react';
import { api } from '../services/api';
import { StoryCard } from '../components/StoryCard';
import { StoryDetailModal } from '../components/StoryDetailModal';
import type { Story } from '../types';

export const SavedPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStory, setSelectedStory] = useState<Story | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['savedFeed'],
    queryFn: () => api.getSavedFeed(1, 50),
  });

  const stories = data?.stories || [];
  const filteredStories = searchQuery
    ? stories.filter(
        (s: Story) =>
          s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (s.headline && s.headline.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    : stories;

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-background h-full">
      {/* Header */}
      <div className="p-4 border-b border-white/5 space-y-3 glass-panel shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Bookmark className="w-5 h-5 text-electric fill-electric" />
            <h2 className="text-base font-bold text-white font-mono">Saved Signals</h2>
          </div>
          <span className="text-xs font-mono text-gray-400">
            {filteredStories.length} bookmarked
          </span>
        </div>

        {/* Search */}
        {stories.length > 0 && (
          <div className="relative flex items-center">
            <Search className="absolute left-3.5 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search saved briefings..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-surface-card border border-white/10 rounded-2xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-electric"
            />
          </div>
        )}
      </div>

      {/* Stories list with Touch Momentum Scroll */}
      <div className="flex-1 scroll-touch-area p-4 space-y-3 pb-8">
        {isLoading ? (
          <div className="py-20 flex flex-col items-center justify-center space-y-3">
            <div className="w-8 h-8 rounded-full border-2 border-electric border-t-transparent animate-spin" />
            <p className="text-xs font-mono text-gray-400">Loading saved intelligence...</p>
          </div>
        ) : filteredStories.length > 0 ? (
          <AnimatePresence>
            {filteredStories.map((story: Story) => (
              <motion.div
                key={story.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                <StoryCard
                  story={story}
                  onSelectStory={(st) => setSelectedStory(st)}
                />
              </motion.div>
            ))}
          </AnimatePresence>
        ) : (
          <div className="py-20 text-center space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-surface border border-white/10 mx-auto flex items-center justify-center text-gray-500">
              <Bookmark className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-bold text-white">No Saved Signals</h3>
            <p className="text-xs text-gray-400 max-w-xs mx-auto">
              Tap the bookmark icon or save button on any intelligence card to store it here.
            </p>
          </div>
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
