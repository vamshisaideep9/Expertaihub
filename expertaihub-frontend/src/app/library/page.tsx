"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Loader2,
  BookOpen,
  Search,
  MoreHorizontal,
  Clock,
  Trash2,
  Pin,
  PinOff,
  Sliders,
  Archive,
  StickyNote,
  X,
} from "lucide-react";
import ResponsiveSidebar from "@/components/ResponsiveSidebar";
import{ MarkdownRenderer}from "@/components/MarkdownRenderer";
import apiPrivate from "@/lib/apiprivate";

// Helpers
function parseISO(dateString?: string): Date {
  return dateString
    ? new Date(dateString.replace(/\.\d+/, ""))
    : new Date();
}
function timeAgo(dateString?: string): string {
  const date = parseISO(dateString);
  const diff = Date.now() - date.getTime();
  const s = Math.floor(diff / 1000),
        m = Math.floor(s / 60),
        h = Math.floor(m / 60),
        d = Math.floor(h / 24);
  if (s < 60) return "just now";
  if (m < 60) return m === 1 ? "1 minute ago" : `${m} minutes ago`;
  if (h < 24) return h === 1 ? "1 hour ago"   : `${h} hours ago`;
  if (d < 7)  return d === 1 ? "1 day ago"    : `${d} days ago`;
  if (d < 30) {
    const w = Math.floor(d / 7);
    return w === 1 ? "1 week ago" : `${w} weeks ago`;
  }
  if (d < 365) {
    const mo = Math.floor(d / 30);
    return mo === 1 ? "1 month ago" : `${mo} months ago`;
  }
  const y = Math.floor(d / 365);
  return y === 1 ? "1 year ago" : `${y} years ago`;
}

type Message = {
  id: number;
  session: number;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
};

type Session = {
  slug: string;
  notes: string;
  pinned: boolean;
  archived: boolean;
  updated: string;
  completed: boolean; 
  advisor_detail: { name: string };
  country_detail: { name: string; code: string };
  messages: Message[];
};

