import React from 'react';

interface MetricGaugeProps {
  label: string;
  value: number;
  max?: number;
  size?: 'sm' | 'md';
  color?: 'electric' | 'cyan' | 'yellow' | 'red';
}

export const MetricGauge: React.FC<MetricGaugeProps> = ({
  label,
  value,
  max = 100,
  size = 'md',
  color = 'electric',
}) => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  const colorStyles = {
    electric: {
      text: 'text-electric',
      border: 'border-electric/30',
      bg: 'bg-electric',
      glow: 'shadow-[0_0_10px_rgba(16,231,96,0.3)]',
    },
    cyan: {
      text: 'text-signal-cyan',
      border: 'border-signal-cyan/30',
      bg: 'bg-signal-cyan',
      glow: 'shadow-[0_0_10px_rgba(13,240,160,0.3)]',
    },
    yellow: {
      text: 'text-signal-yellow',
      border: 'border-signal-yellow/30',
      bg: 'bg-signal-yellow',
      glow: 'shadow-[0_0_10px_rgba(250,204,21,0.3)]',
    },
    red: {
      text: 'text-signal-red',
      border: 'border-signal-red/30',
      bg: 'bg-signal-red',
      glow: 'shadow-[0_0_10px_rgba(244,63,94,0.3)]',
    },
  }[color];

  return (
    <div className="flex flex-col items-center justify-center p-2 rounded-xl bg-surface-light/40 border border-white/5">
      <div className="flex items-baseline space-x-0.5 font-mono font-bold">
        <span className={`${size === 'sm' ? 'text-sm' : 'text-base'} ${colorStyles.text}`}>
          {Math.round(value)}
        </span>
        <span className="text-[10px] text-gray-500 font-normal">/100</span>
      </div>
      <div className="w-full bg-surface-border rounded-full h-1 mt-1 overflow-hidden">
        <div
          className={`h-full rounded-full ${colorStyles.bg} ${colorStyles.glow} transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-[10px] uppercase font-mono tracking-wider text-gray-400 mt-1">
        {label}
      </span>
    </div>
  );
};
