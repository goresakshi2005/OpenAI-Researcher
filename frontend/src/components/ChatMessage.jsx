export default function ChatMessage({ message }) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex items-end gap-3 animate-fade-in ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      {!isUser && (
        <div className="w-9 h-9 flex items-center justify-center rounded-full bg-indigo-600">
          <i className="fas fa-robot text-white"></i>
        </div>
      )}

      <div
        className={`max-w-[75%] px-5 py-3 rounded-2xl shadow-lg ${
          isUser
            ? "bg-indigo-600 text-white rounded-br-none"
            : "bg-white/90 text-gray-900 rounded-bl-none"
        }`}
      >
        {message.content}
      </div>

      {isUser && (
        <div className="w-9 h-9 flex items-center justify-center rounded-full bg-slate-700">
          <i className="fas fa-user text-white"></i>
        </div>
      )}
    </div>
  );
}