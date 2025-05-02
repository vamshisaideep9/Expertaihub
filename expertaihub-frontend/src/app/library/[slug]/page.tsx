"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import ResponsiveSidebar from "@/components/ResponsiveSidebar";
import api from '@/lib/apiprivate';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Mic, Send } from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [quota, setQuota] = useState({ used: 0, limit: 15 });
  const [loadingAnswer, setLoadingAnswer] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.push("/signin");
    } else {
      setLoading(false);
    }
  }, [router]);

  async function handleAsk() {
    if (!query.trim()) return;
    setLoadingAnswer(true);
    setAnswer("");
    try {
      const res = await api.post("/v1/immigration-ai/free/", {
        question: query,
        chat_history: [],
        niche: "immigration",
        country: "usa",
      });

      const data = res.data;

      setAnswer(data.answer);
      setQuota(data.quota);

      if (data.slug) {
        router.push(`/library/${data.slug}`);
      }
    } catch (err) {
      setAnswer("Server error. Please try again.");
    }
    setLoadingAnswer(false);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-background text-foreground">
        <p className="text-xl font-semibold">Loading...</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      <ResponsiveSidebar />
      <main className="flex-1 flex flex-col items-center justify-center px-4 relative bg-[#f9fafb] dark:bg-[#0f0f0f] text-foreground">
        <h1 className="text-4xl md:text-5xl font-semibold mb-10 tracking-tight">Expertaihub</h1>

        <div className="w-full max-w-2xl">
          <div className="rounded-xl border border-border bg-muted px-4 py-3 flex items-center gap-3 shadow-md">
            <Input
              disabled={quota.used >= quota.limit}
              className="flex-1 bg-transparent text-base focus-visible:ring-0 focus-visible:ring-offset-0 border-none"
              placeholder="Ask anything about immigration…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />

            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" className="rounded-full px-3 text-sm cursor-pointer">
                Search
              </Button>
              <Button variant="ghost" size="icon" className="hover:bg-accent cursor-pointer">
                <Mic className="w-5 h-5" />
              </Button>
              <Button
                size="icon"
                className="bg-primary text-white hover:bg-primary/90 cursor-pointer"
                onClick={handleAsk}
                disabled={loadingAnswer || quota.used >= quota.limit}
              >
                <Send className="w-5 h-5" />
              </Button>
            </div>
          </div>

          <div className="mt-3">
            <p className="text-sm text-muted-foreground">
              🔢 {quota.used} / {quota.limit} free queries used this month
            </p>
            {quota.used >= quota.limit && (
              <div className="text-red-500 text-sm mt-1">
                🚫 Limit reached. Upgrade to Pro for unlimited access.
              </div>
            )}
          </div>

          {answer && (
            <div className="mt-6 w-full bg-white dark:bg-zinc-900 p-4 rounded-xl shadow">
              <h4 className="font-semibold mb-2">Answer:</h4>
              <p className="text-sm text-muted-foreground whitespace-pre-line">{answer}</p>
            </div>
          )}
        </div>

        <footer className="absolute bottom-4 text-xs text-muted-foreground">
          <p>
            Need help? Visit our <a href="#" className="underline">Help Center</a>
          </p>
        </footer>
      </main>
    </div>
  );
}

function getToken() {
  if (typeof document !== "undefined") {
    const match = document.cookie.match(new RegExp('(^| )token=([^;]+)'));
    return match?.[2] || null;
  }
  return null;
}
