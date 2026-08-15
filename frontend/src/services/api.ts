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
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Health
  getHealth: async () => {
    const res = await apiClient.get<{ status: string; app: string; version: string }>('/api/health');
    return res.data;
  },

  // Telemetry & Stats
  getRadarStats: async () => {
    const res = await apiClient.get<RadarStats>('/api/status');
    return res.data;
  },

  // Radar Swipe Deck
  getRadarDeck: async (limit = 25, userId = 'default_user') => {
    const res = await apiClient.get<Story[]>('/api/radar/deck', {
      params: { limit, user_id: userId },
    });
    return res.data;
  },

  // Radar Interaction
  interactWithStory: async (
    storyId: number,
    interactionType: string,
    sessionId = 'default_user'
  ) => {
    const res = await apiClient.post<RadarInteractResponse>('/api/radar/interact', {
      story_id: storyId,
      interaction_type: interactionType,
      session_id: sessionId,
    });
    return res.data;
  },

  recordInteraction: async (
    storyId: number,
    interactionType: string,
    sessionId = 'default_user'
  ) => {
    const res = await apiClient.post<RadarInteractResponse>('/api/radar/interact', {
      story_id: storyId,
      interaction_type: interactionType,
      session_id: sessionId,
    });
    return res.data;
  },

  // Specialized Contract Actions
  likeStory: async (storyId: number, userId = 'default_user') => {
    const res = await apiClient.post<RadarInteractResponse>(`/api/stories/${storyId}/like`, null, {
      params: { user_id: userId },
    });
    return res.data;
  },

  dislikeStory: async (storyId: number, userId = 'default_user') => {
    const res = await apiClient.post<RadarInteractResponse>(`/api/stories/${storyId}/dislike`, null, {
      params: { user_id: userId },
    });
    return res.data;
  },

  saveStory: async (storyId: number, userId = 'default_user') => {
    const res = await apiClient.post<RadarInteractResponse>(`/api/stories/${storyId}/save`, null, {
      params: { user_id: userId },
    });
    return res.data;
  },

  openStorySource: async (storyId: number, userId = 'default_user') => {
    const res = await apiClient.post<RadarInteractResponse>(`/api/stories/${storyId}/source-open`, null, {
      params: { user_id: userId },
    });
    return res.data;
  },

  // Feeds
  getFeed: async (params?: {
    category?: string;
    q?: string;
    page?: number;
    limit?: number;
    user_id?: string;
  }) => {
    const res = await apiClient.get<StoryFeedResponse>('/api/feed', { params });
    return res.data;
  },

  getForYouFeed: async (params?: {
    category?: string;
    q?: string;
    page?: number;
    limit?: number;
    user_id?: string;
  }) => {
    const res = await apiClient.get<StoryFeedResponse>('/api/feed', { params });
    return res.data;
  },

  getTrendingFeed: async (page = 1, limit = 20, userId = 'default_user') => {
    const res = await apiClient.get<StoryFeedResponse>('/api/feed/trending', {
      params: { page, limit, user_id: userId },
    });
    return res.data;
  },

  getSavedFeed: async (page = 1, limit = 20, userId = 'default_user') => {
    const res = await apiClient.get<StoryFeedResponse>('/api/feed/saved', {
      params: { page, limit, user_id: userId },
    });
    return res.data;
  },

  getSavedStories: async (page = 1, limit = 20, userId = 'default_user') => {
    const res = await apiClient.get<StoryFeedResponse>('/api/feed/saved', {
      params: { page, limit, user_id: userId },
    });
    return res.data;
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
    const res = await apiClient.get<StoryFeedResponse>('/api/stories', { params });
    return res.data;
  },

  getStoryById: async (id: number) => {
    const res = await apiClient.get<Story>(`/api/stories/${id}`);
    return res.data;
  },

  // Overnight Dispatch (Unique Feature)
  getOvernightDispatch: async (hours = 48) => {
    const res = await apiClient.get<OvernightDispatchResponse>('/api/radar/overnight', {
      params: { hours },
    });
    return res.data;
  },

  // Ask RADAR RAG (Unique Feature)
  askRadar: async (query: string, limit = 5) => {
    const res = await apiClient.post<AskRadarResponse>('/api/radar/ask', { query, limit });
    return res.data;
  },

  // Sources
  getSources: async () => {
    const res = await apiClient.get<Source[]>('/api/sources');
    return res.data;
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
    const res = await apiClient.post<{ status: string; message: string }>('/api/admin/scan');
    return res.data;
  },

  // Preferences
  getPreferences: async (userId = 'default_user') => {
    const res = await apiClient.get<TopicWeight[]>('/api/preferences', {
      params: { user_id: userId },
    });
    return res.data;
  },

  getTopicPreferences: async (userId = 'default_user') => {
    const res = await apiClient.get<TopicWeight[]>('/api/preferences', {
      params: { user_id: userId },
    });
    return res.data;
  },

  updateTopicWeight: async (topic: string, weight: number, userId = 'default_user') => {
    const res = await apiClient.put<TopicWeight>('/api/preferences/topic', { topic, weight }, {
      params: { user_id: userId },
    });
    return res.data;
  },

  updateTopicPreference: async (topic: string, weight: number, userId = 'default_user') => {
    const res = await apiClient.put<TopicWeight>('/api/preferences/topic', { topic, weight }, {
      params: { user_id: userId },
    });
    return res.data;
  },

  resetPreferences: async (userId = 'default_user') => {
    const res = await apiClient.post<{ success: boolean; message: string }>('/api/preferences/reset', null, {
      params: { user_id: userId },
    });
    return res.data;
  },

  getUserSettings: async (userId = 'default_user') => {
    const res = await apiClient.get<UserSetting>('/api/preferences/settings', {
      params: { user_id: userId },
    });
    return res.data;
  },

  updateUserSettings: async (settingsData: Partial<UserSetting> & { gemini_api_key?: string }, userId = 'default_user') => {
    const res = await apiClient.put<UserSetting>('/api/preferences/settings', settingsData, {
      params: { user_id: userId },
    });
    return res.data;
  },
};
