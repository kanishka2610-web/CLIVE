import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import type { Source } from '../types';
import {
  Rss,
  Plus,
  RefreshCw,
  Trash2,
  Loader2,
  X,
} from 'lucide-react';

export const SourcesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [newSourceName, setNewSourceName] = useState('');
  const [newSourceUrl, setNewSourceUrl] = useState('');
  const [newSourceCategory, setNewSourceCategory] = useState('Lab');
  const [newSourceType, setNewSourceType] = useState<'rss' | 'atom' | 'html'>('rss');
  const [addError, setAddError] = useState('');

  const {
    data: sources = [],
    isLoading,
    isRefetching,
  } = useQuery({
    queryKey: ['sources'],
    queryFn: api.getSources,
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
      api.updateSource(id, { is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] });
      queryClient.invalidateQueries({ queryKey: ['radarStats'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteSource(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] });
      queryClient.invalidateQueries({ queryKey: ['radarStats'] });
    },
  });

  const scanMutation = useMutation({
    mutationFn: api.triggerScan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] });
      queryClient.invalidateQueries({ queryKey: ['radarStats'] });
      queryClient.invalidateQueries({ queryKey: ['radarDeck'] });
      queryClient.invalidateQueries({ queryKey: ['forYouFeed'] });
    },
  });

  const createMutation = useMutation({
    mutationFn: () =>
      api.createSource({
        name: newSourceName.trim(),
        url: newSourceUrl.trim(),
        category: newSourceCategory,
        feed_type: newSourceType,
        is_active: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] });
      queryClient.invalidateQueries({ queryKey: ['radarStats'] });
      setIsAddModalOpen(false);
      setNewSourceName('');
      setNewSourceUrl('');
      setAddError('');
    },
    onError: (err: any) => {
      setAddError(err.response?.data?.detail || 'Failed to add source');
    },
  });

  const handleAddSource = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSourceName.trim() || !newSourceUrl.trim()) {
      setAddError('Please provide both name and URL');
      return;
    }
    createMutation.mutate();
  };

  return (
    <div className="flex-1 flex flex-col px-4 py-3 pb-28 scroll-touch-area space-y-4 h-full bg-background">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-xl font-black text-white font-mono flex items-center space-x-2">
            <span>FEED SOURCES</span>
            <Rss className="w-4 h-4 text-electric" />
          </h2>
          <p className="text-xs text-gray-400 font-sans">
            First-party AI labs, research feeds, and company engineering blogs.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => scanMutation.mutate()}
            disabled={scanMutation.isPending}
            className="p-2 rounded-xl bg-surface-light border border-white/10 hover:border-electric/30 text-gray-300 hover:text-white transition-all disabled:opacity-50"
            title="Scan all sources now"
          >
            <RefreshCw
              className={`w-4 h-4 text-electric ${
                scanMutation.isPending || isRefetching ? 'animate-spin' : ''
              }`}
            />
          </button>
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-electric hover:bg-electric-lime text-black font-mono font-bold text-xs shadow-[0_0_12px_rgba(0,240,255,0.3)] transition-all active:scale-95"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Feed</span>
          </button>
        </div>
      </div>

      {/* Sources List */}
      {isLoading ? (
        <div className="py-20 flex flex-col items-center justify-center space-y-3">
          <Loader2 className="w-8 h-8 text-electric animate-spin" />
          <p className="text-xs font-mono text-gray-400">Loading intelligence feeds...</p>
        </div>
      ) : sources.length > 0 ? (
        <div className="space-y-2.5 pb-8">
          {sources.map((source: Source) => {
            const hasError = (source.failure_count || 0) > 0;
            return (
              <div
                key={source.id}
                className="p-3.5 rounded-2xl glass-card border border-white/5 hover:border-white/15 transition-all flex flex-col space-y-2"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-2.5">
                    <div
                      className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
                        source.is_active
                          ? hasError
                            ? 'bg-signal-yellow shadow-[0_0_8px_#FACC15]'
                            : 'bg-electric shadow-[0_0_8px_#00F0FF]'
                          : 'bg-gray-600'
                      }`}
                    />
                    <div>
                      <h4 className="text-sm font-bold text-white leading-tight font-sans">
                        {source.name}
                      </h4>
                      <p className="text-[11px] text-gray-400 font-mono truncate max-w-[240px] mt-0.5">
                        {source.url}
                      </p>
                    </div>
                  </div>

                  {/* Active Toggle Switch */}
                  <div className="flex items-center space-x-2">
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={source.is_active}
                        onChange={(e) =>
                          toggleMutation.mutate({
                            id: source.id,
                            is_active: e.target.checked,
                          })
                        }
                        className="sr-only peer"
                      />
                      <div className="w-8 h-4 bg-surface-border peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-black after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-electric"></div>
                    </label>
                    <button
                      onClick={() => deleteMutation.mutate(source.id)}
                      className="p-1 rounded-lg text-gray-500 hover:text-signal-red hover:bg-white/5 transition-colors"
                      title="Delete source"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <div className="flex items-center justify-between text-[10px] font-mono text-gray-400 border-t border-white/5 pt-2 mt-1">
                  <div className="flex items-center space-x-2">
                    <span className="px-1.5 py-0.5 rounded bg-surface-light text-gray-300">
                      {source.category}
                    </span>
                    <span className="uppercase text-gray-500">{source.feed_type}</span>
                  </div>

                  {hasError && (
                    <span className="text-signal-yellow truncate max-w-[180px]">
                      Error: {source.last_error || 'Scan failed'}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="p-8 text-center glass-card rounded-2xl">
          <p className="text-sm text-gray-400">No sources configured yet.</p>
        </div>
      )}

      {/* Add Source Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="w-full max-w-md bg-surface border border-white/15 rounded-3xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-lg font-bold text-white font-mono flex items-center space-x-2">
                <Plus className="w-5 h-5 text-electric" />
                <span>Add AI Feed Source</span>
              </h3>
              <button
                onClick={() => setIsAddModalOpen(false)}
                className="p-1 rounded-lg text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAddSource} className="space-y-3.5">
              {addError && (
                <div className="p-2.5 rounded-xl bg-signal-red/20 border border-signal-red/40 text-signal-red text-xs font-mono">
                  {addError}
                </div>
              )}

              <div>
                <label className="block text-xs font-mono text-gray-300 mb-1">
                  Source Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. DeepSeek AI Research"
                  value={newSourceName}
                  onChange={(e) => setNewSourceName(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-surface-card border border-white/10 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-electric"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-gray-300 mb-1">
                  Feed Endpoint URL
                </label>
                <input
                  type="url"
                  placeholder="https://example.com/feed.xml"
                  value={newSourceUrl}
                  onChange={(e) => setNewSourceUrl(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-surface-card border border-white/10 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-electric"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-mono text-gray-300 mb-1">
                    Category
                  </label>
                  <select
                    value={newSourceCategory}
                    onChange={(e) => setNewSourceCategory(e.target.value)}
                    className="w-full px-3 py-2 bg-surface-card border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-electric"
                  >
                    <option value="Lab">Lab</option>
                    <option value="Research">Research</option>
                    <option value="Open Source">Open Source</option>
                    <option value="Industry">Industry</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-mono text-gray-300 mb-1">
                    Protocol
                  </label>
                  <select
                    value={newSourceType}
                    onChange={(e) => setNewSourceType(e.target.value as any)}
                    className="w-full px-3 py-2 bg-surface-card border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-electric"
                  >
                    <option value="rss">RSS 2.0</option>
                    <option value="atom">Atom</option>
                    <option value="html">HTML Web Scraper</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-mono text-gray-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-5 py-2 rounded-xl bg-electric hover:bg-electric-lime text-black font-mono font-bold text-xs flex items-center space-x-1.5 transition-all active:scale-95 disabled:opacity-50"
                >
                  {createMutation.isPending && (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  )}
                  <span>Save Feed</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
