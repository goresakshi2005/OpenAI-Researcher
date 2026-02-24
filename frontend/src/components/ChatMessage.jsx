import React from 'react';

const ChatMessage = ({ message }) => {
  const isUser = message.role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-3/4 p-3 rounded-lg ${
        isUser ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'
      }`}>
        {message.content}
      </div>
    </div>
  );
};

export default ChatMessage;