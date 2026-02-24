import React, { useState, useEffect, useRef } from 'react';
import { sendMessage, rateMessage, fetchHistory } from './api';
import ChatMessage from './components/ChatMessage';
import Rating from './components/Rating';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [useWebSearch, setUseWebSearch] = useState(true);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Load chat history on mount
    const loadHistory = async () => {
      const history = await fetchHistory();
      setMessages(history);
    };
    loadHistory();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async () => {
    if (!input.trim()) return;
    setLoading(true);
    try {
      const data = await sendMessage(input, useWebSearch);
      // Add both user and assistant messages to state
      setMessages(prev => [...prev, data.user_message, data.assistant_message]);
      setInput('');
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRate = async (messageId, rating) => {
    try {
      await rateMessage(messageId, rating);
      // Optionally update local message rating
      setMessages(prev =>
        prev.map(msg => (msg.id === messageId ? { ...msg, rating } : msg))
      );
    } catch (error) {
      console.error('Error rating message:', error);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow p-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">AI Research Assistant</h1>
        <div className="flex items-center space-x-2">
          <label htmlFor="webSearch" className="text-sm">Web Search</label>
          <input
            type="checkbox"
            id="webSearch"
            checked={useWebSearch}
            onChange={(e) => setUseWebSearch(e.target.checked)}
            className="toggle"
          />
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((msg) => (
          <div key={msg.id}>
            <ChatMessage message={msg} />
            {msg.role === 'assistant' && msg.rating === null && (
              <div className="flex justify-start ml-12 mt-1">
                <Rating messageId={msg.id} onRate={handleRate} />
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="bg-white p-4 border-t">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type your message..."
            className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading}
            className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            {loading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;