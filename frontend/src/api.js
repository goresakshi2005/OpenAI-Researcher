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

export const rateMessage = async (messageId, rating) => {
  const response = await axios.post(`${API_BASE}/rate/`, { message_id: messageId, rating });
  return response.data;
};

export const fetchHistory = async (conversationId = null) => {
  const url = conversationId ? `${API_BASE}/history/?conversation_id=${conversationId}` : `${API_BASE}/history/`;
  const response = await axios.get(url);
  return response.data;
};