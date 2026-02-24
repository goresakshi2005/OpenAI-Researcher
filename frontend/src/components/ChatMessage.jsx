import MarkdownMessage from './MarkdownMessage';

export default function ChatMessage({ message, onCopy, onRegenerate, onStop, isStreaming }) {
  const isUser = message.role === "user";

  return (
    <div
      className={`group flex items-end gap-3 animate-fade-in ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      {!isUser && (
        <div className="w-9 h-9 flex items-center justify-center rounded-full bg-indigo-600">
          <i className="fas fa-robot text-white"></i>
        </div>
      )}

      <div
        className={`relative max-w-[75%] px-5 py-3 rounded-2xl shadow-lg break-words bubble ${
          isUser
            ? "msg-user text-white rounded-br-none"
            : "msg-assistant text-gray-900 rounded-bl-none"
        }`}
      >
        <div className="prose max-w-full text-sm">
          <MarkdownMessage content={message.content} />
        </div>

        {/* Action buttons (appear on hover) */}
        {!isUser && (
          <div className="absolute -top-8 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-2 items-center hidden-on-mobile">
            <button
              onClick={() => onCopy && onCopy(message)}
              className="bg-white/10 hover:bg-white/20 px-2 py-1 rounded text-xs"
              title="Copy"
            >
              Copy
            </button>

            <button
              onClick={() => onRegenerate && onRegenerate(message)}
              className="bg-white/10 hover:bg-white/20 px-2 py-1 rounded text-xs"
              title="Regenerate"
            >
              Regenerate
            </button>

            {isStreaming ? (
              <button
                onClick={() => onStop && onStop()}
                className="bg-red-600 hover:bg-red-500 px-2 py-1 rounded text-xs"
                title="Stop"
              >
                Stop
              </button>
            ) : null}
          </div>
        )}
      </div>

      {isUser && (
        <div className="w-9 h-9 flex items-center justify-center rounded-full bg-slate-700">
          <i className="fas fa-user text-white"></i>
        </div>
      )}
    </div>
  );
}