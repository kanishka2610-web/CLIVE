import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Radio, Zap } from 'lucide-react';

interface SplashScreenProps {
  onComplete: () => void;
  minDisplayTimeMs?: number;
}

export const SplashScreen: React.FC<SplashScreenProps> = ({
  onComplete,
  minDisplayTimeMs = 1200,
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  const handleDismiss = () => {
    setIsVisible(false);
    onCompleteRef.current();
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(() => {
        onCompleteRef.current();
      }, 300);
    }, minDisplayTimeMs);

    return () => clearTimeout(timer);
  }, [minDisplayTimeMs]);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 1 }}
          exit={{ opacity: 0, scale: 1.04 }}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
          onClick={handleDismiss}
          className="fixed inset-0 z-50 flex flex-col items-center justify-between p-8 bg-[#070A0F] text-white select-none overflow-hidden cursor-pointer"
        >
          {/* Top subtle badge */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-mono tracking-widest text-gray-400 uppercase"
          >
            <span className="text-white font-bold">CLIVE</span>
            <span className="text-electric">•</span>
            <span>AI Radar</span>
          </motion.div>

          {/* Center Brand Identity & Radar Pulse */}
          <div className="flex flex-col items-center space-y-6">
            <div className="relative flex items-center justify-center">
              {/* Concentric Pulse Rings */}
              <motion.div
                animate={{ scale: [1, 1.8, 2.2], opacity: [0.6, 0.2, 0] }}
                transition={{ repeat: Infinity, duration: 2.2, ease: 'easeOut' }}
                className="absolute w-24 h-24 rounded-full border border-electric/40 bg-electric/10"
              />
              <motion.div
                animate={{ scale: [1, 1.4, 1.8], opacity: [0.8, 0.3, 0] }}
                transition={{ repeat: Infinity, duration: 2.2, delay: 0.4, ease: 'easeOut' }}
                className="absolute w-24 h-24 rounded-full border border-electric/30"
              />

              {/* Main Icon Hub */}
              <motion.div
                initial={{ scale: 0.7, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: 'spring', damping: 15, stiffness: 200 }}
                className="relative w-20 h-20 rounded-2xl bg-surface border border-electric/50 flex items-center justify-center shadow-[0_0_40px_rgba(0,240,255,0.35)] z-10"
              >
                <Radio className="w-10 h-10 text-electric animate-pulse" />
                <span className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-electric shadow-[0_0_10px_#00F0FF]" />
              </motion.div>
            </div>

            {/* Title & Tagline */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="text-center space-y-1.5"
            >
              <h1 className="text-3xl font-black tracking-widest text-white font-mono flex items-center justify-center space-x-2">
                <span>CLIVE</span>
              </h1>
              <p className="text-xs text-gray-400 font-sans tracking-wide">
                Your signal in the AI noise.
              </p>
            </motion.div>
          </div>

          {/* Bottom Telemetry Status */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="flex flex-col items-center space-y-1.5"
          >
            <div className="flex items-center space-x-2 text-[11px] font-mono text-gray-400">
              <Zap className="w-3.5 h-3.5 text-electric animate-bounce" />
              <span>Locking onto first-party AI signals...</span>
            </div>
            <span className="text-[9px] font-mono text-gray-600">Tap anywhere to enter</span>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
