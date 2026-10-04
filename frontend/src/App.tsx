import React, { useState, useCallback, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { Header } from './components/Header';
import { BottomNav } from './components/BottomNav';
import { SplashScreen } from './components/SplashScreen';
import { StoryDetailModal } from './components/StoryDetailModal';
import { RadarPage } from './pages/RadarPage';
import { ForYouPage } from './pages/ForYouPage';
import { TrendingPage } from './pages/TrendingPage';
import { SavedPage } from './pages/SavedPage';
import { SourcesPage } from './pages/SourcesPage';
import { SettingsPage } from './pages/SettingsPage';
import { api } from './services/api';
import type { Story } from './types';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: true,
      staleTime: 1000 * 10,
    },
  },
});

const AppContent: React.FC = () => {
  const [showSplash, setShowSplash] = useState(() => {
    try {
      const hasSeen = sessionStorage.getItem('clive_splash_seen');
      return !hasSeen;
    } catch {
      return false;
    }
  });
  const [selectedStory, setSelectedStory] = useState<Story | null>(null);

  // Trigger live feed ingestion scan whenever user opens or reloads page
  useEffect(() => {
    api.triggerScan().catch(() => {});
  }, []);

  const handleSplashComplete = useCallback(() => {
    try {
      sessionStorage.setItem('clive_splash_seen', 'true');
    } catch {
      // Ignore if cookies/storage blocked
    }
    setShowSplash(false);
  }, []);

  const { data: stats } = useQuery({
    queryKey: ['radarStats'],
    queryFn: api.getRadarStats,
    refetchInterval: 10000,
  });


  return (
    <>
      {showSplash && <SplashScreen onComplete={handleSplashComplete} />}

      <div className="mobile-frame-container">
        <div className="app-screen">
          {/* Top Header with Ask & Overnight tools */}
          <Header
            isScanning={stats?.is_scanning}
            onSelectStory={(story) => setSelectedStory(story)}
          />

          {/* Scrollable Page Body */}
          <main className="flex-1 flex flex-col overflow-hidden relative">
            <Routes>
              <Route path="/" element={<RadarPage />} />
              <Route path="/for-you" element={<ForYouPage />} />
              <Route path="/trending" element={<TrendingPage />} />
              <Route path="/saved" element={<SavedPage />} />
              <Route path="/sources" element={<SourcesPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </main>

          {/* Bottom Navigation */}
          <BottomNav
            savedCount={stats?.saved_stories_count || 0}
            breakingCount={stats?.breaking_stories_count || 0}
          />
        </div>
      </div>

      {/* Global Story Detail Modal */}
      <StoryDetailModal
        story={selectedStory}
        isOpen={Boolean(selectedStory)}
        onClose={() => setSelectedStory(null)}
      />
    </>
  );
};

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
