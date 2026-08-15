import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Share2, Copy, Check, Radio, Sparkles } from 'lucide-react';
import type { Story } from '../types';

interface ShareCardModalProps {
  story: Story | null;
  isOpen: boolean;
  onClose: () => void;
}

export const ShareCardModal: React.FC<ShareCardModalProps> = ({
  story,
  isOpen,
  onClose,
}) => {
  const [copied, setCopied] = useState(false);

  if (!story) return null;

  const whyItMattersText = story.why_it_matters && story.why_it_matters.length > 0
    ? story.why_it_matters[0]
    : story.summary || '';

  const shareText = `📡 CLIVE • AI RADAR\n\n⚡ ${story.headline || story.title}\n\n🎯 Why It Matters:\n${whyItMattersText}\n\n📊 Signal Metrics: Importance ${story.importance_score.toFixed(1)}/100 | Novelty ${story.novelty_score.toFixed(1)}/100\n🔗 Read First-Party: ${story.canonical_url}\n\n#AI #Intelligence #CLIVERadar`;

  const handleCopy = () => {
    navigator.clipboard.writeText(shareText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2200);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/85 backdrop-blur-md"
          />

          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="relative w-full max-w-sm bg-surface border border-white/15 rounded-3xl shadow-2xl overflow-hidden flex flex-col z-10"
          >
            {/* Top Bar */}
            <div className="p-4 border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center space-x-2 text-xs font-mono text-gray-300">
                <Share2 className="w-4 h-4 text-electric" />
                <span>Export Intelligence Card</span>
              </div>
              <button
                onClick={onClose}
                className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* The Visual Share Card Preview */}
            <div className="p-5">
              <div className="p-5 rounded-2xl bg-gradient-to-b from-[#141E28] to-[#0B1015] border border-electric/40 shadow-[0_0_30px_rgba(0,240,255,0.15)] space-y-4">
                {/* Brand Header */}
                <div className="flex items-center justify-between pb-3 border-b border-white/10">
                  <div className="flex items-center space-x-1.5 text-[10px] font-mono tracking-widest text-electric uppercase">
                    <Radio className="w-3 h-3 animate-pulse" />
                    <span>CLIVE • AI Radar</span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-electric/15 text-electric text-[10px] font-mono font-bold">
                    SCORE {story.rank_score?.toFixed(1) || story.importance_score.toFixed(1)}
                  </span>
                </div>

                {/* Main Headline */}
                <div>
                  <span className="text-[10px] font-mono text-gray-400 uppercase tracking-wider block mb-1">
                    {story.source_name || story.category}
                  </span>
                  <h3 className="text-sm font-bold text-white leading-snug">
                    {story.headline || story.title}
                  </h3>
                </div>

                {/* Why It Matters */}
                <div className="p-3 rounded-xl bg-white/[0.04] border border-white/5 space-y-1">
                  <div className="flex items-center space-x-1 text-[10px] font-mono text-electric font-semibold">
                    <Sparkles className="w-3 h-3" />
                    <span>WHY IT MATTERS</span>
                  </div>
                  <p className="text-[11px] text-gray-300 leading-relaxed">
                    {whyItMattersText}
                  </p>
                </div>

                {/* Metrics Bar */}
                <div className="grid grid-cols-3 gap-2 pt-1 text-center font-mono">
                  <div className="p-1.5 rounded-lg bg-black/40 border border-white/5">
                    <div className="text-[9px] text-gray-500">IMPORTANCE</div>
                    <div className="text-xs font-bold text-electric">{story.importance_score.toFixed(0)}</div>
                  </div>
                  <div className="p-1.5 rounded-lg bg-black/40 border border-white/5">
                    <div className="text-[9px] text-gray-500">NOVELTY</div>
                    <div className="text-xs font-bold text-cyan-400">{story.novelty_score.toFixed(0)}</div>
                  </div>
                  <div className="p-1.5 rounded-lg bg-black/40 border border-white/5">
                    <div className="text-[9px] text-gray-500">TECHNICAL</div>
                    <div className="text-xs font-bold text-purple-400">{story.technical_score.toFixed(0)}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Actions */}
            <div className="p-4 pt-0">
              <button
                onClick={handleCopy}
                className="w-full py-3 rounded-2xl bg-electric hover:bg-electric-lime text-black font-semibold text-xs flex items-center justify-center space-x-2 transition-all shadow-[0_0_20px_rgba(16,231,96,0.3)]"
              >
                {copied ? (
                  <>
                    <Check className="w-4 h-4" />
                    <span>Copied to Clipboard!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    <span>Copy Card Text for Social Share</span>
                  </>
                )}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
