import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ExternalLink, Bookmark, Sparkles, Building2, Cpu, Tag, Share2 } from 'lucide-react';
import type { Story } from '../types';
import { MetricGauge } from './MetricGauge';
import { ShareCardModal } from './ShareCardModal';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';

interface StoryDetailModalProps {
  story: Story | null;
  isOpen: boolean;
  onClose: () => void;
}

export const StoryDetailModal: React.FC<StoryDetailModalProps> = ({
  story,
  isOpen,
  onClose,
}) => {
  const queryClient = useQueryClient();
  const [showShareCard, setShowShareCard] = useState(false);

  const saveMutation = useMutation({
    mutationFn: ({ storyId, isSaved }: { storyId: number; isSaved: boolean }) =>
      api.interactWithStory(storyId, isSaved ? 'unsave' : 'save'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['radarDeck'] });
      queryClient.invalidateQueries({ queryKey: ['forYouFeed'] });
      queryClient.invalidateQueries({ queryKey: ['savedFeed'] });
      queryClient.invalidateQueries({ queryKey: ['trendingFeed'] });
      queryClient.invalidateQueries({ queryKey: ['radarStats'] });
    },
  });

  const handleOpenSource = () => {
    if (!story) return;
    api.openStorySource(story.id);
    window.open(story.original_url || story.canonical_url, '_blank', 'noopener,noreferrer');
  };

  if (!story) return null;

  const timeAgo = (dateStr: string) => {
    const diffHours = Math.round((Date.now() - new Date(dateStr).getTime()) / (1000 * 60 * 60));
    if (diffHours < 1) return 'Just now';
    if (diffHours === 1) return '1h ago';
    if (diffHours < 24) return `${diffHours}h ago`;
    const days = Math.floor(diffHours / 24);
    return `${days}d ago`;
  };

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={onClose}
              className="fixed inset-0 bg-black/80 backdrop-blur-md"
            />

            {/* Modal Sheet */}
            <motion.div
              initial={{ y: '100%', opacity: 0.5 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: '100%', opacity: 0 }}
              transition={{ type: 'spring', damping: 25, stiffness: 260 }}
              className="relative w-full max-w-lg bg-surface border border-white/10 rounded-t-3xl sm:rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] z-10"
            >
              {/* Header Bar */}
              <div className="flex items-center justify-between px-5 py-4 border-b border-white/5 bg-surface-card/60">
                <div className="flex items-center space-x-2">
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-electric/15 text-electric border border-electric/30">
                    {story.category}
                  </span>
                  {story.is_breaking && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-signal-red/20 text-signal-red border border-signal-red/30 animate-pulse">
                      BREAKING
                    </span>
                  )}
                </div>
                <div className="flex items-center space-x-1.5">
                  <button
                    onClick={() => setShowShareCard(true)}
                    className="p-2 rounded-full text-gray-300 hover:text-white hover:bg-white/10 transition-colors"
                    title="Export Share Card"
                  >
                    <Share2 className="w-4 h-4 text-electric" />
                  </button>
                  <button
                    onClick={() => saveMutation.mutate({ storyId: story.id, isSaved: story.is_saved })}
                    className={`p-2 rounded-full transition-colors ${
                      story.is_saved
                        ? 'text-electric bg-electric/10'
                        : 'text-gray-400 hover:text-white hover:bg-white/10'
                    }`}
                    title={story.is_saved ? 'Saved' : 'Bookmark story'}
                  >
                    <Bookmark className={`w-4 h-4 ${story.is_saved ? 'fill-electric' : ''}`} />
                  </button>
                  <button
                    onClick={onClose}
                    className="p-2 rounded-full text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Modal Scroll Body */}
              <div className="overflow-y-auto px-5 py-4 space-y-5">
                {/* Source & Date metadata */}
                <div className="flex items-center justify-between text-xs text-gray-400 font-mono">
                  <span className="text-gray-300 font-medium">{story.source_name || 'AI Lab'}</span>
                  <span>{timeAgo(story.published_at)}</span>
                </div>

                {/* Title / Headline */}
                <div>
                  <h2 className="text-xl font-extrabold text-white leading-tight font-sans">
                    {story.headline || story.title}
                  </h2>
                  {story.headline && story.title !== story.headline && (
                    <p className="text-xs text-gray-400 mt-1 font-mono">{story.title}</p>
                  )}
                </div>

                {/* Metric Gauges */}
                <div className="grid grid-cols-3 gap-2">
                  <MetricGauge
                    label="Importance"
                    value={story.importance_score}
                    color={story.importance_score > 85 ? 'electric' : 'cyan'}
                  />
                  <MetricGauge
                    label="Novelty"
                    value={story.novelty_score}
                    color={story.novelty_score > 80 ? 'electric' : 'yellow'}
                  />
                  <MetricGauge
                    label="Technical"
                    value={story.technical_score}
                    color="cyan"
                  />
                </div>

                {/* Summary Section */}
                <div className="p-4 rounded-2xl bg-surface-card border border-white/5 space-y-2">
                  <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-gray-400">
                    Executive Brief
                  </h3>
                  <p className="text-sm text-gray-200 leading-relaxed font-sans">
                    {story.summary || story.extracted_content || 'No executive summary available.'}
                  </p>
                </div>

                {/* Why It Matters */}
                {story.why_it_matters && story.why_it_matters.length > 0 && (
                  <div className="p-4 rounded-2xl bg-electric-dark/30 border border-electric/25 space-y-2.5">
                    <div className="flex items-center space-x-1.5 text-xs font-mono font-bold text-electric uppercase tracking-wider">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Why It Matters</span>
                    </div>
                    <ul className="space-y-2">
                      {story.why_it_matters.map((point, index) => (
                        <li key={index} className="flex items-start space-x-2 text-xs text-gray-200 leading-relaxed font-sans">
                          <span className="text-electric font-mono font-bold mt-0.5">•</span>
                          <span>{point}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Tags & Taxonomy Grid */}
                <div className="space-y-3 pt-2">
                  {story.companies && story.companies.length > 0 && (
                    <div>
                      <div className="flex items-center space-x-1 text-[11px] font-mono text-gray-400 mb-1.5">
                        <Building2 className="w-3 h-3 text-cyan-400" />
                        <span>ORGANIZATIONS</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {story.companies.map((comp, i) => (
                          <span key={i} className="px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-light border border-white/5 text-gray-200">
                            {comp}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {story.technologies && story.technologies.length > 0 && (
                    <div>
                      <div className="flex items-center space-x-1 text-[11px] font-mono text-gray-400 mb-1.5">
                        <Cpu className="w-3 h-3 text-electric" />
                        <span>ARCHITECTURES & TECH</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {story.technologies.map((tech, i) => (
                          <span key={i} className="px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-light border border-white/5 text-gray-200">
                            {tech}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {story.topics && story.topics.length > 0 && (
                    <div>
                      <div className="flex items-center space-x-1 text-[11px] font-mono text-gray-400 mb-1.5">
                        <Tag className="w-3 h-3 text-yellow-400" />
                        <span>THEMES & TOPICS</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {story.topics.map((top, i) => (
                          <span key={i} className="px-2 py-0.5 rounded-md text-[11px] font-mono bg-white/5 text-gray-300">
                            #{top}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Bottom Action Dock */}
              <div className="p-4 border-t border-white/5 bg-surface-card/80 flex items-center justify-between gap-3">
                <button
                  onClick={() => setShowShareCard(true)}
                  className="px-4 py-3 rounded-2xl bg-surface-light border border-white/10 text-xs font-mono font-semibold text-white hover:border-electric transition-colors flex items-center space-x-1.5"
                >
                  <Share2 className="w-3.5 h-3.5 text-electric" />
                  <span>Share Card</span>
                </button>

                <button
                  onClick={handleOpenSource}
                  className="flex-1 py-3 px-4 rounded-2xl bg-electric hover:bg-electric-lime text-black font-bold text-xs font-mono uppercase tracking-wider flex items-center justify-center space-x-2 transition-all shadow-[0_0_20px_rgba(16,231,96,0.3)] active:scale-95"
                >
                  <span>Read Original Publication</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Share Card Modal */}
      <ShareCardModal
        story={story}
        isOpen={showShareCard}
        onClose={() => setShowShareCard(false)}
      />
    </>
  );
};
