import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Sparkles, Filter, AlertCircle, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import { StoryCard } from '../components/StoryCard';
import { StoryDetailModal } from '../components/StoryDetailModal';
import type { Story } from '../types';

const CATEGORIES = [
  'All',
  'AI Agents',
  'LLMs',
  'Multimodal',
  'Hardware',
  'Research',
  'Developer Tools',
  'Open Source',
];

export const ForYouPage: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStory, setSelectedStory] = useState<Story | null>(null);

  const {
    data,
    isLoading,
    isError,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['forYouFeed', selectedCategory, searchQuery],
    queryFn: () =>
      api.getForYouFeed({
        category: selectedCategory === 'All' ? undefined : selectedCategory,
        q: searchQuery.trim() || undefined,
        limit: 30,
      }),
  });

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-background h-full">
      {/* Search & Category Filter Header */}
      <div className="p-4 border-b border-white/5 space-y-3 glass-panel shrink-0">
        {/* Search Bar */}
        <div className="relative flex items-center">
          <Search className="absolute left-3.5 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search AI signals, models, papers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-surface-card border border-white/10 rounded-2xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-electric transition-colors"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 text-xs text-gray-400 hover:text-white"
            >
              Clear
            </button>
          )}
        </div>

        {/* Category Horizontal Slider */}
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 no-scrollbar touch-pan-x">
          <Filter className="w-3.5 h-3.5 text-gray-400 shrink-0 ml-1 mr-0.5" />
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-full text-xs font-mono whitespace-nowrap transition-all ${
                selectedCategory === cat
                  ? 'bg-electric text-black font-bold shadow-[0_0_12px_rgba(0,240,255,0.3)]'
                  : 'bg-surface-light border border-white/5 text-gray-300 hover:text-white hover:border-white/20'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Stories Feed Area with Touch Momentum Scroll */}
      <div className="flex-1 scroll-touch-area p-4 space-y-3.5">
        {isLoading ? (
          <div className="py-20 flex flex-col items-center justify-center space-y-3">
            <div className="w-8 h-8 rounded-full border-2 border-electric border-t-transparent animate-spin" />
            <p className="text-xs font-mono text-gray-400">Loading personalized intelligence stream...</p>
          </div>
        ) : isError ? (
          <div className="p-6 rounded-2xl bg-signal-red/10 border border-signal-red/30 text-center space-y-3">
            <AlertCircle className="w-8 h-8 text-signal-red mx-auto" />
            <h3 className="text-sm font-bold text-white">Feed Ingestion Error</h3>
            <p className="text-xs text-gray-300">Unable to connect to intelligence database.</p>
            <button
              onClick={() => refetch()}
              className="px-4 py-2 rounded-xl bg-surface border border-white/10 text-xs font-mono text-white hover:border-electric"
            >
              Retry Connection
            </button>
          </div>
        ) : data && data.stories.length > 0 ? (
          <>
            <div className="flex items-center justify-between px-1 text-[11px] font-mono text-gray-400">
              <span className="flex items-center space-x-1">
                <Sparkles className="w-3 h-3 text-electric" />
                <span>Personalized Ranked Stream</span>
              </span>
              <div className="flex items-center space-x-2">
                <span>{data.total} signals</span>
                {isFetching && <RefreshCw className="w-3 h-3 animate-spin text-electric" />}
              </div>
            </div>

            <div className="space-y-3 pb-8">
              <AnimatePresence>
                {data.stories.map((story: Story) => (
                  <motion.div
                    key={story.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <StoryCard
                      story={story}
                      onSelectStory={(st) => setSelectedStory(st)}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </>
        ) : (
          <div className="py-20 text-center space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-surface border border-white/10 mx-auto flex items-center justify-center text-gray-500">
              <Search className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-bold text-white">No Signals Found</h3>
            <p className="text-xs text-gray-400 max-w-xs mx-auto">
              No matching intelligence reports for the selected filters.
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