export default function LibraryPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading]   = useState(true);

  const router = useRouter();

  // UI state for filters/search
  const [searchTerm,   setSearchTerm]   = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const [onlyPinned,   setOnlyPinned]   = useState(false);
  const [sortOrder,    setSortOrder]    = useState<"newest"|"oldest">("newest");
  const [dateFrom,     setDateFrom]     = useState("");
  const [dateTo,       setDateTo]       = useState("");
  const [filterOpen,   setFilterOpen]   = useState(false);
  const filterRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    apiPrivate.get<Session[]>("/sessions/").then(res => {
      setSessions(res.data.filter(s => s.completed));
      setLoading(false);
    });
  }, []);

  // Close filter popup on outside click
  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (filterRef.current && !filterRef.current.contains(e.target as Node)) {
        setFilterOpen(false);
      }
    }
    if (filterOpen) document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [filterOpen]);

  // Row menus & notes state
  const [menuOpen,     setMenuOpen]    = useState<Record<string,boolean>>({});
  const [showAbsolute, setShowAbsolute]= useState<Record<string,boolean>>({});
  const [notesOpen,    setNotesOpen]   = useState<Record<string,boolean>>({});
  const [notesText,    setNotesText]   = useState<Record<string,string>>({});

  // Close any open row menu on outside click
  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (!(e.target as Element).closest(".menu-wrapper")) {
        setMenuOpen({});
      }
    }
    if (Object.values(menuOpen).some(v => v)) {
      document.addEventListener("mousedown", onClick);
    }
    return () => document.removeEventListener("mousedown", onClick);
  }, [menuOpen]);

  const toggleMenu  = (slug: string) => setMenuOpen(p => ({ ...p, [slug]: !p[slug] }));
  const toggleDate  = (slug: string) => setShowAbsolute(p => ({ ...p, [slug]: !p[slug] }));
  const toggleNotes = (slug: string) => setNotesOpen(p => ({ ...p, [slug]: !p[slug] }));

  // CRUD handlers
  const handlePin = async (slug:string,pinned:boolean) => {
    await apiPrivate.post(`/sessions/${slug}/${pinned?"unpin":"pin"}/`);
    setSessions(s => s.map(x => x.slug===slug ? { ...x, pinned: !pinned } : x));
  };
  const handleArchive = async (slug:string,archived:boolean) => {
    await apiPrivate.post(`/sessions/${slug}/${archived?"unarchive":"archive"}/`);
    setSessions(s => s.map(x => x.slug===slug ? { ...x, archived: !archived } : x));
  };
  const handleDelete = async (slug:string) => {
    await apiPrivate.delete(`/sessions/${slug}/`);
    setSessions(s => s.filter(x => x.slug!==slug));
  };
  const handleSaveNotes = async (slug:string) => {
    await apiPrivate.patch(`/sessions/${slug}/update_metadata/`, { notes: notesText[slug] || "" });
    setSessions(s => s.map(x => x.slug===slug ? { ...x, notes: notesText[slug]||"" } : x));
    setNotesOpen({});
  };

  // Apply filters, sort, search
  const filtered = sessions
    .filter(s => s.completed)
    .filter(s => showArchived ? s.archived : !s.archived)
    .filter(s => onlyPinned   ? s.pinned   : true)
    .filter(s => {
      if (dateFrom && parseISO(s.updated) < new Date(dateFrom)) return false;
      if (dateTo) {
        const d = new Date(dateTo); d.setHours(23,59,59,999);
        if (parseISO(s.updated) > d) return false;
      }
      return true;
    })
    .sort((a,b) => {
      if (a.pinned !== b.pinned) return a.pinned ? -1 : 1;
      const ta = parseISO(a.updated).getTime(),
            tb = parseISO(b.updated).getTime();
      return sortOrder==="newest" ? tb-ta : ta-tb;
    })
    .filter(s => {
      const t = searchTerm.toLowerCase();
      const firstQ = s.messages[0]?.content.toLowerCase() || "";
      const firstA = s.messages[1]?.content.toLowerCase() || "";
      return firstQ.includes(t) || firstA.includes(t);
    });

  // Notes modal data
  const openSlug     = Object.entries(notesOpen).find(([_,v])=>v)?.[0] || null;
  const openNoteText = openSlug
    ? notesText[openSlug] ?? sessions.find(s=>s.slug===openSlug)?.notes ?? ""
    : "";

  return (
    <div className="flex min-h-screen bg-[#fcfbf7]">
      <ResponsiveSidebar />

      <main className="ml-10 flex-1 flex flex-col">
        {/* HEADER */}
        <div className="sticky top-0 z-10 bg-[#fcfbf7] border-b border-gray-200 h-[60px] flex items-center">
          <div className="max-w-5xl w-full mx-auto px-6 flex items-center justify-between">
            <h1 className="flex items-center text-3xl font-serif text-gray-900">
              <BookOpen className="w-6 h-6 mr-2" /> Library
            </h1>
            <div className="flex items-center space-x-4">
              {/* Search */}
              <div className="relative w-full max-w-sm">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-800 w-5 h-5" />
                <input
                  className="w-full pl-12 pr-40 h-10 bg-[#fcfbf7] border border-gray-600 rounded-full focus:ring-0 focus:border-gray-300"
                  placeholder="Search your chats…"
                  value={searchTerm}
                  onChange={e => setSearchTerm(e.target.value)}
                />
              </div>
              {/* Filters */}
              <div className="relative inline-block" ref={filterRef}>
                <Sliders
                  className="w-6 h-6 text-gray-700 hover:text-gray-900 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                  onClick={()=>setFilterOpen(o=>!o)}
                />
                {filterOpen && (
                  <div className="absolute right-0 mt-2 w-64 bg-[#fcfbf7] border border-gray-200 rounded-2xl shadow-lg p-6 space-y-4 z-30">
                    <label className="flex items-center gap-2">
                      <input type="checkbox" checked={showArchived} onChange={()=>setShowArchived(a=>!a)} className="h-4 w-4"/>
                      <span className="text-sm">Show archived</span>
                    </label>
                    <label className="flex items-center gap-2">
                      <input type="checkbox" checked={onlyPinned} onChange={()=>setOnlyPinned(p=>!p)} className="h-4 w-4"/>
                      <span className="text-sm">Only pinned</span>
                    </label>
                    <div className="space-y-1">
                      <span className="text-xs">Date from</span>
                      <input type="date" value={dateFrom} onChange={e=>setDateFrom(e.target.value)} className="w-full text-sm border rounded px-2 py-1"/>
                    </div>
                    <div className="space-y-1">
                      <span className="text-xs">Date to</span>
                      <input type="date" value={dateTo} onChange={e=>setDateTo(e.target.value)} className="w-full text-sm border rounded px-2 py-1"/>
                    </div>
                    <div className="space-y-1">
                      <span className="text-xs">Sort by</span>
                      <select value={sortOrder} onChange={e=>setSortOrder(e.target.value as any)} className="w-full text-sm border rounded px-2 py-1">
                        <option value="newest">Newest first</option>
                        <option value="oldest">Oldest first</option>
                      </select>
                    </div>
                    {/* Clear filters button */}
                    <div className="mt-4 text-right">
                      <button
                        className="text-sm text-blue-600 hover:underline"
                        onClick={() => {
                          setShowArchived(false);
                          setOnlyPinned(false);
                          setDateFrom("");
                          setDateTo("");
                          setSortOrder("newest");
                        }}
                      >
                        Clear filters
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* LIST */}
        <div className="flex-1 overflow-auto mt-2">
          <div className="max-w-5xl mx-auto px-6">
            {loading ? (
              <div className="flex items-center gap-2 text-gray-500">
                <Loader2 className="animate-spin w-5 h-5"/> Loading…
              </div>
            ) : sessions.length === 0 ? (
              <div className="text-center text-gray-500 py-10">
                No chats available yet.<br/>
                <Link href="/home" className="text-blue-600 hover:underline">
                  Start a new conversation
                </Link>
              </div>
            ) : filtered.length === 0 ? (
              <div className="text-center text-gray-500 py-10">
                Oops! No chats match your filters.<br/>
                <button
                  className="text-blue-600 hover:underline cursor-pointer"
                  onClick={() => {
                    setShowArchived(false);
                    setOnlyPinned(false);
                    setDateFrom("");
                    setDateTo("");
                    setSortOrder("newest");
                  }}
                >
                  Clear filters
                </button>
              </div>
            ) : (
              <ul>
                {filtered.map((s, idx) => {
                  const abs   = parseISO(s.updated).toLocaleString();
                  const rel   = timeAgo(s.updated);
                  const label = showAbsolute[s.slug] ? abs : rel;

                  const firstQ = s.messages[0]?.content ?? "";
                  const firstA = s.messages[1]?.content ?? "";

                  const advisorName = s.advisor_detail?.name ?? "Unknown Advisor";
                  const countryCode = s.country_detail?.name?.toUpperCase() ?? "";

                  return (
                    <li
                      key={s.slug}
                      className={`flex items-start justify-between pb-4 mb-4 ${
                        idx < filtered.length - 1 ? "border-b border-gray-400" : ""
                      }`}
                    >
                      <div
                           className="flex-1 pr-4 cursor-pointer"
     onClick={() => router.push(`/library/${s.slug}/`)}
  >
                        <h2 className="flex items-center font-semibold text-gray-900 mb-1 line-clamp-2">
                          {s.pinned && <Pin className="w-4 h-4 mr-1"/>}
                          {firstQ}
                        </h2>
                       
                        <div className="text-sm text-gray-600 mb-2 line-clamp-2">
                          <MarkdownRenderer content={firstA}/>
                        </div>
                        
                        <div className="flex justify-between text-xs text-black">
                          <span>{advisorName}</span>
                          <span>{countryCode}</span>
                        </div>
                        <div className="mt-1 flex items-center text-xs text-gray-800 gap-1">
                          <Clock
                            className="w-3.5 h-3.5 cursor-pointer text-gray-900"
                            onClick={e => { e.preventDefault(); toggleDate(s.slug); }}
                          />
                          <span className="text-gray-900">{label}</span>
                        </div>
                      </div>
                      <div className="flex items-start space-x-2">
                        <StickyNote
                          className="w-5 h-5 text-gray-900 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                          onClick={() => toggleNotes(s.slug)}
                        />
                        <div className="relative menu-wrapper">
                          <MoreHorizontal
                            className="w-5 h-5 text-gray-900 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                            onClick={() => toggleMenu(s.slug)}
                          />
                          {menuOpen[s.slug] && (
                            <div className="absolute right-0 mt-2 w-40 bg-[#fcfbf7] border border-gray-200 rounded-2xl shadow-lg p-2 z-20">
                              <button
                                className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-gray-100 w-full"
                                onClick={e => { e.preventDefault(); handleArchive(s.slug, s.archived); }}
                              >
                                <Archive className="w-4 h-4"/>
                                {s.archived ? "Unarchive" : "Archive"}
                              </button>
                              <button
                                className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-gray-100 w-full"
                                onClick={e => { e.preventDefault(); handlePin(s.slug, s.pinned); }}
                              >
                                {s.pinned ? <PinOff className="w-4 h-4"/> : <Pin className="w-4 h-4"/>}
                                {s.pinned ? "Unpin" : "Pin"}
                              </button>
                              <button
                                className="flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-gray-100 w-full"
                                onClick={e => { e.preventDefault(); handleDelete(s.slug); }}
                              >
                                <Trash2 className="w-4 h-4"/>Delete
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </div>
      </main>

      {/* NOTES MODAL */}
      {openSlug && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
          <div className="bg-[#fcfbf7] border border-gray-300 rounded-2xl shadow-lg w-1/3 h-80 flex flex-col">
            <div className="flex justify-between items-center p-4 border-b border-gray-300">
              <span className="font-medium">Notes</span>
              <button className="p-2" onClick={() => setNotesOpen({})}>
                <X className="w-4 h-4 cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 rounded"/>
              </button>
            </div>
            <textarea
              className="flex-1 p-4  bg-[#fcfbf7] text-sm resize-none overflow-auto focus:outline-none"
              value={openNoteText}
              onChange={e => setNotesText(p => ({ ...p, [openSlug]: e.target.value }))}
              maxLength={1000}
              placeholder="Write your notes here…"
            />
            <div className="flex justify-between items-center p-4 border-t border-gray-300">
              <span className="text-xs text-gray-500">
                {(notesText[openSlug]?.length ?? sessions.find(s => s.slug === openSlug)?.notes.length ?? 0)}/1000
              </span>
              <button
                className="text-sm text-blue-600 hover:underline"
                onClick={() => handleSaveNotes(openSlug)}
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
