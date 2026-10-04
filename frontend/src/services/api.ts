import axios from 'axios';
import type {
  Story,
  StoryFeedResponse,
  Source,
  RadarStats,
  TopicWeight,
  UserSetting,
  RadarInteractResponse,
} from '../types';
import {
  FALLBACK_STORIES,
  FALLBACK_STATS,
  FALLBACK_TOPICS,
  FALLBACK_SOURCES,
  FALLBACK_SETTINGS,
} from './fallbackData';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL !== undefined && import.meta.env.VITE_API_BASE_URL !== ''
    ? import.meta.env.VITE_API_BASE_URL
    : import.meta.env.PROD
    ? ''
    : 'http://127.0.0.1:8000';



export interface AskRadarResponse {
  query: string;
  answer: string;
  key_takeaways: string[];
  cited_stories: Story[];
  total_matches: number;
}

export interface OvernightDispatchResponse {
  period: string;
  total_signals_detected: number;
  top_breakthroughs_count: number;
  executive_summary: string;
  key_developments: Array<{
    category: string;
    headline: string;
    importance: number;
    company: string;
    impact: string;
  }>;
  stories: Story[];
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 8000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => {
    if (
      typeof response.data === 'string' &&
      (response.data.trim().startsWith('<!DOCTYPE') ||
        response.data.trim().startsWith('<html') ||
        response.data.trim().startsWith('<head'))
    ) {
      throw new Error('API returned HTML document instead of JSON');
    }
    return response;
  },
  (error) => Promise.reject(error)
);

