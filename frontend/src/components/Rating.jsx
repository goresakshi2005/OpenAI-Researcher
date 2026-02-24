import React, { useState } from 'react';

const Rating = ({ messageId, onRate }) => {
  const [hover, setHover] = useState(0);
  const [rating, setRating] = useState(0);

  const handleClick = (value) => {
    setRating(value);
    onRate(messageId, value);
  };

  return (
    <div className="flex items-center space-x-1">
      {[1,2,3,4,5].map(star => (
        <button
          key={star}
          className={`text-2xl ${star <= (hover || rating) ? 'text-yellow-400' : 'text-gray-300'}`}
          onMouseEnter={() => setHover(star)}
          onMouseLeave={() => setHover(0)}
          onClick={() => handleClick(star)}
        >
          ★
        </button>
      ))}
    </div>
  );
};

export default Rating;