"use client";
import { useState, useRef, useEffect } from "react";
import { v4 as uuid } from "uuid";
import { sendMessage, clearSession } from "@/lib/api";
import { ChatMessage, Message } from "@/components/ChatMessage";
import { RaceSelector } from "@/components/RaceSelector";

export default function Home() {
  const [sessionId] = useState(() => uuid());
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hi! I'm your F1 race analyst. Ask me anything about a race — strategies, lap times, why someone won or lost. I'll pull real timing data to back up every claim.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function submit(question?: string) {
    const text = (question ?? input).trim();
    if (!text || loading) return;
    setInput("");
    setError(null);

    setMessages((prev) => [
      ...prev,
      { role: "user", content: text },
      { role: "assistant", content: "", loading: true },
    ]);
    setLoading(true);

    try {
      const res = await sendMessage(text, sessionId);
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = {
          role: "assistant",
          content: res.response,
          toolCallsMade: res.tool_calls_made,
        };
        return next;
      });
    } catch (e: any) {
      setError(e.message);
      setMessages((prev) => prev.slice(0, -1)); // remove loading bubble
    } finally {
      setLoading(false);
    }
  }

  function handleClear() {
    clearSession(sessionId);
    setMessages([
      {
        role: "assistant",
        content: "Conversation cleared. What race would you like to analyse?",
      },
    ]);
  }

  return (
    <div className="flex h-screen bg-gray-950 text-white overflow-hidden">
      {/* Sidebar */}
      <aside className="w-72 border-r border-gray-800 flex flex-col p-4 overflow-y-auto flex-shrink-0">
        <h1 className="text-lg font-bold mb-1">🏎 F1 Analyst</h1>
        <p className="text-xs text-gray-400 mb-6">Real data · No hallucinations</p>
        <RaceSelector onQuestion={(q) => submit(q)} />
        <div className="mt-auto pt-4">
          <button
            onClick={handleClear}
            className="w-full text-xs text-gray-500 hover:text-gray-300 py-2 border border-gray-700 rounded-lg transition-colors"
          >
            Clear conversation
          </button>
        </div>
      </aside>

      {/* Chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {messages.map((msg, i) => (
            <ChatMessage key={i} msg={msg} />
          ))}
          {error && (
            <div className="text-red-400 text-sm text-center my-2">
              ⚠ {error} — is the backend running? (uvicorn main:app --port 8000)
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="border-t border-gray-800 px-6 py-4">
          <div className="flex gap-3 items-end">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  submit();
                }
              }}
              placeholder="Ask about any F1 race… (Enter to send, Shift+Enter for new line)"
              rows={2}
              disabled={loading}
              className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500 resize-none disabled:opacity-50 placeholder-gray-500"
            />
            <button
              onClick={() => submit()}
              disabled={loading || !input.trim()}
              className="px-5 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-xl text-sm font-medium transition-colors"
            >
              {loading ? "…" : "Send"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
