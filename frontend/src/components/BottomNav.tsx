import React from 'react';
import { NavLink } from 'react-router-dom';
import { Radio, Compass, Flame, Bookmark, Rss, SlidersHorizontal } from 'lucide-react';

interface BottomNavProps {
  savedCount?: number;
  breakingCount?: number;
}

export const BottomNav: React.FC<BottomNavProps> = ({ savedCount = 0, breakingCount = 0 }) => {
  const navItems = [
    { to: '/', label: 'RADAR', icon: Radio, exact: true },
    { to: '/for-you', label: 'For You', icon: Compass },
    { to: '/trending', label: 'Trending', icon: Flame, badge: breakingCount > 0 ? breakingCount : undefined },
    { to: '/saved', label: 'Saved', icon: Bookmark, badge: savedCount > 0 ? savedCount : undefined },
    { to: '/sources', label: 'Sources', icon: Rss },
    { to: '/settings', label: 'Settings', icon: SlidersHorizontal },
  ];

  return (
    <nav className="fixed sm:absolute bottom-0 left-0 right-0 z-40 bg-surface/90 backdrop-blur-xl border-t border-white/10 px-2 py-2 select-none">
      <div className="flex items-center justify-around max-w-lg mx-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `relative flex flex-col items-center justify-center py-1 px-2 rounded-xl transition-all duration-200 ${
                  isActive
                    ? 'text-electric font-semibold'
                    : 'text-gray-400 hover:text-gray-200'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <div className="relative">
                    <Icon className={`w-5 h-5 transition-transform ${isActive ? 'scale-110' : ''}`} />
                    {item.badge !== undefined && (
                      <span className="absolute -top-1.5 -right-2.5 min-w-[16px] h-4 px-1 rounded-full bg-signal-red text-[9px] font-mono text-white flex items-center justify-center font-bold">
                        {item.badge}
                      </span>
                    )}
                  </div>
                  <span className="text-[10px] font-mono mt-1 tracking-tight">
                    {item.label}
                  </span>
                  {isActive && (
                    <span className="absolute bottom-0 w-4 h-0.5 rounded-full bg-electric shadow-[0_0_8px_#10E760]" />
                  )}
                </>
              )}
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
};
