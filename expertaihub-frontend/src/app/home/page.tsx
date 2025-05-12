"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import ResponsiveSidebar from "@/components/ResponsiveSidebar";
import api from "@/lib/apiprivate";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Mic, Send } from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const [loadingAuth, setLoadingAuth] = useState(true);
  const [question, setQuestion] = useState("");
  const [sending, setSending] = useState(false);
  const [quota, setQuota] = useState({ used: 0, limit: 15 });

  // Redirect to signin if no token
  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.push("/signin");
    } else {
      setLoadingAuth(false);
    }
  }, [router]);

  async function handleAsk() {
    if (!question.trim()) return;
    setSending(true);

    try {
      const res = await api.post("/v1/immigration-ai/free/", {
        question,
        chat_history: [],           
        niche: "immigration",
        country: "usa",
      });

      const data = res.data;
      setQuota(data.quota);
      if (data.slug) {
        router.push(`library/${data.slug}`);
        return;
      }
      alert("No slug returned from server. Answer:\n\n" + data.answer);
    } catch (err: any) {
      console.error(err);
      alert("Error sending your question. Please try again.");
    } finally {
      setSending(false);
      setQuestion("");
    }
  }

  if (loadingAuth) {
    return (
      <div className="flex items-center justify-center h-screen bg-background text-foreground">
        <p className="text-xl font-semibold">Loading…</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      <ResponsiveSidebar />
      <main className="flex-1 flex flex-col items-center justify-center px-4 bg-[#f9fafb] dark:bg-[#0f0f0f] text-foreground">
        <h1 className="text-4xl md:text-5xl font-semibold mb-10 tracking-tight">
          Expertaihub
        </h1>

        <div className="w-full max-w-2xl">
          <div className="flex items-center gap-3 p-4 bg-muted rounded-xl border border-border shadow-md">
            <Input
              placeholder="Ask anything about immigration…"
              className="flex-1 bg-transparent border-none focus-visible:ring-0 focus-visible:ring-offset-0"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !sending && handleAsk()}
              disabled={sending || quota.used >= quota.limit}
            />

            <Button
              variant="ghost"
              size="icon"
              className="hover:bg-accent"
              onClick={handleAsk}
              disabled={sending || quota.used >= quota.limit}
            >
              {sending ? (
                <Send className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </Button>

            <Button variant="ghost" size="icon">
              <Mic className="w-5 h-5" />
            </Button>
          </div>
          <div className="mt-3">
            <p className="text-sm text-muted-foreground">
              🔢 {quota.used} / {quota.limit} free queries used this month
            </p>
            {quota.used >= quota.limit && (
              <p className="text-red-500 text-sm mt-1">
                🚫 You’ve reached your free limit. Upgrade to keep chatting.
              </p>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

// Pull token from cookie
function getToken() {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(^| )token=([^;]+)/);
  return match ? match[2] : null;
}