// src/app/home/page.tsx
"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Send, Mic, Search, ArrowUpLeft, Star, StopCircle } from "lucide-react";
import apiPrivate from "@/lib/apiprivate";
import ResponsiveSidebar from "@/components/ResponsiveSidebar";

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
  const [advisorName, setAdvisor] = useState("...");
  const [countryName, setCountry] = useState("...");
  const [usage, setUsage] = useState<{ used: number; limit: number }>({ used: 0, limit: 15 });
  const [pendingSlug, setPendingSlug] = useState<string | null>(null);   // ← track the slug
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);
  const controllerRef = useRef<AbortController | null>(null);

  const outOfQuota = usage.used >= usage.limit;

  useEffect(() => {
    apiPrivate.get<{ name: string }>("/advisor/") 
      .then(r => setAdvisor(r.data.name))
      .catch(() => setAdvisor("immigration"));
    apiPrivate.get<{ name: string }>("/country/")
      .then(r => setCountry(r.data.name))
      .catch(() => setCountry("USA"));
    apiPrivate.get<{ count: number }>("/monthly-usage/")
      .then(r => setUsage(us => ({ ...us, used: r.data.count })))
      .catch(() => {});
  }, []);

  // abort on unmount
  useEffect(() => () => controllerRef.current?.abort(), []);

  const placeholder = `Ask anything about immigration in usa …`;
  const filtered = DEFAULT_SUGGESTIONS.filter(s =>
    s.toLowerCase().includes(question.toLowerCase())
  );

  async function startChat(overrideQ?: string) {
    const q = (overrideQ ?? question).trim();
    if (!q || outOfQuota) return;

    const ctrl = new AbortController();
    controllerRef.current = ctrl;
    setProcessing(true);

    try {
      // 1️⃣ create session
      const { data: { slug } } = await apiPrivate.post<{ slug: string }>(
        "/sessions/create/",
        { question: q, country: "+1" },
        { signal: ctrl.signal }
      );
      setPendingSlug(slug);  // ← remember it

      // 2️⃣ fire off stream
      await apiPrivate.post(
        `/sessions/${slug}/stream/`,
        { question: q },
        { signal: ctrl.signal }
      );

      router.push(`/library/${slug}`);
    } catch (err: any) {
      const isAbort = ["AbortError","CanceledError"].includes(err.name) || err.code === "ERR_CANCELED";
      if (!isAbort) console.error("startChat errored:", err);
    } finally {
      setProcessing(false);
      controllerRef.current = null;
    }
  }

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

    // 3️⃣ refresh usage so aborted session doesn’t count
    try {
      const { data } = await apiPrivate.get<{ count: number }>("/monthly-usage/");
      setUsage(u => ({ ...u, used: data.count }));
    } catch {}

    // 4️⃣ finally stop spinner
    setProcessing(false);
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
            className="relative w-full max-w-xl"
            onBlur={e => {
              if (!containerRef.current?.contains(e.relatedTarget as Node)) {
                setShowSug(false);
              }
            }}
          >
            <form
              onSubmit={e => { e.preventDefault(); startChat(); }}
              className="flex items-center bg-[#fcfbf7] border border-gray-600 rounded-xl overflow-visible h-16 w-full"
            >
              <input
                type="text"
                className="flex-1 px-4 py-3 text-base placeholder-gray-400 bg-[#fcfbf7] focus:outline-none"
                placeholder={placeholder}
                value={question}
                onChange={e => setQuestion(e.target.value)}
                onFocus={() => setShowSug(true)}
                disabled={processing}
              />
              <div className="flex items-center space-x-4 pr-4">
                <div className="relative group">
                  <button type="button" disabled={processing} className="text-gray-600 hover:text-gray-900">
                    <Mic className="w-5 h-5 cursor-pointer" />
                  </button>
                  <span className="absolute bottom-full mb-1 left-1/2 transform -translate-x-1/2 whitespace-nowrap bg-gray-800 text-white text-xs rounded py-1 px-2 opacity-0 group-hover:opacity-100">
                    Microphone
                  </span>
                </div>
                {processing ? (
                  <div className="relative group">
                    <button type="button" onClick={stopProcessing} className="text-red-600 hover:text-red-800">
                      <StopCircle className="w-6 h-6 cursor-pointer" />
                    </button>
                    <span className="absolute bottom-full mb-1 left-1/2 transform -translate-x-1/2 whitespace-nowrap bg-gray-800 text-white text-xs rounded py-1 px-2 opacity-0 group-hover:opacity-100">
                      Stop streaming
                    </span>
                  </div>
                ) : (
                  <div className="relative group">
                    <button type="submit" disabled={!question.trim()} className="text-gray-600 hover:text-gray-900">
                      <Send className="w-5 h-5 cursor-pointer" />
                    </button>
                    <span className="absolute bottom-full mb-1 left-1/2 transform -translate-x-1/2 whitespace-nowrap bg-gray-800 text-white text-xs rounded py-1 px-2 opacity-0 group-hover:opacity-100">
                      Send question
                    </span>
                  </div>
                )}
              </div>
            </form>

            <div className="mt-2 text-sm text-gray-600 text-center">
              🔢 {usage.used} / {usage.limit} used this month
            </div>
            {outOfQuota && (
              <div className="mt-1 text-red-600 text-sm text-center">
                You’ve reached your monthly limit. <a href="/pro" className="underline">Upgrade to Pro</a> to continue.
              </div>
            )}

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
