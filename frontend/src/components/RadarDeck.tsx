import React, { useState } from 'react';
import { motion, useMotionValue, useTransform, AnimatePresence } from 'framer-motion';
import { Check, X, Bookmark, ExternalLink, Sparkles, Flame, RefreshCw, Layers } from 'lucide-react';
import type { Story } from '../types';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { MetricGauge } from './MetricGauge';

interface RadarDeckProps {
  stories: Story[];
  onOpenDetail: (story: Story) => void;
  onRefresh: () => void;
  isLoading?: boolean;
}

interface SwipeCardProps {
  story: Story;
  index: number;
  isTop: boolean;
  onSwipe: (direction: 'right' | 'left') => void;
  onOpenDetail: (story: Story) => void;
  onSaveToggle: (story: Story) => void;
  onOpenSource: (story: Story) => void;
}

const SwipeCard: React.FC<SwipeCardProps> = ({
  story,
  index,
  isTop,
  onSwipe,
  onOpenDetail,
  onSaveToggle,
  onOpenSource,
}) => {
  const x = useMotionValue(0);
  const rotate = useTransform(x, [-200, 200], [-18, 18]);
  const opacity = useTransform(x, [-200, -150, 0, 150, 200], [0.6, 0.9, 1, 0.9, 0.6]);

  // Stamp feedback opacities
  const rightStampOpacity = useTransform(x, [15, 80], [0, 1]);
  const leftStampOpacity = useTransform(x, [-15, -80], [0, 1]);

  const handleDragEnd = (_: any, info: any) => {
    const threshold = 60;
    const velocityThreshold = 180;

    if (info.offset.x > threshold || info.velocity.x > velocityThreshold) {
      onSwipe('right');
    } else if (info.offset.x < -threshold || info.velocity.x < -velocityThreshold) {
      onSwipe('left');
    }
  };

  const timeAgo = (dateStr: string) => {
    const diffHours = Math.round((Date.now() - new Date(dateStr).getTime()) / (1000 * 60 * 60));
    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  return (
    <motion.div
      style={{
        x: isTop ? x : 0,
        rotate: isTop ? rotate : 0,
        opacity: isTop ? opacity : 1 - index * 0.15,
        scale: 1 - index * 0.04,
        y: index * 8,
        zIndex: 10 - index,
        touchAction: 'none',
      }}
      drag={isTop ? 'x' : false}
      dragConstraints={{ left: 0, right: 0 }}
      dragElastic={0.65}
      onDragEnd={isTop ? handleDragEnd : undefined}
      initial={{ scale: 0.9, opacity: 0, y: 20 }}
      animate={{
        scale: 1 - index * 0.04,
        opacity: 1 - index * 0.15,
        y: index * 8,
      }}
      exit={{
        x: x.get() < 0 ? -400 : 400,
        opacity: 0,
        scale: 0.85,
        transition: { duration: 0.22 },
      }}
      className="absolute inset-0 w-full h-full rounded-3xl glass-card border border-white/10 p-4 sm:p-5 flex flex-col justify-between shadow-2xl cursor-grab active:cursor-grabbing select-none touch-none"
    >
      {/* Swipe Feedback Stamp Overlays */}
      {isTop && (
        <>
          <motion.div
            style={{ opacity: rightStampOpacity }}
            className="absolute top-5 left-5 z-30 pointer-events-none px-3.5 py-1 rounded-xl border-2 border-electric bg-surface/95 text-electric font-mono font-black text-xs sm:text-sm tracking-widest uppercase shadow-[0_0_20px_rgba(0,240,255,0.5)] transform -rotate-12"
          >
            INTERESTED
          </motion.div>
          <motion.div
            style={{ opacity: leftStampOpacity }}
            className="absolute top-5 right-5 z-30 pointer-events-none px-3.5 py-1 rounded-xl border-2 border-signal-red bg-surface/95 text-signal-red font-mono font-black text-xs sm:text-sm tracking-widest uppercase shadow-[0_0_20px_rgba(255,51,102,0.5)] transform rotate-12"
          >
            SKIP
          </motion.div>
        </>
      )}

      {/* Card Header */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-1.5">
            <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded-full bg-electric/15 text-electric border border-electric/30">
              {story.category}
            </span>
            {story.is_breaking && (
              <span className="flex items-center space-x-1 text-[9px] font-mono font-extrabold px-1.5 py-0.5 rounded-full bg-signal-red/20 text-signal-red border border-signal-red/30 animate-pulse">
                <Flame className="w-2.5 h-2.5" />
                <span>BREAKING</span>
              </span>
            )}
          </div>
          <span className="text-[11px] font-mono text-gray-400">
            {timeAgo(story.published_at)}
          </span>
        </div>

        {/* Source info */}
        <div className="flex items-center space-x-1.5 text-[11px] text-gray-400 font-mono mb-1.5 truncate">
          <span className="text-gray-300 font-semibold">{story.source_name || 'AI Lab'}</span>
          {story.companies && story.companies.length > 0 && (
            <>
              <span>•</span>
              <span className="text-electric font-medium truncate">{story.companies.join(', ')}</span>
            </>
          )}
        </div>

        {/* Headline */}
        <h2
          onClick={() => onOpenDetail(story)}
          className="text-base sm:text-lg font-extrabold text-white leading-snug hover:text-electric transition-colors cursor-pointer line-clamp-2"
        >
          {story.headline || story.title}
        </h2>
      </div>

      {/* Card Center: Summary & Why it matters preview */}
      <div
        onClick={() => onOpenDetail(story)}
        className="my-2 space-y-2 cursor-pointer flex-1 flex flex-col justify-center"
      >
        <p className="text-xs sm:text-sm text-gray-300 line-clamp-3 leading-relaxed font-sans">
          {story.summary || story.title}
        </p>

        {story.why_it_matters && story.why_it_matters.length > 0 && (
          <div className="p-2.5 rounded-xl bg-electric-dark/25 border border-electric/20 space-y-1">
            <div className="flex items-center space-x-1 text-[10px] font-mono font-bold text-electric uppercase tracking-wider">
              <Sparkles className="w-3 h-3" />
              <span>Why It Matters</span>
            </div>
            <p className="text-xs text-gray-200 line-clamp-2 leading-relaxed">
              {story.why_it_matters[0]}
            </p>
          </div>
        )}
      </div>

      {/* Card Bottom: Gauges & Tap to read hint */}
      <div className="shrink-0 pt-1">
        <div className="grid grid-cols-3 gap-1.5 mb-2.5">
          <MetricGauge
            label="Importance"
            value={story.importance_score}
            size="sm"
            color={story.importance_score > 85 ? 'electric' : 'cyan'}
          />
          <MetricGauge
            label="Novelty"
            value={story.novelty_score}
            size="sm"
            color="yellow"
          />
          <MetricGauge
            label="Technical"
            value={story.technical_score}
            size="sm"
            color="cyan"
          />
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-white/10 text-xs font-mono text-gray-400">
          <button
            onClick={() => onOpenDetail(story)}
            className="text-gray-400 hover:text-electric transition-colors flex items-center space-x-1 text-[11px]"
          >
            <span>Tap for full brief</span>
          </button>
          <div className="flex items-center space-x-1.5">
            <button
              onClick={() => onOpenSource(story)}
              className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
              title="Open publication"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => onSaveToggle(story)}
              className={`p-1.5 rounded-lg transition-colors ${
                story.is_saved
                  ? 'text-electric bg-electric/10'
                  : 'text-gray-400 hover:text-white hover:bg-white/10'
              }`}
              title={story.is_saved ? 'Saved' : 'Bookmark'}
            >
              <Bookmark className={`w-3.5 h-3.5 ${story.is_saved ? 'fill-electric' : ''}`} />
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export const RadarDeck: React.FC<RadarDeckProps> = ({
  stories,
  onOpenDetail,
  onRefresh,
}) => {
  const queryClient = useQueryClient();
  const [deck, setDeck] = useState<Story[]>(stories);

  // Sync state with incoming stories
  React.useEffect(() => {
    setDeck(stories);
  }, [stories]);

  const interactMutation = useMutation({
    mutationFn: ({
      storyId,
      type,
    }: {
      storyId: number;
      type: 'swipe_right' | 'swipe_left' | 'save' | 'unsave' | 'open_source';
    }) => api.recordInteraction(storyId, type),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['forYouFeed'] });
      queryClient.invalidateQueries({ queryKey: ['preferences'] });
      queryClient.invalidateQueries({ queryKey: ['radarStats'] });
      queryClient.invalidateQueries({ queryKey: ['savedFeed'] });
    },
  });

  const handleSwipe = (direction: 'right' | 'left') => {
    if (deck.length === 0) return;
    const topStory = deck[0];
    const interactionType = direction === 'right' ? 'swipe_right' : 'swipe_left';
    
    interactMutation.mutate({ storyId: topStory.id, type: interactionType });
    setDeck((prev) => prev.slice(1));
  };

  const handleSave = (story: Story) => {
    interactMutation.mutate({
      storyId: story.id,
      type: story.is_saved ? 'unsave' : 'save',
    });
    setDeck((prev) =>
      prev.map((s) => (s.id === story.id ? { ...s, is_saved: !s.is_saved } : s))
    );
  };

  const handleOpenSource = (story: Story) => {
    interactMutation.mutate({ storyId: story.id, type: 'open_source' });
    window.open(story.original_url || story.canonical_url, '_blank', 'noopener,noreferrer');
  };

  return (
    <div className="relative w-full flex-1 flex flex-col items-center justify-between select-none min-h-0">
      {/* Swipe Deck Viewport */}
      <div className="relative w-full max-w-sm flex-1 min-h-[380px] max-h-[500px] my-1">
        <AnimatePresence>
          {deck.length > 0 ? (
            deck
              .slice(0, 3)
              .map((story, index) => (
                <SwipeCard
                  key={story.id}
                  story={story}
                  index={index}
                  isTop={index === 0}
                  onSwipe={handleSwipe}
                  onOpenDetail={onOpenDetail}
                  onSaveToggle={handleSave}
                  onOpenSource={handleOpenSource}
                />
              ))
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="w-full h-full rounded-3xl glass-card border border-white/10 p-6 flex flex-col items-center justify-center text-center space-y-4"
            >
              <div className="w-14 h-14 rounded-full bg-electric-dark/40 border border-electric/30 flex items-center justify-center text-electric">
                <Layers className="w-7 h-7" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white font-mono">Radar Clear</h3>
                <p className="text-xs text-gray-400 mt-1 max-w-xs leading-relaxed">
                  You've reviewed all current radar signals. Refresh to reload candidate signals.
                </p>
              </div>
              <button
                onClick={onRefresh}
                className="flex items-center space-x-2 px-4 py-2 rounded-full bg-electric hover:bg-electric-lime text-black font-mono font-bold text-xs shadow-[0_0_20px_rgba(0,240,255,0.3)] transition-all active:scale-95"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Reload Signals</span>
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Interactive Swipe Action Control Bar */}
      <div className="w-full max-w-xs flex items-center justify-between py-2 px-4 shrink-0">
        {/* Skip / Swipe Left */}
        <button
          onClick={() => handleSwipe('left')}
          disabled={deck.length === 0}
          className="w-11 h-11 rounded-full bg-surface-light border border-white/10 hover:border-signal-red/50 text-gray-400 hover:text-signal-red flex items-center justify-center shadow-lg transition-all active:scale-90 disabled:opacity-40"
          title="Skip (Swipe Left)"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Save / Bookmark */}
        <button
          onClick={() => deck.length > 0 && handleSave(deck[0])}
          disabled={deck.length === 0}
          className={`w-10 h-10 rounded-full border transition-all active:scale-90 flex items-center justify-center shadow-lg disabled:opacity-40 ${
            deck[0]?.is_saved
              ? 'bg-electric/20 border-electric text-electric'
              : 'bg-surface-light border-white/10 text-gray-400 hover:text-white'
          }`}
          title="Save Bookmark"
        >
          <Bookmark className={`w-4 h-4 ${deck[0]?.is_saved ? 'fill-electric' : ''}`} />
        </button>

        {/* Read Source */}
        <button
          onClick={() => deck.length > 0 && handleOpenSource(deck[0])}
          disabled={deck.length === 0}
          className="w-10 h-10 rounded-full bg-surface-light border border-white/10 hover:border-white/30 text-gray-400 hover:text-white flex items-center justify-center shadow-lg transition-all active:scale-90 disabled:opacity-40"
          title="Read Original Publication"
        >
          <ExternalLink className="w-4 h-4" />
        </button>

        {/* Interested / Swipe Right */}
        <button
          onClick={() => handleSwipe('right')}
          disabled={deck.length === 0}
          className="w-11 h-11 rounded-full bg-electric/15 border border-electric/40 text-electric hover:bg-electric hover:text-black flex items-center justify-center shadow-[0_0_20px_rgba(0,240,255,0.2)] transition-all active:scale-90 disabled:opacity-40"
          title="Interested (Swipe Right)"
        >
          <Check className="w-5 h-5" />
        </button>
      </div>

      {/* Swipe gesture helper caption */}
      <p className="text-[10px] font-mono text-gray-500 text-center tracking-wide pb-1 shrink-0">
        Swipe Left to Skip • Swipe Right for Interested • Tap for Detail
      </p>
    </div>
  );
};
