import React from 'react';

export default function Sidebar({
  conversations = [],
  selectedId = null,
  onSelect,
  onNewChat,
  collapsed = false,
  mobileOpen = false,
  onCloseMobile = null,
}) {
  // Desktop width classes (collapsed vs expanded)
  const desktopWidth = collapsed ? 'w-16' : 'w-72';

  // Mobile transform: slide-in when `mobileOpen` true
  const mobileTransform = mobileOpen ? 'translate-x-0' : '-translate-x-full';

  return (
    <>
      {/* Backdrop for mobile when open */}
      <div
        className={`fixed inset-0 bg-black/50 z-30 md:hidden transition-opacity ${mobileOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        onClick={() => onCloseMobile && onCloseMobile()}
      />

      <aside
        className={`sidebar transition-width duration-300 ease-in-out ${desktopWidth} ${mobileTransform} md:translate-x-0 border-r border-white/10 bg-black/60 md:static fixed top-0 left-0 h-full z-40 md:z-auto overflow-hidden`}
      >
        <div className="px-4 py-3 border-b border-white/5">
          <button
            onClick={onNewChat}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white py-2 rounded-md"
          >
            + New Chat
          </button>
        </div>

        <div className="p-3 overflow-y-auto flex-1 text-sm text-gray-300">
          <p className="opacity-60">Recent</p>
          <ul className="mt-2 space-y-2">
            {conversations.length === 0 && (
              <li className="px-3 py-2 rounded bg-white/5">No conversations yet</li>
            )}
            {conversations.map((c) => (
              <li
                key={c.id}
                onClick={() => {
                  onSelect && onSelect(c);
                  // close mobile panel after selection
                  if (onCloseMobile) onCloseMobile();
                }}
                className={`px-3 py-2 rounded cursor-pointer ${selectedId === c.id ? 'bg-indigo-700 text-white' : 'bg-white/5'}`}
              >
                {c.title || `Conversation ${c.id}`}
              </li>
            ))}
          </ul>
        </div>

        <div className="px-3 py-4 text-xs text-gray-400 border-t border-white/5">
          <div className="mb-2">Model</div>
          <select className="w-full bg-transparent border border-white/10 rounded px-2 py-1">
            <option>gpt-4o (default)</option>
            <option>gpt-4</option>
            <option>gpt-3.5</option>
          </select>
        </div>
      </aside>
    </>
  );
}
