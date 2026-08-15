import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Moon, Sparkles, ArrowUpRight, Copy, Check } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import type { Story } from '../types';

interface OvernightModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectStory?: (story: Story) => void;
}

export const OvernightModal: React.FC<OvernightModalProps> = ({
  isOpen,
  onClose,
  onSelectStory,
}) => {
  const [copied, setCopied] = React.useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['overnightDispatch'],
    queryFn: () => api.getOvernightDispatch(48),
    enabled: isOpen,
  });

  const handleCopy = () => {
    if (!data) return;
    const text = `🌙 CLIVE • WHAT CHANGED OVERNIGHT (${data.period})\n\n${data.executive_summary}\n\nTop Developments:\n${data.key_developments
      .map((d) => `• [${d.company}] ${d.headline}\n  Impact: ${d.impact}`)
      .join('\n\n')}\n\nvia CLIVE AI Radar`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
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
            {/* Header */}
            <div className="p-5 border-b border-white/5 flex items-center justify-between bg-gradient-to-r from-electric/10 to-transparent">
              <div className="flex items-center space-x-2.5">
                <div className="w-9 h-9 rounded-xl bg-electric/10 border border-electric/30 flex items-center justify-center text-electric">
                  <Moon className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-mono tracking-widest text-electric uppercase">
                      Morning Briefing
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-white/10 text-[9px] font-mono text-gray-400">
                      {data?.period || '48h'}
                    </span>
                  </div>
                  <h2 className="text-base font-bold text-white tracking-tight">
                    What Changed Overnight?
                  </h2>
                </div>
              </div>

              <div className="flex items-center space-x-1.5">
                <button
                  onClick={handleCopy}
                  className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 transition-colors"
                  title="Copy Executive Brief"
                >
                  {copied ? <Check className="w-4 h-4 text-electric" /> : <Copy className="w-4 h-4" />}
                </button>
                <button
                  onClick={onClose}
                  className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-400 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Content Area */}
            <div className="p-5 space-y-5 overflow-y-auto flex-1">
              {isLoading ? (
                <div className="py-12 flex flex-col items-center justify-center space-y-3">
                  <div className="w-8 h-8 rounded-full border-2 border-electric border-t-transparent animate-spin" />
                  <p className="text-xs font-mono text-gray-400">Synthesizing overnight AI intelligence...</p>
                </div>
              ) : data ? (
                <>
                  {/* Executive Overview */}
                  <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/5 space-y-2">
                    <div className="flex items-center space-x-1.5 text-xs font-mono text-electric">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span className="font-semibold uppercase tracking-wider">Executive Synthesis</span>
                    </div>
                    <p className="text-xs text-gray-200 leading-relaxed">
                      {data.executive_summary}
                    </p>
                  </div>

                  {/* Key Breakthroughs */}
                  <div className="space-y-2.5">
                    <h3 className="text-xs font-mono text-gray-400 uppercase tracking-wider flex items-center justify-between">
                      <span>Key Strategic Movements</span>
                      <span className="text-electric">{data.total_signals_detected} signals</span>
                    </h3>

                    <div className="space-y-2.5">
                      {data.key_developments.map((dev, idx) => (
                        <div
                          key={idx}
                          className="p-3.5 rounded-xl bg-surface-card border border-white/5 hover:border-electric/30 transition-all cursor-pointer group"
                          onClick={() => {
                            const found = data.stories.find((s) => s.headline === dev.headline || s.title === dev.headline);
                            if (found && onSelectStory) {
                              onSelectStory(found);
                              onClose();
                            }
                          }}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="px-2 py-0.5 rounded bg-electric/10 text-electric text-[10px] font-mono font-medium">
                              {dev.company}
                            </span>
                            <span className="text-[10px] font-mono text-gray-500">
                              Imp {dev.importance.toFixed(1)}
                            </span>
                          </div>
                          <h4 className="text-xs font-semibold text-white group-hover:text-electric transition-colors mb-1.5 flex items-center justify-between">
                            <span>{dev.headline}</span>
                            <ArrowUpRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity ml-1 shrink-0" />
                          </h4>
                          <p className="text-[11px] text-gray-400 leading-normal">
                            {dev.impact}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <p className="text-xs text-gray-400 text-center py-6">No overnight reports available.</p>
              )}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
