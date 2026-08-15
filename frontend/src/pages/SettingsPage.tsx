import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Settings as SettingsIcon, Sliders, Cpu, Shield, RotateCcw, Check, Sparkles } from 'lucide-react';
import { api } from '../services/api';
import type { TopicWeight, UserSetting } from '../types';

export const SettingsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [selectedModel, setSelectedModel] = useState('gemini-3.5-flash-lite');
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Load user topic preference weights
  const { data: preferences, isLoading: prefsLoading } = useQuery<TopicWeight[]>({
    queryKey: ['preferences'],
    queryFn: () => api.getPreferences('default_user'),
  });

  // Load user settings
  const { data: settings } = useQuery<UserSetting>({
    queryKey: ['userSettings'],
    queryFn: () => api.getUserSettings('default_user'),
  });

  useEffect(() => {
    if (settings) {
      if (settings.gemini_model) {
        setSelectedModel(settings.gemini_model);
      }
    }
  }, [settings]);

  // Update Topic Weight
  const updateWeightMutation = useMutation({
    mutationFn: ({ topic, weight }: { topic: string; weight: number }) =>
      api.updateTopicWeight(topic, weight, 'default_user'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['preferences'] });
      queryClient.invalidateQueries({ queryKey: ['forYouFeed'] });
      queryClient.invalidateQueries({ queryKey: ['radarDeck'] });
    },
  });

  // Reset Weights
  const resetMutation = useMutation({
    mutationFn: () => api.resetPreferences('default_user'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['preferences'] });
      queryClient.invalidateQueries({ queryKey: ['forYouFeed'] });
      queryClient.invalidateQueries({ queryKey: ['radarDeck'] });
    },
  });

  // Update API Key & Model
  const updateSettingsMutation = useMutation({
    mutationFn: (data: { gemini_api_key?: string; gemini_model?: string }) =>
      api.updateUserSettings(data, 'default_user'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['userSettings'] });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2500);
    },
  });

  const handleSaveAISettings = (e: React.FormEvent) => {
    e.preventDefault();
    updateSettingsMutation.mutate({
      gemini_api_key: apiKeyInput.trim() || undefined,
      gemini_model: selectedModel,
    });
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-background h-full">
      {/* Header */}
      <div className="p-4 border-b border-white/5 glass-panel flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-2">
          <SettingsIcon className="w-5 h-5 text-electric" />
          <h2 className="text-base font-bold text-white font-mono">Personalization & Engine</h2>
        </div>
        <span className="text-[11px] font-mono text-gray-400">Settings</span>
      </div>

      <div className="flex-1 scroll-touch-area p-4 space-y-6 pb-28">
        {/* Section 1: Topic Interest Matrix */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1.5 text-xs font-mono font-bold text-gray-300">
              <Sliders className="w-4 h-4 text-electric" />
              <span className="uppercase tracking-wider">Topic Interest Matrix</span>
            </div>
            <button
              onClick={() => resetMutation.mutate()}
              disabled={resetMutation.isPending}
              className="flex items-center space-x-1 text-[11px] font-mono text-gray-400 hover:text-signal-red transition-colors disabled:opacity-50"
              title="Reset weights"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset All</span>
            </button>
          </div>

          <p className="text-xs text-gray-400">
            Swiping right/left dynamically shifts these weights. Adjust sliders manually to fine-tune your radar feed.
          </p>

          <div className="p-4 rounded-2xl bg-surface-card border border-white/5 space-y-4">
            {prefsLoading ? (
              <div className="py-6 text-center text-xs font-mono text-gray-400">Loading topic matrix...</div>
            ) : preferences && preferences.length > 0 ? (
              preferences.slice(0, 10).map((item: TopicWeight) => (
                <div key={item.topic} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-white font-medium">{item.topic}</span>
                    <span className="text-electric font-bold">{item.weight.toFixed(2)}x</span>
                  </div>
                  <input
                    type="range"
                    min="0.2"
                    max="3.0"
                    step="0.05"
                    value={item.weight}
                    onChange={(e) =>
                      updateWeightMutation.mutate({
                        topic: item.topic,
                        weight: parseFloat(e.target.value),
                      })
                    }
                    className="w-full h-1.5 bg-surface-light rounded-lg appearance-none cursor-pointer accent-electric"
                  />
                  <div className="flex items-center justify-between text-[10px] font-mono text-gray-500">
                    <span>Pos: {item.positive_count}</span>
                    <span>Neg: {item.negative_count}</span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-xs text-gray-400 text-center py-4">No topic preferences recorded yet.</p>
            )}
          </div>
        </div>

        {/* Section 2: Gemini AI Engine Configuration */}
        <div className="space-y-3">
          <div className="flex items-center space-x-1.5 text-xs font-mono font-bold text-gray-300">
            <Cpu className="w-4 h-4 text-cyan-400" />
            <span className="uppercase tracking-wider">Gemini AI Configuration</span>
          </div>

          <div className="p-4 rounded-2xl bg-surface-card border border-white/5 space-y-4">
            <form onSubmit={handleSaveAISettings} className="space-y-3.5">
              <div>
                <label className="block text-xs font-mono text-gray-300 mb-1.5">
                  Gemini Model (Default: gemini-3.5-flash-lite)
                </label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full px-3 py-2 bg-surface-light border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-electric"
                >
                  <option value="gemini-3.5-flash-lite">gemini-3.5-flash-lite (Fast & Efficient)</option>
                  <option value="gemini-3.6-flash">gemini-3.6-flash (Deep Reasoning & Synthesis)</option>
                  <option value="gemini-2.5-flash">gemini-2.5-flash (Standard)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono text-gray-300 mb-1.5 flex items-center justify-between">
                  <span>Custom Gemini API Key</span>
                  <span className="text-[10px] text-gray-500">Optional override</span>
                </label>
                <div className="relative flex items-center">
                  <Shield className="absolute left-3 w-4 h-4 text-gray-400" />
                  <input
                    type="password"
                    placeholder="Enter custom API key to override server default"
                    value={apiKeyInput}
                    onChange={(e) => setApiKeyInput(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 bg-surface-light border border-white/10 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-electric"
                  />
                </div>
                {settings?.has_custom_api_key && (
                  <p className="text-[10px] font-mono text-electric mt-1 flex items-center space-x-1">
                    <Check className="w-3 h-3" />
                    <span>Custom key active</span>
                  </p>
                )}
              </div>

              <button
                type="submit"
                disabled={updateSettingsMutation.isPending}
                className="w-full py-2.5 rounded-xl bg-electric hover:bg-electric-lime text-black font-mono font-bold text-xs flex items-center justify-center space-x-1.5 transition-all disabled:opacity-50"
              >
                {saveSuccess ? (
                  <>
                    <Check className="w-4 h-4" />
                    <span>Settings Saved!</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Save Engine Configuration</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Section 3: Ranking Weights Explainer */}
        <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 space-y-2 font-mono text-xs text-gray-400">
          <div className="text-white font-bold mb-1">CLIVE Multi-Factor Score:</div>
          <div>• 40% Importance (AI Practitioner Significance)</div>
          <div>• 30% Personal Relevance (Dynamic Topic Weights)</div>
          <div>• 20% Recency (Discrete step decay)</div>
          <div>• 10% Novelty (Architectural & Tech Depth)</div>
          <div>+ Breaking Alert Boost (+15 pts)</div>
        </div>
      </div>
    </div>
  );
};
