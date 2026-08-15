import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Search, Sparkles, Send, ArrowUpRight, BookOpen } from 'lucide-react';
import { api, type AskRadarResponse } from '../services/api';
import type { Story } from '../types';

interface AskRadarModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectStory?: (story: Story) => void;
}

export const AskRadarModal: React.FC<AskRadarModalProps> = ({
  isOpen,
  onClose,
  onSelectStory,
}) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AskRadarResponse | null>(null);

  const sampleQueries = [
    'Reasoning model architectures',
    'Agent SDK & MCP tool updates',
    'On-device local inference hardware',
    'Open-weights releases',
  ];

  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      const res = await api.askRadar(searchQuery.trim(), 4);
      setResult(res);
    } catch (e) {
      console.error('Ask Radar failed:', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/80 backdrop-blur-md"
          />

          <motion.div
            initial={{ y: '100%', opacity: 0.5 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: '100%', opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 280 }}
            className="relative w-full max-w-lg bg-surface border border-white/10 rounded-t-3xl sm:rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh] z-10"
          >
            {/* Top Bar */}
            <div className="p-5 border-b border-white/5 flex items-center justify-between bg-gradient-to-r from-electric/10 to-transparent">
              <div className="flex items-center space-x-2.5">
                <div className="w-9 h-9 rounded-xl bg-electric/10 border border-electric/30 flex items-center justify-center text-electric">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-xs font-mono tracking-widest text-electric uppercase">
                    RAG Intelligence Search
                  </span>
                  <h2 className="text-base font-bold text-white tracking-tight">
                    Ask RADAR
                  </h2>
                </div>
              </div>

              <button
                onClick={onClose}
                className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-400 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Query Input */}
            <div className="p-5 border-b border-white/5 bg-white/[0.01]">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSearch(query);
                }}
                className="relative flex items-center"
              >
                <Search className="absolute left-3.5 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask anything across first-party AI signals..."
                  className="w-full pl-10 pr-12 py-3 bg-surface-card border border-white/10 rounded-2xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-electric transition-colors"
                  autoFocus
                />
                <button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="absolute right-2 p-2 rounded-xl bg-electric text-black disabled:opacity-40 hover:bg-electric-lime transition-all"
                >
                  <Send className="w-3.5 h-3.5" />
                </button>
              </form>

              {/* Sample Queries */}
              {!result && (
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {sampleQueries.map((sq, i) => (
                    <button
                      key={i}
                      onClick={() => {
                        setQuery(sq);
                        handleSearch(sq);
                      }}
                      className="px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-[10px] font-mono text-gray-300 transition-colors border border-white/5"
                    >
                      {sq}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Results Area */}
            <div className="p-5 space-y-5 overflow-y-auto flex-1">
              {loading ? (
                <div className="py-12 flex flex-col items-center justify-center space-y-3">
                  <div className="w-8 h-8 rounded-full border-2 border-electric border-t-transparent animate-spin" />
                  <p className="text-xs font-mono text-gray-400">Querying intelligence corpus & citing reports...</p>
                </div>
              ) : result ? (
                <div className="space-y-4">
                  {/* Synthesized Answer */}
                  <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/5 space-y-2">
                    <div className="flex items-center space-x-1.5 text-xs font-mono text-electric">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span className="font-semibold uppercase tracking-wider">Synthesized Intelligence</span>
                    </div>
                    <p className="text-xs text-gray-200 whitespace-pre-line leading-relaxed">
                      {result.answer}
                    </p>
                  </div>

                  {/* Key Takeaways */}
                  <div className="space-y-2">
                    <h3 className="text-xs font-mono text-gray-400 uppercase tracking-wider">
                      Strategic Takeaways
                    </h3>
                    <div className="space-y-1.5">
                      {result.key_takeaways.map((t, idx) => (
                        <div key={idx} className="flex items-start space-x-2 text-xs text-gray-300">
                          <span className="text-electric">•</span>
                          <span>{t}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Cited Intelligence Signals */}
                  <div className="space-y-2">
                    <h3 className="text-xs font-mono text-gray-400 uppercase tracking-wider flex items-center justify-between">
                      <span>Cited Intelligence Sources</span>
                      <span className="text-electric">{result.cited_stories.length} references</span>
                    </h3>

                    <div className="space-y-2">
                      {result.cited_stories.map((story) => (
                        <div
                          key={story.id}
                          className="p-3 rounded-xl bg-surface-card border border-white/5 hover:border-electric/30 transition-all cursor-pointer group"
                          onClick={() => {
                            if (onSelectStory) {
                              onSelectStory(story);
                              onClose();
                            }
                          }}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-[10px] font-mono text-electric font-medium">
                              {story.source_name || 'Lab Report'}
                            </span>
                            <span className="text-[10px] font-mono text-gray-500">
                              Score {story.rank_score?.toFixed(1) || story.importance_score.toFixed(1)}
                            </span>
                          </div>
                          <h4 className="text-xs font-semibold text-white group-hover:text-electric transition-colors flex items-center justify-between">
                            <span>{story.headline || story.title}</span>
                            <ArrowUpRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity ml-1 shrink-0" />
                          </h4>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-10 text-gray-500 text-xs">
                  <BookOpen className="w-8 h-8 mx-auto mb-2 opacity-40 text-electric" />
                  Ask any question to synthesize answers directly from first-party publications.
                </div>
              )}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
