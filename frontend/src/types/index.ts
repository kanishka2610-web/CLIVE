export interface Story {
  id: number;
  source_id: number;
  source_name?: string;
  source_icon?: string;
  canonical_url: string;
  original_url: string;
  title: string;
  normalized_title: string;
  author?: string;
  raw_content?: string;
  extracted_content?: string;
  published_at: string;
  created_at: string;
  
  is_ai_related: boolean;
  category: string;
  sub_category?: string;
  companies: string[];
  technologies: string[];
  topics: string[];
  
  importance_score: number;
  novelty_score: number;
  technical_score: number;
  is_breaking: boolean;
  
  headline?: string;
  summary?: string;
  why_it_matters: string[];
  
  is_saved: boolean;
  interaction_state?: 'interested' | 'skipped' | 'swiped' | null;
  rank_score?: number;
}

export interface StoryFeedResponse {
  stories: Story[];
  total: number;
  page: number;
  has_more: boolean;
}

export interface Source {
  id: number;
  name: string;
  url: string;
  feed_type: 'rss' | 'atom' | 'html';
  category: string;
  is_active: boolean;
  icon_url?: string;
  last_scanned_at?: string;
  last_success_at?: string;
  failure_count: number;
  last_error?: string;
  created_at: string;
  story_count?: number;
}

export interface TopicPreference {
  topic: string;
  weight: number;
  positive_count: number;
  negative_count: number;
  updated_at: string;
}

export type TopicWeight = TopicPreference;

export interface UserSetting {
  user_id: string;
  gemini_model: string;
  has_custom_api_key: boolean;
  min_importance_threshold: number;
  auto_scan_enabled: boolean;
}

export interface RadarStats {
  total_sources: number;
  active_sources: number;
  total_stories: number;
  breaking_stories_count: number;
  saved_stories_count: number;
  total_interactions: number;
  last_scan_time?: string;
  is_scanning: boolean;
  category_distribution: { category: string; count: number }[];
  top_topics: string[];
}

export interface RadarInteractResponse {
  success: boolean;
  interaction_type: string;
  story_id: number;
  topics_updated: string[];
  message: string;
}
