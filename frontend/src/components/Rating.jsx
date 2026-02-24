import { useState } from "react";

export default function Rating({ messageId, onRate }) {
  const [hover, setHover] = useState(0);

  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          onClick={() => onRate(messageId, star)}
          onMouseEnter={() => setHover(star)}
          onMouseLeave={() => setHover(0)}
          className={`text-2xl focus:outline-none focus:ring-2 focus:ring-indigo-500 rounded ${
            star <= hover ? "text-yellow-400" : "text-gray-300"
          }`}
          aria-label={`Rate ${star} star${star > 1 ? "s" : ""}`}
        >
          ★
        </button>
      ))}
    </div>
  );
}