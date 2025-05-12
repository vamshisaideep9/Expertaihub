// src/app/library/[slug]/page.tsx
"use client";

import { useEffect, useState, FormEvent, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import ResponsiveSidebar from "@/components/ResponsiveSidebar";
import api from "@/lib/apiprivate";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Send, Mic } from "lucide-react";

interface Message {
  role: "user" | "ai";
  content: string;
}

interface Quota {
  used: number;
  limit: number;
}

export default function ChatPage() {
  const router = useRouter();
  const { slug } = useParams();  
  const sessionId = typeof slug === "string" ? slug : null;

  const [history, setHistory] = useState<Message[]>([]);
  const [quota, setQuota] = useState<Quota>({ used: 0, limit: 15 });
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // 1) Redirect if no slug
  useEffect(() => {
    if (!sessionId) router.push("/");
  }, [sessionId, router]);

  // 2) On mount: “resume” by pinging the free endpoint
  useEffect(() => {
    if (!sessionId) return;
    (async () => {
      try {
        const res = await api.post("/v1/immigration-ai/free/", {
          question: "__resume__",        // dummy question
          chat_history: history,         // initially []
          niche: "immigration",
          country: "usa",
          session_id: sessionId,
        });
        // hydrate your state
        setHistory(res.data.chat_history);
        setQuota(res.data.quota);
      } catch (err) {
        console.error("Failed to resume chat session:", err);
      }
    })();
  }, [sessionId]);

  // 3) autoscroll on new messages
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  // 4) Handle sends as before
  const onSend = async (e?: FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || sending || quota.used >= quota.limit) return;
    setSending(true);
    try {
      const res = await api.post("/v1/immigration-ai/free/", {
        question: input.trim(),
        chat_history: history,
        niche: "immigration",
        country: "usa",
        session_id: sessionId,
      });
      const data = res.data as {
        answer: string;
        chat_history: Message[];
        quota: Quota;
        session_id: string;
      };
      setHistory(data.chat_history);
      setQuota(data.quota);
      setInput("");
    } catch (err: any) {
      console.error("Chat error:", err);
      alert(err?.response?.data?.detail || err.message || "Something went wrong.");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      <ResponsiveSidebar />
      <main className="flex-1 flex flex-col bg-[#f9fafb] dark:bg-[#0f0f0f]">
        {/* Chat */}
        <div className="flex-1 overflow-auto p-6 space-y-4">
          {history.map((m, i) => (
            <div
              key={i}
              className={`max-w-[80%] p-3 rounded-lg ${
                m.role === "user" ? "self-end bg-blue-100" : "self-start bg-gray-100"
              }`}
            >
              {m.content}
            </div>
          ))}
          <div ref={scrollRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t bg-white">
          <form onSubmit={onSend} className="flex items-center gap-2">
            <Input
              className="flex-1"
              placeholder="Type your question…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={sending || quota.used >= quota.limit}
            />
            <Button size="icon" onClick={onSend} disabled={sending}>
              <Send className={sending ? "animate-spin" : ""} />
            </Button>
            <Button size="icon">
              <Mic />
            </Button>
          </form>
          <p className="mt-2 text-sm text-gray-500">
            🔢 {quota.used} / {quota.limit} free queries used
          </p>
          {quota.used >= quota.limit && (
            <p className="mt-1 text-sm text-red-500">
              🚫 You’ve reached your free limit. Upgrade to continue.
            </p>
          )}
        </div>
      </main>
    </div>
  );
}
