import { useEffect, useRef, useState } from "react";
import { sendMessage, fetchHistory, rateMessage } from "./api";
import ChatMessage from "./components/ChatMessage";
import Rating from "./components/Rating";
import TypingIndicator from "./components/TypingIndicator";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [useWebSearch, setUseWebSearch] = useState(true);
  const bottomRef = useRef(null);

  useEffect(() => {
    fetchHistory().then(setMessages);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const tempUser = {
      id: Date.now(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, tempUser]);
    setInput("");
    setLoading(true);

    try {
      const res = await sendMessage(tempUser.content, useWebSearch);
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== tempUser.id),
        res.user_message,
        res.assistant_message,
      ]);
    } catch (error) {
      console.error("Send failed:", error);
      // Optional: show error toast
    } finally {
      setLoading(false);
    }
  };

  // Handle rating submission
  const handleRate = async (messageId, rating) => {
    try {
      await rateMessage(messageId, rating);
      // Update local state so the rating stars disappear
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId ? { ...msg, rating } : msg
        )
      );
    } catch (error) {
      console.error("Rating failed:", error);
    }
  };

  return (
    <div className="h-screen bg-gradient-to-br from-indigo-900 via-slate-900 to-black text-white">
      {/* Header */}
      <header className="sticky top-0 z-20 backdrop-blur-xl bg-white/10 border-b border-white/10">
        <div className="max-w-5xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-lg font-semibold tracking-wide">
            <i className="fas fa-robot mr-2"></i> AI Research Assistant
          </h1>

          <label className="flex items-center gap-2 text-sm opacity-80">
            <span>Web Search</span>
            <input
              type="checkbox"
              checked={useWebSearch}
              onChange={(e) => setUseWebSearch(e.target.checked)}
              className="accent-indigo-500"
            />
          </label>
        </div>
      </header>

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto px-4 py-6 custom-scroll">
        <div className="max-w-5xl mx-auto space-y-5">
          {messages.map((msg) => (
            <div key={msg.id}>
              <ChatMessage message={msg} />
              {msg.role === "assistant" && msg.rating == null && (
                <div className="ml-14 mt-1">
                  <Rating messageId={msg.id} onRate={handleRate} />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="ml-14">
              <TypingIndicator />
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </main>

      {/* Input */}
      <footer className="sticky bottom-0 bg-black/40 backdrop-blur-xl border-t border-white/10">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <div className="relative">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
              placeholder="Ask anything..."
              rows={1}
              className="w-full resize-none rounded-2xl bg-white/10 border border-white/10 px-5 py-4 pr-14 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />

            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-indigo-400 hover:text-indigo-300 disabled:opacity-40 text-xl"
              aria-label="Send message"
            >
              ➤
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}