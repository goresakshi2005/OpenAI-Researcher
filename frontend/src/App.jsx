import { useEffect, useRef, useState } from "react";
import { sendMessage, sendMessageStream, fetchHistory, rateMessage, fetchConversations, createConversation } from "./api";
import ChatMessage from "./components/ChatMessage";
import Rating from "./components/Rating";
import TypingIndicator from "./components/TypingIndicator";
import Sidebar from "./components/Sidebar";
import ChatInput from "./components/ChatInput";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [useWebSearch, setUseWebSearch] = useState(true);
  const [conversationId, setConversationId] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const bottomRef = useRef(null);
  const abortControllerRef = useRef(null);

  useEffect(() => {
    fetchHistory().then(setMessages);
    fetchConversations().then(setConversations).catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const tempUser = { id: Date.now(), role: 'user', content: input };

    // add user bubble
    setMessages((prev) => [...prev, tempUser]);
    setInput('');
    setLoading(true);

    // prepare assistant placeholder and streaming
    const tempAssistant = { id: Date.now() + 1, role: 'assistant', content: '' };
    setMessages((prev) => [...prev, tempAssistant]);

    // abort controller for stopping streaming
    if (abortControllerRef.current) {
      try { abortControllerRef.current.abort(); } catch (e) {}
    }
    const ac = new AbortController();
    abortControllerRef.current = ac;

    try {
      let accumulated = '';
      const onChunk = (chunk) => {
        accumulated += chunk;
        setMessages((prev) =>
          prev.map((m) => (m.id === tempAssistant.id ? { ...m, content: accumulated } : m))
        );
      };

      const res = await sendMessageStream(tempUser.content, useWebSearch, conversationId, onChunk, ac.signal);

      // If response is a structured object, update conversation id and final messages
      if (res.conversation_id) setConversationId(res.conversation_id);

      // If server returned structured messages, replace assistant and add user message
      if (res.user_message && res.assistant_message) {
        setMessages((prev) => prev.map((m) => (m.id === tempAssistant.id ? res.assistant_message : m)));
      } else if (res.assistant_message) {
        setMessages((prev) => prev.map((m) => (m.id === tempAssistant.id ? res.assistant_message : m)));
      } else if (typeof res === 'string' || res.assistant_message == null) {
        // keep accumulated content
        setMessages((prev) => prev.map((m) => (m.id === tempAssistant.id ? { ...m, content: accumulated } : m)));
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Streaming aborted');
      } else {
        console.error('Send failed:', error);
      }
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleNewConversation = async () => {
    try {
      const res = await createConversation('New conversation');
      const id = res.id || res.conversation_id || null;
      if (id) {
        setConversationId(id);
        // refresh conversation list
        const list = await fetchConversations();
        setConversations(list);
        // clear messages for new conv
        setMessages([]);
      }
    } catch (e) {
      console.error('Create conversation failed', e);
    }
  };

  const handleSelectConversation = async (conv) => {
    if (!conv) return;
    setConversationId(conv.id);
    try {
      const history = await fetchHistory(conv.id);
      setMessages(history || []);
    } catch (e) {
      console.error('Failed to load conversation', e);
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

  // Copy assistant content
  const handleCopy = (message) => {
    navigator.clipboard?.writeText(message.content || '')?.catch(() => {});
  };

  // Regenerate: resend the last user message and replace assistant
  const handleRegenerate = async (assistantMessage) => {
    // find last user message before this assistant
    const idx = messages.findIndex((m) => m.id === assistantMessage.id);
    if (idx <= 0) return;
    const prev = messages[idx - 1];
    if (!prev || prev.role !== 'user') return;

    setInput(prev.content);
    // remove assistant message and call handleSend
    setMessages((prevMsgs) => prevMsgs.filter((m) => m.id !== assistantMessage.id));
    // small delay then send
    setTimeout(() => handleSend(), 50);
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      try { abortControllerRef.current.abort(); } catch (e) {}
    }
    setLoading(false);
  };

  return (
    <div className="h-screen bg-gradient-to-br from-indigo-900 via-slate-900 to-black text-white app-shell">
      <Sidebar
        conversations={conversations}
        selectedId={conversationId}
        onSelect={handleSelectConversation}
        onNewChat={handleNewConversation}
        collapsed={sidebarCollapsed}
        mobileOpen={mobileSidebarOpen}
        onCloseMobile={() => setMobileSidebarOpen(false)}
      />

      {/* Mobile floating button to open sidebar */}
      {!mobileSidebarOpen && (
        <button
          onClick={() => setMobileSidebarOpen(true)}
          className="md:hidden fixed left-4 bottom-6 z-50 bg-indigo-600 text-white w-12 h-12 rounded-full shadow-lg flex items-center justify-center"
          aria-label="Open sidebar"
        >
          ☰
        </button>
      )}

      <div className="chat-column">
        {/* Header */}
        <header className="sticky top-0 z-20 backdrop-blur-xl bg-white/10 border-b border-white/10">
          <div className="max-w-5xl mx-auto px-4 py-4 flex justify-between items-center">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarCollapsed((s) => !s)}
                className="md:hidden bg-white/5 p-2 rounded-md mr-1"
                aria-label="Toggle sidebar"
              >
                ☰
              </button>

              <h1 className="text-lg font-semibold tracking-wide">
                <i className="fas fa-robot mr-2"></i> AI Research Assistant
              </h1>
            </div>

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
        <main className="flex-1 overflow-y-auto px-4 py-6 custom-scroll chat-inner">
          <div className="chat-pane max-w-5xl mx-auto space-y-5">
            {messages.map((msg) => (
            <div key={msg.id}>
              <ChatMessage
                message={msg}
                onCopy={handleCopy}
                onRegenerate={handleRegenerate}
                onStop={handleStop}
                isStreaming={loading}
              />
              {msg.role === 'assistant' && msg.rating == null && (
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

        <ChatInput
          input={input}
          setInput={setInput}
          onSend={handleSend}
          loading={loading}
          useWebSearch={useWebSearch}
          setUseWebSearch={setUseWebSearch}
        />
      </div>
    </div>
  );
}