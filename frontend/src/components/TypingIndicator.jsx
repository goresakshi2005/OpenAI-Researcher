export default function TypingIndicator() {
  return (
    <div className="flex gap-1 px-4 py-2 bg-white/80 text-black rounded-xl w-fit">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"
          style={{ animationDelay: `${i * 150}ms` }}
        />
      ))}
    </div>
  );
}