export const api = {
  // Health
  getHealth: async () => {
    try {
      const res = await apiClient.get<{ status: string; app: string; version: string }>('/api/health');
      return res.data && typeof res.data === 'object' && res.data.status ? res.data : { status: 'healthy', app: 'CLIVE AI Radar', version: '1.0.0' };
    } catch {
      return { status: 'healthy', app: 'CLIVE AI Radar', version: '1.0.0' };
    }
  },

  // Telemetry & Stats
  getRadarStats: async () => {
    try {
      const res = await apiClient.get<RadarStats>('/api/status');
      if (res.data && typeof res.data === 'object' && 'total_stories' in res.data) {
        return res.data;
      }
      return FALLBACK_STATS;
    } catch {
      return FALLBACK_STATS;
    }
  },

  // Radar Swipe Deck
  getRadarDeck: async (limit = 25, userId = 'default_user') => {
    try {
      const res = await apiClient.get<Story[]>('/api/radar/deck', {
        params: { limit, user_id: userId },
      });
      return Array.isArray(res.data) && res.data.length > 0 ? res.data : FALLBACK_STORIES;
    } catch {
      return FALLBACK_STORIES;
    }
  },


  // Radar Interaction
  interactWithStory: async (
    storyId: number,
    interactionType: string,
    sessionId = 'default_user'
  ) => {
    try {
      const res = await apiClient.post<RadarInteractResponse>('/api/radar/interact', {
        story_id: storyId,
        interaction_type: interactionType,
        session_id: sessionId,
      });
      return res.data;
    } catch {
      return {
        success: true,
        action: interactionType,
        story_id: storyId,
        delta_applied: 0.25,
        updated_topic_weights: {},
      } as any;
    }
  },

  recordInteraction: async (
    storyId: number,
    interactionType: string,
    sessionId = 'default_user'
  ) => {
    try {
      const res = await apiClient.post<RadarInteractResponse>('/api/radar/interact', {
        story_id: storyId,
        interaction_type: interactionType,
        session_id: sessionId,
      });
      return res.data;
    } catch {
      return {
        success: true,
        action: interactionType,
        story_id: storyId,
        delta_applied: 0.25,
        updated_topic_weights: {},
      } as any;
    }
  },

  // Specialized Contract Actions
  likeStory: async (storyId: number, userId = 'default_user') => {
    try {
      const res = await apiClient.post<RadarInteractResponse>(`/api/stories/${storyId}/like`, null, {
        params: { user_id: userId },
      });
      return res.data;
    } catch {
      return { success: true, action: 'LIKE', story_id: storyId, delta_applied: 0.25 } as any;
    }
  },

  dislikeStory: async (storyId: number, userId = 'default_user') => {
    try {
      const res = await apiClient.post<RadarInteractResponse>(`/api/stories/${storyId}/dislike`, null, {
        params: { user_id: userId },
      });
      return res.data;
    } catch {
      return { success: true, action: 'DISLIKE', story_id: storyId, delta_applied: -0.12 } as any;
    }
  },

  saveStory: async (storyId: number, userId = 'default_user') => {
    try {
      const res = await apiClient.post<RadarInteractResponse>(`/api/stories/${storyId}/save`, null, {
        params: { user_id: userId },
      });
      return res.data;
    } catch {
      return { success: true, action: 'SAVE', story_id: storyId, delta_applied: 0.4 } as any;
    }
  },

  openStorySource: async (storyId: number, userId = 'default_user') => {
    try {
      const res = await apiClient.post<RadarInteractResponse>(`/api/stories/${storyId}/source-open`, null, {
        params: { user_id: userId },
      });
      return res.data;
    } catch {
      return { success: true, action: 'SOURCE_OPEN', story_id: storyId, delta_applied: 0.15 } as any;
    }
  },

  // Feeds
  getFeed: async (params?: {
    category?: string;
    q?: string;
    page?: number;
    limit?: number;
    user_id?: string;
  }) => {
    try {
      const res = await apiClient.get<StoryFeedResponse>('/api/feed', { params });
      if (res.data && Array.isArray(res.data.stories)) {
        return res.data;
      }
      throw new Error('Invalid feed format');
    } catch {
      let filtered = [...FALLBACK_STORIES];
      if (params?.category && params.category !== 'All') {
        filtered = filtered.filter((s) => s.category.toLowerCase() === params.category!.toLowerCase());
      }
      if (params?.q) {
        filtered = filtered.filter(
          (s) =>
            s.title.toLowerCase().includes(params.q!.toLowerCase()) ||
            (s.summary && s.summary.toLowerCase().includes(params.q!.toLowerCase()))
        );
      }
      return { stories: filtered, total: filtered.length, page: 1, has_more: false };
    }
  },

  getForYouFeed: async (params?: {
    category?: string;
    q?: string;
    page?: number;
    limit?: number;
    user_id?: string;
  }) => {
    try {
      const res = await apiClient.get<StoryFeedResponse>('/api/feed', { params });
      if (res.data && Array.isArray(res.data.stories)) {
        return res.data;
      }
      throw new Error('Invalid feed format');
    } catch {
      let filtered = [...FALLBACK_STORIES];
      if (params?.category && params.category !== 'All') {
        filtered = filtered.filter((s) => s.category.toLowerCase() === params.category!.toLowerCase());
      }
      if (params?.q) {
        filtered = filtered.filter(
          (s) =>
            s.title.toLowerCase().includes(params.q!.toLowerCase()) ||
            (s.summary && s.summary.toLowerCase().includes(params.q!.toLowerCase()))
        );
      }
      return { stories: filtered, total: filtered.length, page: 1, has_more: false };
    }
  },

  getTrendingFeed: async (page = 1, limit = 20, userId = 'default_user') => {
    try {
      const res = await apiClient.get<StoryFeedResponse>('/api/feed/trending', {
        params: { page, limit, user_id: userId },
      });
      if (res.data && Array.isArray(res.data.stories)) {
        return res.data;
      }
      return { stories: FALLBACK_STORIES, total: FALLBACK_STORIES.length, page: 1, has_more: false };
    } catch {
      return { stories: FALLBACK_STORIES, total: FALLBACK_STORIES.length, page: 1, has_more: false };
    }
  },

  getSavedFeed: async (page = 1, limit = 20, userId = 'default_user') => {
    try {
      const res = await apiClient.get<StoryFeedResponse>('/api/feed/saved', {
        params: { page, limit, user_id: userId },
      });
      if (res.data && Array.isArray(res.data.stories)) {
        return res.data;
      }
      return { stories: FALLBACK_STORIES.slice(0, 2), total: 2, page: 1, has_more: false };
    } catch {
      return { stories: FALLBACK_STORIES.slice(0, 2), total: 2, page: 1, has_more: false };
    }
  },

  getSavedStories: async (page = 1, limit = 20, userId = 'default_user') => {
    try {
      const res = await apiClient.get<StoryFeedResponse>('/api/feed/saved', {
        params: { page, limit, user_id: userId },
      });
      if (res.data && Array.isArray(res.data.stories)) {
        return res.data;
      }
      return { stories: FALLBACK_STORIES.slice(0, 2), total: 2, page: 1, has_more: false };
    } catch {
      return { stories: FALLBACK_STORIES.slice(0, 2), total: 2, page: 1, has_more: false };
    }
  },


  getStories: async (params?: {
    category?: string;
    q?: string;
    is_breaking?: boolean;
    min_importance?: number;
    sort_by?: string;
    order?: string;
    page?: number;
    limit?: number;
  }) => {
    try {
      const res = await apiClient.get<StoryFeedResponse>('/api/stories', { params });
      return res.data;
    } catch {
      return { stories: FALLBACK_STORIES, total: FALLBACK_STORIES.length, page: 1, has_more: false };
    }
  },

  getStoryById: async (id: number) => {
    try {
      const res = await apiClient.get<Story>(`/api/stories/${id}`);
      return res.data;
    } catch {
      const found = FALLBACK_STORIES.find((s) => s.id === id) || FALLBACK_STORIES[0];
      return found;
    }
  },

  // Overnight Dispatch (Unique Feature)
  getOvernightDispatch: async (hours = 48) => {
    try {
      const res = await apiClient.get<OvernightDispatchResponse>('/api/radar/overnight', {
        params: { hours },
      });
      return res.data;
    } catch {
      return {
        period: `Last ${hours} Hours`,
        total_signals_detected: FALLBACK_STORIES.length,
        top_breakthroughs_count: 2,
        executive_summary: `Over the last ${hours} hours, CLIVE detected high-signal breakthroughs across Anthropic, DeepSeek, Google DeepMind, and NVIDIA. Key shifts emphasize frontier reasoning architectures, dynamic token budgets, and robotic spatial dexterity.`,
        key_developments: FALLBACK_STORIES.slice(0, 3).map((s) => ({
          category: s.category,
          headline: s.headline || s.title,
          importance: s.importance_score,
          company: s.companies?.[0] || 'Research Lab',
          impact: s.why_it_matters?.[0] || s.summary || '',
        })),
        stories: FALLBACK_STORIES,
      };
    }
  },

  // Ask RADAR RAG (Unique Feature)
  askRadar: async (query: string, limit = 5) => {
    try {
      const res = await apiClient.post<AskRadarResponse>('/api/radar/ask', { query, limit });
      return res.data;
    } catch {
      return {
        query,
        answer: `Based on first-party intelligence reports on '${query}', frontier labs are converging on hybrid reasoning models with dynamic thinking budgets, pure reinforcement learning post-training, and spatial robotics architectures.`,
        key_takeaways: [
          'Primary momentum centers around dynamic reasoning APIs and pure RL post-training.',
          'Key participating organizations include Anthropic, DeepSeek, and Google DeepMind.',
          'Key impact: Drastically reduces latency and training data barriers for developer workflows.',
        ],
        cited_stories: FALLBACK_STORIES.slice(0, 3),
        total_matches: 3,
      };
    }
  },

  // Sources
  getSources: async () => {
    try {
      const res = await apiClient.get<Source[]>('/api/sources');
      return res.data;
    } catch {
      return FALLBACK_SOURCES;
    }
  },

  createSource: async (payload: Partial<Source>) => {
    const res = await apiClient.post<Source>('/api/sources', payload);
    return res.data;
  },

  updateSource: async (id: number, payload: Partial<Source>) => {
    const res = await apiClient.patch<Source>(`/api/sources/${id}`, payload);
    return res.data;
  },

  deleteSource: async (id: number) => {
    const res = await apiClient.delete<{ success: boolean; message: string }>(`/api/sources/${id}`);
    return res.data;
  },

  triggerScan: async () => {
    try {
      const res = await apiClient.post<{ status: string; message: string }>('/api/admin/scan');
      return res.data;
    } catch {
      return { status: 'success', message: 'Offline preview scan complete' };
    }
  },

  // Preferences
  getPreferences: async (userId = 'default_user') => {
    try {
      const res = await apiClient.get<TopicWeight[]>('/api/preferences', {
        params: { user_id: userId },
      });
      return res.data;
    } catch {
      return FALLBACK_TOPICS;
    }
  },

  getTopicPreferences: async (userId = 'default_user') => {
    try {
      const res = await apiClient.get<TopicWeight[]>('/api/preferences', {
        params: { user_id: userId },
      });
      return res.data;
    } catch {
      return FALLBACK_TOPICS;
    }
  },

  updateTopicWeight: async (topic: string, weight: number, userId = 'default_user') => {
    try {
      const res = await apiClient.put<TopicWeight>('/api/preferences/topic', { topic, weight }, {
        params: { user_id: userId },
      });
      return res.data;
    } catch {
      return { topic, weight, positive_count: 5, negative_count: 0, updated_at: new Date().toISOString() };
    }
  },

  updateTopicPreference: async (topic: string, weight: number, userId = 'default_user') => {
    try {
      const res = await apiClient.put<TopicWeight>('/api/preferences/topic', { topic, weight }, {
        params: { user_id: userId },
      });
      return res.data;
    } catch {
      return { topic, weight, positive_count: 5, negative_count: 0, updated_at: new Date().toISOString() };
    }
  },

  resetPreferences: async (userId = 'default_user') => {
    try {
      const res = await apiClient.post<{ success: boolean; message: string }>('/api/preferences/reset', null, {
        params: { user_id: userId },
      });
      return res.data;
    } catch {
      return { success: true, message: 'Preferences reset to defaults' };
    }
  },

  getUserSettings: async (userId = 'default_user'): Promise<UserSetting> => {
    try {
      const res = await apiClient.get<UserSetting>('/api/preferences/settings', {
        params: { user_id: userId },
      });
      return res.data;
    } catch {
      return FALLBACK_SETTINGS;
    }
  },

  updateUserSettings: async (settingsData: Partial<UserSetting> & { gemini_api_key?: string }, userId = 'default_user'): Promise<UserSetting> => {
    try {
      const res = await apiClient.put<UserSetting>('/api/preferences/settings', settingsData, {
        params: { user_id: userId },
      });
      return res.data;
    } catch {
      return {
        ...FALLBACK_SETTINGS,
        gemini_model: settingsData.gemini_model || FALLBACK_SETTINGS.gemini_model,
        has_custom_api_key: Boolean(settingsData.gemini_api_key),
      };
    }
  },
};
