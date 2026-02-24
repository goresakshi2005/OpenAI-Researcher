import React from 'react';

export default function ChatInput({ input, setInput, onSend, loading, useWebSearch, setUseWebSearch }) {
  return (
    <div className="sticky bottom-0 bg-black/40 backdrop-blur-xl border-t border-white/10 input-area">
      <div className="max-w-5xl mx-auto px-4 py-4">
        <div className="flex items-start gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && onSend()}
            placeholder="Ask anything..."
            rows={1}
            className="w-full resize-none rounded-2xl bg-white/10 border border-white/10 px-5 py-4 pr-14 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />

          <div className="flex flex-col items-end gap-2">
            <label className="flex items-center gap-2 text-sm opacity-80">
              <span>Web</span>
              <input
                type="checkbox"
                checked={useWebSearch}
                onChange={(e) => setUseWebSearch(e.target.checked)}
                className="accent-indigo-500"
              />
            </label>

            <button
              onClick={onSend}
              disabled={!input.trim() || loading}
              className="w-10 h-10 md:w-auto md:h-auto p-2 md:p-0 bg-indigo-600 hover:bg-indigo-500 rounded-full md:rounded text-white flex items-center justify-center disabled:opacity-40"
              aria-label="Send message"
            >
              ➤
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
