import React from 'react';
import { Bookmark, ExternalLink, Flame } from 'lucide-react';
import type { Story } from '../types';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';

interface StoryCardProps {
  story: Story;
  onSelect?: (story: Story) => void;
  onSelectStory?: (story: Story) => void;
  showRankScore?: boolean;
}

export const StoryCard: React.FC<StoryCardProps> = ({
  story,
  onSelect,
  onSelectStory,
  showRankScore = false,
}) => {
  const queryClient = useQueryClient();

  const handleCardClick = () => {
    if (onSelect) onSelect(story);
    if (onSelectStory) onSelectStory(story);
  };

  const saveMutation = useMutation({
    mutationFn: ({ storyId, isSaved }: { storyId: number; isSaved: boolean }) =>
      api.interactWithStory(storyId, isSaved ? 'unsave' : 'save'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['forYouFeed'] });
      queryClient.invalidateQueries({ queryKey: ['savedFeed'] });
      queryClient.invalidateQueries({ queryKey: ['trendingFeed'] });
      queryClient.invalidateQueries({ queryKey: ['radarDeck'] });
      queryClient.invalidateQueries({ queryKey: ['radarStats'] });
    },
  });

  const handleOpenSource = (e: React.MouseEvent) => {
    e.stopPropagation();
    api.openStorySource(story.id);
    window.open(story.original_url || story.canonical_url, '_blank', 'noopener,noreferrer');
  };

  const handleSaveToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    saveMutation.mutate({ storyId: story.id, isSaved: story.is_saved });
  };

  const timeAgo = (dateStr: string) => {
    const diffHours = Math.round((Date.now() - new Date(dateStr).getTime()) / (1000 * 60 * 60));
    if (diffHours < 1) return 'Just now';
    if (diffHours === 1) return '1h ago';
    if (diffHours < 24) return `${diffHours}h ago`;
    const days = Math.floor(diffHours / 24);
    return `${days}d ago`;
  };

  return (
    <div
      onClick={handleCardClick}
      className="glass-card glass-card-hover rounded-2xl p-4 cursor-pointer relative overflow-hidden group select-none"
    >
      {/* Accent top border highlight */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-electric/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

      {/* Card Header: Category & Score & Date */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-1.5">
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-electric/10 text-electric border border-electric/20">
            {story.category}
          </span>
          {story.is_breaking && (
            <span className="px-1.5 py-0.5 rounded-full text-[9px] font-mono font-bold bg-signal-red/20 text-signal-red border border-signal-red/30 flex items-center space-x-0.5">
              <Flame className="w-2.5 h-2.5" />
              <span>BREAKING</span>
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2 text-[11px] font-mono text-gray-400">
          {showRankScore && story.rank_score !== undefined && (
            <span className="text-electric font-bold">
              {story.rank_score.toFixed(1)} pt
            </span>
          )}
          <span>{timeAgo(story.published_at)}</span>
        </div>
      </div>

      {/* Story Headline */}
      <h3 className="text-sm font-bold text-white leading-snug group-hover:text-electric transition-colors mb-1.5">
        {story.headline || story.title}
      </h3>

      {/* Summary Snippet */}
      <p className="text-xs text-gray-400 line-clamp-2 leading-relaxed mb-3">
        {story.summary || story.extracted_content || story.title}
      </p>

      {/* Card Footer: Source / Tags & Action Buttons */}
      <div className="flex items-center justify-between pt-2 border-t border-white/5 text-xs text-gray-400">
        <span className="font-mono text-[11px] text-gray-300 font-medium truncate max-w-[170px]">
          {story.source_name || 'AI Lab'}
        </span>

        <div className="flex items-center space-x-1">
          <button
            onClick={handleSaveToggle}
            className={`p-1.5 rounded-lg transition-colors ${
              story.is_saved
                ? 'text-electric bg-electric/10'
                : 'text-gray-400 hover:text-white hover:bg-white/10'
            }`}
            title={story.is_saved ? 'Saved' : 'Bookmark story'}
          >
            <Bookmark className={`w-3.5 h-3.5 ${story.is_saved ? 'fill-electric' : ''}`} />
          </button>

          <button
            onClick={handleOpenSource}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
            title="Open original source publication"
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
