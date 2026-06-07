"use client";

export interface Message {
  role: "user" | "assistant";
  content: string;
  toolCallsMade?: number;
  loading?: boolean;
}

export function ChatMessage({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-gray-800 text-gray-100 border border-gray-700"
        }`}
      >
        {msg.loading ? (
          <div className="flex items-center gap-2">
            <div className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </div>
            <span className="text-gray-400 text-xs">Analysing race data…</span>
          </div>
        ) : (
          <>
            <p className="whitespace-pre-wrap">{msg.content}</p>
            {!isUser && msg.toolCallsMade !== undefined && msg.toolCallsMade > 0 && (
              <p className="mt-2 text-xs text-gray-500">
                📡 {msg.toolCallsMade} data call{msg.toolCallsMade > 1 ? "s" : ""} made
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
