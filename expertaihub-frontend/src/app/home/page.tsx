// src/app/home/page.tsx
"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Send, Mic, Search, ArrowUpLeft, Star, StopCircle } from "lucide-react";
import apiPrivate from "@/lib/apiprivate";
import ResponsiveSidebar from "@/components/ResponsiveSidebar";
import { useMonthlyUsage } from "@/hooks/useMonthlyUsage";

const DEFAULT_SUGGESTIONS = [
  "What documents are required to file Form AR-11?",
  "Can you explain DACA eligibility and benefits?",
  "What is the step-by-step process to renew my Green Card?",
  "How should I prepare for a visa interview?",
  "What are the steps to bring my spouse to the USA?",
];

export default function HomePage() {
  const [question, setQuestion] = useState("");
  const [processing, setProcessing] = useState(false);
  const [showSug, setShowSug] = useState(false);
  /* -----------------------------------------------------------
+     1)  Pick advisor & country once – then hold them in state
+         (query-params override; fallback to Immigration / USA)
+     ----------------------------------------------------------- */
  const search     = useSearchParams();
  const [advisorName] = useState(
    (search.get("advisor")  ?? "immigration").toLowerCase()
  );
  const [countryName] = useState(
    (search.get("country")  ?? "USA").toUpperCase()
  );

  /* you can delete the old /advisor/ and /country/ fetch calls */
  const [pendingSlug, setPendingSlug] = useState<string | null>(null);   // ← track the slug
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);
  const controllerRef = useRef<AbortController | null>(null);

      /*  realtime usage ---------------------------------------------- */
      const [currentUser, setCurrentUser] = useState<{ id: number }>({ id: 0 });
      useEffect(() => {
       apiPrivate.get<{ id: number }>("/users/me/")
          .then((r) => setCurrentUser(r.data))
          .catch(console.error);
      }, []);
    
      const { used, limit, refresh: refreshUsage } = useMonthlyUsage(currentUser.id);
      const outOfQuota = used >= limit;


  // abort on unmount
  useEffect(() => () => controllerRef.current?.abort(), []);

  const placeholder = `Ask anything about ${advisorName} in ${countryName} …`;
  const filtered = DEFAULT_SUGGESTIONS.filter(s =>
    s.toLowerCase().includes(question.toLowerCase())
  );

  async function stopProcessing() {
    // 1️⃣ abort fetch
    controllerRef.current?.abort();

    // 2️⃣ if we had a pending session, delete it outright
    if (pendingSlug) {
      try {
        await apiPrivate.delete(`/sessions/${pendingSlug}/`);
      } catch (e) {
        console.warn("Failed to delete aborted session:", e);
      }
      setPendingSlug(null);
    }

    // 3️⃣ finally stop spinner and clear controller
    setProcessing(false);
    controllerRef.current = null;
  }

  async function startChat(overrideQ?: string) {
    const q = (overrideQ ?? question).trim();
    if (!q || outOfQuota) return;

    // If we're already processing, stop it first
    if (processing) {
      await stopProcessing();
      // Add a small delay to ensure cleanup is complete
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    const ctrl = new AbortController();
    controllerRef.current = ctrl;
    setProcessing(true);

    try {
      // 1️⃣ create session
      const { data: { slug } } = await apiPrivate.post<{ slug: string }>(
        "/sessions/create/",
        {
                    question: q,
                    advisor_name: advisorName,   // "immigration", "grant", …
                    country:      countryName,   // "USA", "CANADA", …
                  },
        { signal: ctrl.signal }
      );
      setPendingSlug(slug);

      // 2️⃣ stream generation
      const token = document.cookie.match(/(?:^|; )token=([^;]+)/)?.[1];
      const base = process.env.NEXT_PUBLIC_API_BASE || "";
      const res = await fetch(`${base}/sessions/${slug}/stream/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({ question: q }),
        credentials: "include",
        signal: ctrl.signal,
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      if (!res.body) {
        throw new Error("No streaming body");
      }

      const reader = res.body.getReader();
      const dec = new TextDecoder();
      let done = false;

      while (!done) {
        try {
          const { value, done: rd } = await reader.read();
          done = rd;
          if (value) {
            // Just consume the chunks without updating UI
            dec.decode(value);
          }
        } catch (err: any) {
          if (err.name === "AbortError" || err.code === "ERR_CANCELED") {
            // If aborted, clean up and return without navigating
            await stopProcessing(); // Use the existing cleanup function
            return; // Exit early on abort
          }
          throw err; // Re-throw other errors
        }
      }

      // Only navigate if we completed the entire stream
      router.push(`/library/${slug}`);
    } catch (err: any) {
      const isAbort = ["AbortError", "CanceledError"].includes(err.name) || err.code === "ERR_CANCELED";
      if (!isAbort) {
        console.error("startChat errored:", err);
        await stopProcessing(); // Use the existing cleanup function
      }
    } finally {
      if (!controllerRef.current) { // Only reset if we're not still processing
        setProcessing(false);
      }
    }
  }

  return (
    <div className="flex bg-[#fcfbf7] min-h-screen">
      <ResponsiveSidebar />
      <main className="flex-1 flex flex-col">
        <div className="flex-1 flex flex-col justify-center items-center p-8">
          <h1 className="text-5xl font-base text-center mb-8" style={{ fontFamily: "Georgia, serif" }}>
            Expertaihub
          </h1>
          <div
            ref={containerRef}
            className="relative w-full max-w-2xl mx-auto"
            onBlur={e => {
              if (!containerRef.current?.contains(e.relatedTarget as Node)) {
                setShowSug(false);
              }
            }}
          >
            <form
  onSubmit={e => { e.preventDefault(); startChat(); }}
  className="mt-auto sticky bottom-0 p-2 z-10 bg-[#fcfbf7] dark:bg-gray-900"
>
  <div className="w-full max-w-3xl mx-auto">
    <div className="flex flex-col bg-[#fcfbf7] dark:bg-[#2A2C3E] border border-gray-600 dark:border-gray-700 rounded-2xl p-4">
      <textarea
        rows={1}
        className="w-full bg-transparent text-gray-900 dark:text-gray-100 placeholder-gray-600 dark:placeholder-gray-500 resize-none overflow-y-auto max-h-36 focus:outline-none scrollbar-thin scrollbar-thumb-gray-700 dark:scrollbar-thumb-gray-900"
        placeholder={placeholder}
        value={question}
        onChange={e => setQuestion(e.target.value)}
        onFocus={() => setShowSug(true)}
        disabled={processing}
        onInput={e => {
          const ta = e.currentTarget;
          ta.style.height = "auto";
          ta.style.height = `${ta.scrollHeight}px`;
        }}
        onKeyDown={e => {
               if (e.key === "Enter" && !e.shiftKey) {
                 e.preventDefault();
                 startChat();
               }
             }}
      />

      <div className="flex justify-between items-center mt-4">
        <div className="text-sm text-gray-600">
          🔢 {used} / {limit} used this month
          {outOfQuota && (
            <div className="mt-1 text-red-600">
              You've reached your limit.{" "}
              <a href="/pro" className="underline">
                Upgrade to Pro
              </a>
            </div>
          )}
        </div>

        <div className="flex items-center space-x-4">
          <div className="relative inline-flex flex-col items-center group">
            <button
              type="button"
              disabled={processing}
              className="p-1 rounded text-gray-600 hover:text-gray-900"
            >
              <Mic className="w-5 h-5 cursor-pointer" />
            </button>
            <span className="absolute bottom-full mb-1 left-1/2 transform -translate-x-1/2 whitespace-nowrap bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100">
              Microphone
            </span>
          </div>

          {processing ? (
            <div className="relative inline-flex flex-col items-center group">
              <button
                type="button"
                onClick={stopProcessing}
                className="p-1 rounded text-red-600 hover:text-red-800"
              >
                <StopCircle className="w-6 h-6 cursor-pointer" />
              </button>
              <span className="absolute bottom-full mb-1 left-1/2 transform -translate-x-1/2 whitespace-nowrap bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100">
                Stop streaming
              </span>
            </div>
          ) : (
            <div className="relative inline-flex flex-col items-center group">
              <button
                type="submit"
                disabled={!question.trim()}
                className="p-1 rounded text-gray-600 hover:text-gray-900"
              >
                <Send className="w-5 h-5 cursor-pointer" />
              </button>
              <span className="absolute bottom-full mb-1 left-1/2 transform -translate-x-1/2 whitespace-nowrap bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100">
                Send question
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  </div>
</form>

            {showSug && (
              <ul className="absolute left-0 right-0 mt-1 bg-[#fcfbf7] border border-t-0 border-gray-300 rounded-b-xl z-20 overflow-visible">
                {filtered.map(s => (
                  <li
                    key={s}
                    className="px-6 py-3 hover:bg-gray-200 cursor-pointer flex items-center justify-between"
                    onMouseDown={() => { setQuestion(s); setShowSug(false); startChat(s); }}
                  >
                    <div className="flex items-center space-x-2">
                      <Search className="w-4 h-4 text-gray-800" />
                      <span>{s}</span>
                    </div>
                    <ArrowUpLeft className="w-4 h-4 text-gray-800" />
                  </li>
                ))}
                <li
                  className="px-6 py-4 bg-gradient-to-r from-yellow-100 to-yellow-200 rounded-b-xl cursor-pointer hover:from-yellow-200 hover:to-yellow-300 flex items-center justify-between"
                  onMouseDown={() => { setShowSug(false); startChat(); }}
                >
                  <div className="flex items-center space-x-2">
                    <Star className="w-4 h-4 text-yellow-600" />
                    <span className="font-semibold text-yellow-800">Discover Pro Features</span>
                  </div>
                  <button className="bg-yellow-600 text-white px-3 py-1 rounded-full flex items-center space-x-1 hover:bg-yellow-700">
                    <span>Upgrade to Pro</span>
                  </button>
                </li>
              </ul>
            )}

            <div className="mt-8 w-full p-6 bg-gradient-to-r from-blue-50 to-blue-200 border border-blue-200 rounded-xl text-center shadow-md">
              <h2 className="text-2xl font-semibold text-blue-700 mb-2 flex items-center justify-center space-x-2">
                <span>Upgrade to Pro</span>
              </h2>
              <p className="text-blue-800 mb-4">
                Unlock advanced features, priority support, and exclusive insights!
              </p>
              <button className="px-6 py-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition cursor-pointer">
                Go Pro Now
              </button>
            </div>
          </div>
        </div>

        <footer className="py-4 text-center space-x-6 text-sm text-gray-600">
          <a href="/pro" className="hover:underline">Pro</a>
          <a href="/blog" className="hover:underline">Blog</a>
          <a href="/privacy" className="hover:underline">Privacy</a>
        </footer>
      </main>
    </div>
  );
}