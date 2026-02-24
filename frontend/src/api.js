import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';  // Django dev server

export const sendMessage = async (message, useWebSearch) => {
  const response = await axios.post(`${API_BASE}/chat/`, { message, use_web_search: useWebSearch });
  return response.data;
};

export const rateMessage = async (messageId, rating) => {
  const response = await axios.post(`${API_BASE}/rate/`, { message_id: messageId, rating });
  return response.data;
};

export const fetchHistory = async () => {
  const response = await axios.get(`${API_BASE}/history/`);
  return response.data;
};