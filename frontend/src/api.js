import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

// Send credentials (cookies) across origins when available
axios.defaults.withCredentials = true;

export const sendMessage = async (message, useWebSearch, conversationId = null) => {
  const payload = { message, use_web_search: useWebSearch };
  if (conversationId) payload.conversation_id = conversationId;
  const response = await axios.post(`${API_BASE}/chat/`, payload);
  return response.data;
};

// Streaming send (tries /chat/stream/ then falls back to normal send)
export const sendMessageStream = async (
  message,
  useWebSearch,
  conversationId = null,
  onChunk = () => {},
  signal = null
) => {
  const payload = { message, use_web_search: useWebSearch };
  if (conversationId) payload.conversation_id = conversationId;

  try {
    const res = await fetch(`${API_BASE}/chat/stream/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal,
      credentials: 'include',
    });

    if (!res.ok) {
      // Fallback to regular API
      return await sendMessage(message, useWebSearch, conversationId);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let done = false;
    let accumulated = '';

    while (!done) {
      const { value, done: d } = await reader.read();
      done = d;
      if (value) {
        const chunk = decoder.decode(value, { stream: true });
        accumulated += chunk;
        onChunk(chunk, accumulated);
      }
    }

    // When stream completes, try to parse final json (if server sends it)
    try {
      const json = JSON.parse(accumulated);
      return json;
    } catch (e) {
      // If not JSON, return simple structure
      return { assistant_message: { id: Date.now(), role: 'assistant', content: accumulated } };
    }
  } catch (err) {
    // If aborted or streaming failed, propagate
    throw err;
  }
};

export const rateMessage = async (messageId, rating) => {
  const response = await axios.post(`${API_BASE}/rate/`, { message_id: messageId, rating });
  return response.data;
};

export const fetchHistory = async (conversationId = null) => {
  const url = conversationId ? `${API_BASE}/history/?conversation_id=${conversationId}` : `${API_BASE}/history/`;
  const response = await axios.get(url);
  return response.data;
};

export const fetchConversations = async () => {
  const response = await axios.get(`${API_BASE}/conversations/`);
  return response.data;
};

export const createConversation = async (title = 'New conversation') => {
  const response = await axios.post(`${API_BASE}/conversations/`, { title });
  return response.data;
};