"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { FloatingMenu } from "@/components/FloatingMenu";
import { FeedbackModal, FeedbackValues } from "@/components/FeedBackModel";
import { useMonthlyUsage } from "@/hooks/useMonthlyUsage";          /* NEW */
import {
  useState,
  useEffect,
  useRef,
  FormEvent,
  useContext,
  useMemo,
} from "react";
import { useParams } from "next/navigation";
import {
  Mic,
  Send,
  StopCircle,
  ChevronDown,
  Brain,
  Ellipsis,
  Pencil,
  X,
  FileText,
  File,
  Trash2,
  Share,
  Lock,
  Link as LinkIcon,
  Check,
  ThumbsUp,
  ThumbsDown,
  Copy,
  CheckCircle,
  Flag,
  ArrowUp,
  ArrowLeft,
} from "lucide-react";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { RelatedQueries } from "@/components/RelatedQueries";
import ResponsiveSidebar from "@/components/ResponsiveSidebar";
import api from "@/lib/apiprivate";
import { UserContext } from "@/context/UserContext";

const avatarColors = [
  "bg-red-500",
  "bg-green-500",
  "bg-blue-500",
  "bg-yellow-500",
  "bg-purple-500",
  "bg-pink-500",
  "bg-indigo-500",
];
function getAvatarColor(name: string) {
  const hash = name
    .split("")
    .reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return avatarColors[hash % avatarColors.length];
}

type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
  html_content?: string;
  timestamp: string;
  user_reaction?: "like" | "dislike";
  user_feedback?: {
    reasons: string[];
    additional_comments: string
  };
  suggestions?: string[];
};

export default function ChatPage() {
  const router = useRouter();
  const { slug } = useParams();
  const searchParams = useSearchParams();

  /* ── toast ──────────────────────────────── */
  const [toastVisible, setToastVisible] = useState(false);
  const [toastMessage, setToastMessage] = useState("");
  useEffect(() => {
    if (!toastVisible) return;
    const id = setTimeout(() => setToastVisible(false), 3_000);
    return () => clearTimeout(id);
  }, [toastVisible]);

  /* ── user / session meta ────────────────── */
  const { user: currentUser, loading: userLoading } = useContext(UserContext);
  if (userLoading) return null;
  const [owner, setOwner] = useState<{ id: number; full_name: string }>(
    () =>
      currentUser
        ? { id: currentUser.id, full_name: currentUser.full_name }
        : { id: 0, full_name: "" }
  );
  const [updatedAt, setUpdatedAt] = useState<string>("");
  const [countryName, setCountryName] = useState("");
  const [advisorName, setAdvisorName] = useState("");
  const [sessionTitle, setSessionTitle] = useState("");
  const [shareOption, setShareOption] = useState<"private" | "link">("private");

  // Private‐session flow
  const [isPrivate, setIsPrivate] = useState(false);
  const [sessionChecked, setSessionChecked] = useState(false);
  const [accessRequested, setAccessRequested] = useState(false);

  // Chat history & streaming
  const [history, setHistory] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  // UI state
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownButtonRef = useRef<HTMLDivElement>(null);
  const dropdownMenuRef = useRef<HTMLDivElement>(null);
  const [moreOpen, setMoreOpen] = useState(false);
  const moreRef = useRef<HTMLDivElement>(null);
  const [shareOpen, setShareOpen] = useState(false);
  const shareRef = useRef<HTMLDivElement>(null);
  const [copied, setCopied] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editValue, setEditValue] = useState("");
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);

  // Per‐answer export dropdown
  const [openExportDropdownId, setOpenExportDropdownId] = useState<number | null>(null);
  const exportBtnRefs = useRef<Record<number, HTMLButtonElement | null>>({});

  const [openOptionsMenuId, setOpenOptionsMenuId] = useState<number | null>(null);
  const optionsBtnRefs = useRef<Record<number, HTMLButtonElement | null>>({});
  const optionsMenuRef = useRef<HTMLDivElement|null>(null);

  const [messageReactions, setMessageReactions] = useState<Record<number, 'like'|'dislike'>>({});

  const [feedbackOpen, setFeedbackOpen]             = useState(false);
  const [reportingMessageId, setReportingMessageId] = useState<number|null>(null);


  const [openReasonForId, setOpenReasonForId] = useState<number|null>(null);
// was it a like or dislike?
  const [pendingReactionType, setPendingReactionType] = useState<'like'|'dislike'|null>(null);
// which reason did they pick?
  const [selectedReason, setSelectedReason] = useState<string>('');
// only used if they pick "other"
  const [otherComment, setOtherComment] = useState<string>('');

  const [initialFeedback, setInitialFeedback] = useState<FeedbackValues>({
    reasons: [],
    comments: "",
  });

  const { used, limit, refresh: refreshUsage }= useMonthlyUsage(currentUser?.id ?? 0);
  const outOfQuota      = used >= limit;

  const [justSent, setJustSent] = useState(false);
  const [userScrolledUp, setUserScrolledUp] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const [editingMessageId, setEditingMessageId] = useState<number | null>(null)
const [editingContent, setEditingContent] = useState("")
  const editingTaRef                                = useRef<HTMLTextAreaElement>(null);
  const taRef      = useRef<HTMLTextAreaElement>(null);

  const [regeneratingId, setRegeneratingId] = useState<number | null>(null);

  useEffect(() => {
    const ta = editingTaRef.current;
    if (!ta) return;
    // reset & grow
    ta.style.height = "auto";
    ta.style.height = `${ta.scrollHeight}px`;
  }, [editingContent, editingMessageId]);

const lineClampCss = `
  .line-clamp-3 {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
`;

<style jsx global>{lineClampCss}</style>

// 1) User clicked "Edit"
function startEdit(m: Message) {
  setEditingMessageId(m.id)
  setEditingContent(m.content)
}

// 2) Cancel & revert
function cancelEdit() {
  setEditingMessageId(null)
  setEditingContent("")
}

const [expanded, setExpanded] = useState<number | null>(null);
const [copiedQ, setCopiedQ] = useState<number | null>(null);

const originalRef = useRef<HTMLDivElement>(null);

useEffect(() => {
  if (editingMessageId != null && originalRef.current && editingTaRef.current) {
    // read the question bubble's height
    const h = originalRef.current.getBoundingClientRect().height;
    // apply it to the textarea
    editingTaRef.current.style.height = `${h}px`;
  }
}, [editingMessageId]);

// 3) Save back to the server
// inside ChatPage component

async function saveEdit() {
  if (!slug || editingMessageId == null) return;

  try {
    // 1) Persist the updated question
    const { data: updatedQuestion } = await api.patch<Message>(
      `/sessions/${slug}/messages/${editingMessageId}/`,
      { content: editingContent }
    );

    // 2) Update both the question AND blank its assistant reply in one pass
    setHistory(old =>
      old.map((m, i) => {
        if (m.id === editingMessageId) {
          // replace the question
          return updatedQuestion;
        }
        // if right after that question, blank the assistant
        if (old[i - 1]?.id === editingMessageId && m.role === "assistant") {
          return { ...m, content: "", html_content: "" };
        }
        return m;
      })
    );

    // 3) Close the editor and show toast
    setEditingMessageId(null);
    setToastMessage("Regenerating response…");
    setToastVisible(true);
    setStreaming(true);

    // 4) Locate the stubId (assistant message right after your edited question)
    const stubMsg = history.find((m, i) =>
      history[i - 1]?.id === editingMessageId && m.role === "assistant"
    );
    const stubId = stubMsg?.id;
    if (stubId) {
      setRegeneratingId(stubId); // Set regeneratingId to show animation under edited question
    }

    // 5) Fire a single /stream/ POST using reply_to = stubId
    const token = document.cookie.match(/(?:^|; )token=([^;]+)/)?.[1];
    const base  = process.env.NEXT_PUBLIC_API_BASE || "";
    const res = await fetch(`${base}/sessions/${slug}/stream/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      credentials: "include",
      body: JSON.stringify({
        question: editingContent,
        reply_to: stubId,
      }),
    });
    if (!res.ok || !res.body) {
      throw new Error("Streaming failed");
    }

    // 6) Stream chunks back into that stub
    const reader = res.body.getReader();
    const dec    = new TextDecoder();
    let done = false;
    while (!done) {
      const { value, done: rd } = await reader.read();
      done = rd;
      if (value) {
        const chunk = dec.decode(value);
        setHistory(h =>
          h.map(m =>
            m.id === stubId
              ? { ...m, content: m.content + chunk }
              : m
          )
        );
      }
    }

    // 7) Finish up
    setStreaming(false);
    setRegeneratingId(null);
    setTimeout(() => setEditingMessageId(null), 0); // Clear regeneratingId when done
    setToastMessage("Message updated");
    setToastVisible(true);

  } catch (err) {
    console.error("Edit failed", err);
    setToastMessage("Failed to save edit");
    setToastVisible(true);
    setStreaming(false);
    setRegeneratingId(null); // Clear regeneratingId on error
  }
}

function handleChatScroll() {
  if (!chatContainerRef.current) return;
  const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
  setUserScrolledUp(scrollHeight - scrollTop - clientHeight > 50);
}

useEffect(() => {
  if (!userScrolledUp && chatContainerRef.current) {
    setTimeout(() => {
      chatContainerRef.current!.scrollTop = chatContainerRef.current!.scrollHeight;
    }, 0);
  }
}, [history]);

 







  // ——— Close native pop-overs on outside click ———
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        dropdownOpen &&
        !dropdownButtonRef.current?.contains(e.target as Node) &&
        !dropdownMenuRef.current?.contains(e.target as Node)
      ) {
        setDropdownOpen(false);
      }
      if (moreOpen && !moreRef.current?.contains(e.target as Node)) {
        setMoreOpen(false);
      }
      if (shareOpen && !shareRef?.current?.contains(e.target as Node)) {
        setShareOpen(false);
      }
      // Add check for options menu
      if (
        openOptionsMenuId !== null &&
        !Object.values(optionsBtnRefs.current).some(el => el?.contains(e.target as Node)) &&
        !optionsMenuRef.current?.contains(e.target as Node)
      ) {
        setOpenOptionsMenuId(null);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [dropdownOpen, moreOpen, shareOpen, shareRef, openOptionsMenuId]);

  // ——— Close export menus on outside click ———
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      const clickedOnAny = Object.values(exportBtnRefs.current).some(el =>
        el?.contains(e.target as Node)
      );
      if (!clickedOnAny && openExportDropdownId !== null) {
        setOpenExportDropdownId(null);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [openExportDropdownId]);


  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        openOptionsMenuId !== null &&
        optionsMenuRef.current &&
        !optionsMenuRef.current.contains(e.target as Node)
      ) {
        setOpenOptionsMenuId(null);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [openOptionsMenuId]);

  // ——— Auto-open share pop-over if URL has `?open_share=true` ———
  useEffect(() => {
    if (searchParams.get("open_share") === "true") {
      setShareOpen(true);
    }
  }, [searchParams]);

  // ——— Poll for approval on private shares ———
  useEffect(() => {
    if (!accessRequested || !slug) return;
    const iv = setInterval(async () => {
      try {
        await api.get(`/sessions/${slug}/`);
        window.location.reload();
      } catch {}
    }, 5000);
    return () => clearInterval(iv);
  }, [accessRequested, slug]);


  // ——— Fetch session metadata ———
  useEffect(() => {
    if (!slug) return;
    setSessionChecked(false);
    api
      .get<any>(`/sessions/${slug}/`)
      .then(r => {
        setSessionTitle(r.data.title);
        setCountryName(r.data.country_detail.name);
        setAdvisorName(r.data.advisor_detail.name);
        setShareOption(r.data.share_option);
        setOwner(r.data.owner_detail);
        setUpdatedAt(r.data.updated);
        setIsPrivate(false);
      })
      .catch(err => {
        if (err.response?.status === 403) setIsPrivate(true);
        else console.error(err);
      })
      .finally(() => setSessionChecked(true));
  }, [slug]);

  // ——— Fetch chat history ———
  async function fetchHistory() {
    if (!slug) return;
    try {
      const res = await api.get<Message[]>(`/sessions/${slug}/messages/`);
      const msgs = res.data;
      setHistory(msgs);
  
      // build a map of messageId → user_reaction
      const reacts: Record<number, "like" | "dislike"> = {};
      msgs.forEach((m) => {
        if (m.user_reaction === "like" || m.user_reaction === "dislike") {
          reacts[m.id] = m.user_reaction;
        }
      });
      setMessageReactions(reacts);
  
      endRef.current?.scrollIntoView({ behavior: "auto" });
    } catch (e) {
      console.error(e);
    }
  }
  useEffect(() => {
    if (slug && sessionChecked && !isPrivate) fetchHistory();
  }, [slug, sessionChecked, isPrivate]);



  // ——— Always scroll to bottom on new history ———
  useEffect(() => {
    if (streaming || regeneratingId !== null) return;
    const last = history[history.length - 1];
    if (last?.role === "user") {
      endRef.current?.scrollIntoView({ behavior: "auto" });
    }
  }, [history, streaming, regeneratingId]);

  // ——— Stop the streaming response & clean up ———
  async function stopStream() {
    controllerRef.current?.abort();
    setStreaming(false);
    controllerRef.current = null;

    // remove stub messages
    setHistory(h => {
      const n = h.length;
      if (n >= 2 && h[n - 2].role === "user" && h[n - 1].role === "assistant") {
        return h.slice(0, n - 2);
      }
      return h;
    });

    try {
      const res = await api.get<Message[]>(`/sessions/${slug}/messages/`);
      const persisted = res.data;
      const lastUser = [...persisted].reverse().find(m => m.role === "user");
      if (lastUser) {
        await api.delete(`/sessions/${slug}/messages/${lastUser.id}/`);
      }
      const fresh = await api.get<Message[]>(`/sessions/${slug}/messages/`);
      setHistory(fresh.data);
    } catch (err) {
      console.error("Could not clean up stopped message:", err);
    }
  }

  // ——— Fetch usage ———

  const [copiedUnderChat, setCopiedUnderChat] = useState(false);
  const [sharedUnderChat, setSharedUnderChat] = useState(false);
  function handleSuggestionClick(text: string) {
    setInput(text);
    void sendMessage(null, text);
  }

  useEffect(() => {
    if (justSent || streaming) {
      endRef.current?.scrollIntoView({ behavior: "smooth" });
      setJustSent(false);
    }
  }, [history]);
  

  // ——— Send & stream logic ———
  async function sendMessage(e?: FormEvent | null, overrideText?: string) {
    e?.preventDefault();
    const text = (overrideText ?? input).trim();
    if (!text || !slug) return;

    let aborted = false;

    // If out of quota, just show a local "limit reached" stub
    if (outOfQuota) {
      const ts = new Date().toISOString();
      const uid = Date.now();
      setHistory((h) => [
        ...h,
        { id: uid, role: "user", content: text, timestamp: ts },
        {
          id: uid + 1,
          role: "assistant",
          content: "You've reached your monthly limit. Upgrade to Pro to continue.",
          timestamp: ts,
        },
      ]);
      setInput("");
      return;
    }

    // 1) Add user stub + empty assistant stub (will fill in as chunks arrive)
    const ts = new Date().toISOString();
    const uid = Date.now();
    setHistory((h) => [
      ...h,
      { id: uid, role: "user", content: text, timestamp: ts },
      { id: uid + 1, role: "assistant", content: "", timestamp: ts },
    ]);
    setInput("");

    // 2) Start streaming
    const ctrl = new AbortController();
    controllerRef.current = ctrl;
    setStreaming(true);

    try {
      const token = document.cookie.match(/(?:^|; )token=([^;]+)/)?.[1];
      const base = process.env.NEXT_PUBLIC_API_BASE || "";
      const res = await fetch(`${base}/sessions/${slug}/stream/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({ question: text }),
        credentials: "include",
        signal: ctrl.signal,
      });
      if (!res.ok) {
        // on error, just reload the full history
        setTimeout(fetchHistory, 5000);
        return;
      }
      if (!res.body) throw new Error("No streaming body");

      const reader = res.body.getReader();
      const dec = new TextDecoder();
      let done = false;
      let finalSuggestions: string[] | null = null;

      while (!done) {
        const { value, done: rd } = await reader.read();
        done = rd;
        if (value) {
          const chunk = dec.decode(value);
          if (done) {
            const trimmed = chunk.trimStart();
            try {
              const obj = JSON.parse(trimmed);
              if (Array.isArray(obj.suggestions)) {
                finalSuggestions = obj.suggestions as string[];
                continue;
              }
            } catch {}
          }
          // Append each chunk onto the last assistant stub
          setHistory((h) => {
            const last = h[h.length - 1];
            return [...h.slice(0, -1), { ...last, content: last.content + chunk }];
          });
        }
      }

      if (finalSuggestions) {
        setHistory(h => {
          const last = h[h.length - 1];
          return [...h.slice(0, -1), { ...last, suggestions: finalSuggestions }];
        });
      }
    } catch (err: any) {
      if (err.name === "AbortError") {
               // + user pressed "Stop"
               aborted = true;
             } else {
               console.error(err);
             }
    } finally {
      setStreaming(false);
      controllerRef.current = null;
      // Once streaming is done, re-fetch so that html_content is filled in
      setJustSent(true);
      fetchHistory();
      if (!aborted) {
               void refreshUsage();
             }
    }
  }

  const formatDate = (iso: string) => {
        const d = new Date(iso);
        // e.g. "May 25, 2025" → remove the space before the day:
        return d
          .toLocaleDateString("en-US", { month: "short", day: "2-digit", year: "numeric" })
          .replace(" ", "");
      };

  // ——— Share under chat ———
  async function handleShareUnderChat() {
    if (!slug) return;
    try {
      await api.patch(`/sessions/${slug}/share_option/`, { share_option: "link" });
    } catch {}
    const url = `${window.location.origin}/library/${slug}`;
    await navigator.clipboard.writeText(url);
    setSharedUnderChat(true);
    setTimeout(() => setSharedUnderChat(false), 2000);
    setToastMessage("Link copied. Paste to share.");
    setToastVisible(true);
  }

  // ——— Request access ———
  async function requestAccess() {
    if (!slug) return;
    try {
      await api.get(`/sessions/${slug}/`);
    } catch (err: any) {
      if (err.response?.status === 403) {
        setAccessRequested(true);
      } else {
        console.error(err);
        alert("Failed to request access");
      }
    }
  }

  // ——— Change share setting ———
  async function handleShareOption(option: "private" | "link") {
    if (!slug) return;
    try {
      await api.patch(`/sessions/${slug}/share_option/`, { share_option: option });
      setShareOption(option);
    } catch {
      alert("Could not update share setting");
    }
  }

  // ——— Edit title ———
  function openEditModal() {
    setEditValue(sessionTitle);
    setMoreOpen(false);
    setEditOpen(true);
  }
  async function saveTitle() {
    if (!slug) return;
    try {
      await api.patch(`/sessions/${slug}/update_metadata/`, { title: editValue });
      setSessionTitle(editValue);
      setEditOpen(false);
    } catch {
      alert("Could not save title");
    }
  }

  // ——— Delete session ———
  const isOwner = currentUser ? owner.id === currentUser.id : false;
  function openDeleteConfirm() {
    setMoreOpen(false);
    setConfirmDeleteOpen(true);
  }
  function closeDeleteConfirm() {
    setConfirmDeleteOpen(false);
  }
  async function deleteSession() {
    if (!slug) return;
    try {
      await api.delete(`/sessions/${slug}/`);
      router.push("/home");
    } catch {
      alert("Could not delete session");
    }
  }

  // ——— Copy link ———
  async function copyLink() {
    await navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setShareOpen(false);
  }

  // ——— Choose display user ———
  const displayUser = useMemo(
    () =>
      owner.id !== 0 && currentUser && owner.id !== currentUser.id
        ? owner
        : currentUser || owner,
    [owner, currentUser]
  );

  // ——— Placeholder exports ———
  async function exportAsPdf() {
    if (!slug) return;
    try {
      const res = await api.get<Blob>(`/sessions/${slug}/export/pdf/`, {
        responseType: "blob",
      });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${slug}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error(err);
      alert(err.message || "Failed to export PDF");
    }
  }
  async function exportAsDocx() {
    if (!slug) return;
    try {
      const res = await api.get<Blob>(`/sessions/${slug}/export/docx/`, {
        responseType: "blob",
      });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${slug}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error(err);
      alert(err.message || "Failed to export DOCX");
    }
  }

  function toggleExportMenu(id: number) {
    setOpenExportDropdownId(prev => (prev === id ? null : id));
  }

  // ——— Per-answer export ———
  async function exportAnswerPdf(m: Message) {
    if (!slug) return;
    try {
      const res = await api.get<Blob>(
        `/sessions/${slug}/messages/${m.id}/export/pdf/`,
        { responseType: "blob" }
      );
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `answer-${m.id}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert("Failed to export PDF");
    } finally {
      setOpenExportDropdownId(null);
    }
  }
  async function exportAnswerDocx(m: Message) {
    if (!slug) return;
    try {
      const res = await api.get<Blob>(
        `/sessions/${slug}/messages/${m.id}/export/docx/`,
        { responseType: "blob" }
      );
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `answer-${m.id}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert("Failed to export DOCX");
    } finally {
      setOpenExportDropdownId(null);
    }
  }

  // 1) Remove the old handleReact
//    which just opened the box immediately…

// 2) Replace it with this:
async function handleReact(messageId: number, reaction: 'like' | 'dislike') {
  if (!slug) return;

  try {
    // 1️⃣ update the reaction on the server first
    await api.post(
      `/sessions/${slug}/messages/${messageId}/react/`,
      { reaction }
    );
    // 2️⃣ reflect it in local UI
    setMessageReactions(prev => ({
      ...prev,
      [messageId]: reaction
    }));
    // 3️⃣ now open the reason picker
    setOpenReasonForId(messageId);
    setPendingReactionType(reaction);
    setSelectedReason('');
    setOtherComment('');
  } catch (err) {
    console.error("React error:", err);
    setToastMessage("Could not record reaction");
    setToastVisible(true);
  }
}


async function submitReaction(feedback?: { reason?: string; comments?: string }) {
  if (!slug || openReasonForId == null || pendingReactionType == null) return;

  try {
    // 1) hit the exact same endpoint your other calls use:
    const res = await api.post(
      `/sessions/${slug}/messages/${openReasonForId}/react/`,
      {
        reaction: pendingReactionType,
        // only send these if they exist
        ...(feedback?.reason    && { reason:  feedback.reason    }),
        ...(feedback?.comments  && { comment: feedback.comments  }),
      }
    );

    // 2) read back the fields your serializer returns:
    const { my_reaction, my_reason, my_comment } = res.data;

    // 3) update your local history so the UI re-renders
    setHistory(h =>
      h.map(msg =>
        msg.id === openReasonForId
          ? {
              ...msg,
              user_reaction: my_reaction,
              // if you'd like, embed these into user_feedback:
              user_feedback: { reasons: my_reason ? [my_reason] : [], additional_comments: my_comment }
            }
          : msg
      )
    );

    // 4) close the picker
    setOpenReasonForId(null);
    setPendingReactionType(null);
    setSelectedReason('');
    setOtherComment('');

  } catch (err) {
    console.error("Error submitting reaction:", err);
    setToastMessage("Could not save your reason");
    setToastVisible(true);
  }
}


  // new: copy-to-clipboard handler
  async function handleCopyAnswer(content: string) {
    const cleaned = content.replace(/[^A-Za-z0-9 \-\,\.]/g, "");
    try {
      await navigator.clipboard.writeText(cleaned);
      setCopiedUnderChat(true);
      setTimeout(() => setCopiedUnderChat(false), 2000);
      setToastMessage("Copied to clipboard");
      setToastVisible(true);
    } catch (err) {
      console.error("Copy failed", err);
      setToastMessage("Copy failed");
      setToastVisible(true);
    }
  }

  // ——— If still locked ———
  if (isPrivate) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#fcfbf7] dark:bg-gray-900">
        {!accessRequested ? (
          <div className="text-center space-y-4">
            <Lock className="mx-auto w-12 h-12 text-gray-500" />
            <h2 className="text-xl font-semibold">This session is private</h2>
            <button
              onClick={requestAccess}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Request Access
            </button>
          </div>
        ) : (
          <div className="text-center space-y-4">
            <Check className="mx-auto w-12 h-12 text-green-500" />
            <h2 className="text-xl font-semibold">Access requested</h2>
            <p>The owner will receive an email to approve your request.</p>
          </div>
        )}
      </div>
    );
  }
  // ——— Main chat UI ———
    return (
      <div className="flex min-h-screen bg-[#fcfbf7]">
        <ResponsiveSidebar />
        <main className="flex-1 flex flex-col bg-[#fcfbf7] dark:bg-gray-900 pl-20">

        {toastVisible && (
    <div className="fixed top-20 right-3 bg-[#fcfbf7] dark:bg-gray-800 shadow-lg rounded-lg px-4 py-2 flex items-center space-x-2 z-50">
      <CheckCircle className="w-5 h-5 text-green-500" />
      <span className="font-medium font-Grotesk dark:text-gray-100">{toastMessage}</span>
    </div>
  )}

          {/* Header */}
          <div className="sticky top-0 z-20 bg-[#fcfbf7]">
            <div className="px-2 py-1 flex items-center justify-between">

              {/* Profile dropdown */}
              <div ref={dropdownButtonRef} className="relative inline-block">
                <div
                  className="flex items-center cursor-pointer px-2 py-1"
                  onClick={() => setDropdownOpen(o => !o)}
                >
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-white text-xs ${getAvatarColor(
                      displayUser.full_name
                    )}`}
                  >
                    {displayUser.full_name.charAt(0).toUpperCase()}
                  </div>
                  <span className="ml-2 text-sm font-medium text-gray-900 dark:text-gray-100">
                    {displayUser.full_name}
                    {owner.id && currentUser && owner.id !== currentUser.id && (
                      <span className="ml-1 text-sm text-gray-500">(owner)</span>
                    )}
                  </span>
                  <ChevronDown className="ml-1 w-4 h-4 text-gray-700 dark:text-gray-300" />
                </div>
                {dropdownOpen && (
  <div
    ref={dropdownMenuRef}
    className="
       absolute top-full left-0
       mt-2
       w-[240px]
       bg-[#fcfbf7] dark:bg-gray-900
       border border-gray-200 dark:border-gray-700
       rounded-lg
       shadow-lg
       overflow-hidden
    "
  >
    {/* Created by */}
    <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 dark:border-gray-700">
      <span className="text-sm text-gray-600 dark:text-gray-400">Created by</span>
      <span className="text-sm font-base text-gray-900 dark:text-gray-100 truncate">
        {displayUser.full_name} ({currentUser && owner.id === currentUser.id ? 'you' : 'owner'})
      </span>
    </div>

    {/* Last updated */}
    <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 dark:border-gray-700">
      <span className="text-sm text-gray-600 dark:text-gray-400">Last updated</span>
      <span className="text-sm font-base text-gray-900 dark:text-gray-100">
        {formatDate(updatedAt)}
      </span>
    </div>

    {/* Country */}
    <div className="flex items-center px-4 py-2 border-b border-gray-200 dark:border-gray-700">
      <span className="fi fi-us w-3 h-3 mr-2" />
      <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
        {countryName}
      </span>
    </div>

    {/* Advisor */}
    <div className="flex items-center px-4 py-2 border-b border-gray-200 dark:border-gray-700">
      <Brain className="w-4 h-4 mr-2 text-gray-700 dark:text-gray-300" />
      <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
        {advisorName}
      </span>
    </div>
  </div>
)}
              </div>

              {/* More + Share */}
              <div className="flex items-center space-x-4 mt-2 mr-4">

                {/* More menu */}
                <div ref={moreRef} className="relative">
                  <Ellipsis
                    className="w-6 h-6 text-gray-900 dark:text-gray-300 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                    onClick={() => setMoreOpen(o => !o)}
                  />
                  {moreOpen && (
                    <div className="absolute top-full right-0 mt-2 w-64 bg-[#fcfbf7] dark:bg-gray-800 shadow-lg border border-gray-200 dark:border-gray-700 rounded-md z-20">
                      <div
                        className="px-4 py-2 flex items-center hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
                        onClick={openEditModal}
                      >
                        <span className="truncate flex-1 text-sm text-gray-900 dark:text-gray-100">
                          {sessionTitle || history.find((m) => m.role === "user")?.content}
                        </span>
                        <Pencil className="w-4 h-4 ml-2 text-gray-600 dark:text-gray-400" />
                      </div>
                      <div className="border-t border-gray-200 dark:border-gray-700" />
                      <div
                        className="px-4 py-2 flex items-center hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
                        onClick={() => {
                          setMoreOpen(false);
                          exportAsPdf();
                        }}
                      >
                        <File className="w-4 h-4 mr-2 text-gray-600 dark:text-gray-400" />
                        <span className="text-sm text-gray-900 dark:text-gray-100">
                          Export as PDF
                        </span>
                      </div>
                      <div
                        className="px-4 py-2 flex items-center hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
                        onClick={() => {
                          setMoreOpen(false);
                          exportAsDocx();
                        }}
                      >
                        <FileText className="w-4 h-4 mr-2 text-gray-600 dark:text-gray-400" />
                        <span className="text-sm text-gray-900 dark:text-gray-100">
                          Export as DOCX
                        </span>
                      </div>
                      {isOwner && (
                        <div
                          className="px-4 py-2 flex items-center hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
                          onClick={openDeleteConfirm}
                        >
                          <Trash2 className="w-4 h-4 mr-2 text-red-600 dark:text-red-400" />
                          <span className="text-sm text-red-600 dark:text-red-400">
                            Delete Session
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Share pop-over */}
                <div ref={shareRef} className="relative">
                <div className="relative inline-flex flex-col items-center group">
  <button
    aria-label="Share session"
    onClick={() => { setShareOpen(o=>!o); setCopied(false); }}
    className="w-5 h-5 text-gray-700 hover:text-gray-900 cursor-pointer ml-3 hover:bg-gray-100 dark:hover:bg-gray-700 rounded flex mb-2"
  >
    <Share/>
  </button>
  <span className="
      absolute top-full mt-1
      bg-black text-white text-xs
      px-2 py-1 rounded
      opacity-0 group-hover:opacity-100
      transition-opacity
    ">
    Share
  </span>
</div>
                  {shareOpen && (
                    <div className="absolute top-full right-0 mt-2 w-96 bg-[#fcfbf7] dark:bg-gray-800 shadow-lg border border-gray-200 dark:border-gray-700 rounded-lg z-20">
                      <div className="p-4 space-y-4">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                          Share this chat session
                        </h3>

                        {/* options */}
                        <div className="mt-2 divide-y divide-gray-200 dark:divide-gray-700">
                          <button
                            onClick={() => handleShareOption("private")}
                            className={`
                              w-full text-left px-4 py-3 flex justify-between items-start
                              rounded-md
                              ${shareOption === "private"
                                ? "bg-gray-100 dark:bg-gray-700"
                                : "hover:bg-gray-50 dark:hover:bg-gray-700"}
                            `}
                          >
                            <div>
                              <div className="flex items-center space-x-2">
                                <Lock className="w-5 h-5 text-gray-500" />
                                <span className="font-medium text-gray-900 dark:text-gray-100">
                                  Private
                                </span>
                              </div>
                              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                                Only the author can view
                              </p>
                            </div>
                            {shareOption === "private" && (
                              <Check className="w-5 h-5 text-blue-500 mt-1" />
                            )}
                          </button>

                          <button
                            onClick={() => handleShareOption("link")}
                            className={`
                              w-full text-left px-4 py-3 flex justify-between items-start
                              rounded-md
                              ${shareOption === "link"
                                ? "bg-gray-100 dark:bg-gray-700"
                                : "hover:bg-gray-50 dark:hover:bg-gray-700"}
                            `}
                          >
                            <div>
                              <div className="flex items-center space-x-2">
                                <LinkIcon className="w-5 h-5 text-gray-500" />
                                <span className="font-medium text-gray-900 dark:text-gray-100">
                                  Anyone with the link
                                </span>
                              </div>
                              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                                Anyone can view
                              </p>
                            </div>
                            {shareOption === "link" && (
                              <Check className="w-5 h-5 text-blue-500 mt-1" />
                            )}
                          </button>
                        </div>

                        {/* feedback */}
                        {copied && (
                          <div className="flex items-center space-x-1 text-sm text-green-600">
                            <LinkIcon className="w-4 h-4" />
                            <span>Link copied. Paste to share</span>
                          </div>
                        )}

                        {/* Copy Link */}
                        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                          <button
                            onClick={copyLink}
                            className="w-full flex items-center justify-center px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-md font-medium hover:bg-gray-200 dark:hover:bg-gray-600"
                          >
                            <LinkIcon className="w-4 h-4 mr-2" />
                            Copy Link
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Chat history & input */}
          <div className="flex-1 flex flex-col w-full max-w-[700px] mx-auto transform -translate-x-0 ml-[19rem]">
          <div
  id="chat-to-export"
  ref={chatContainerRef}
  onScroll={handleChatScroll}
  className="flex-1 overflow-auto hide-scrollbar px-6 py-4 space-y-4"
>

{history.map((m, idx) => {
  const isLast     = idx === history.length - 1;
  const isEditing  = editingMessageId === m.id;
  const paras      = m.content.split(/\n\n/);
  const tooLong    = paras.length > 3;
  const isExpanded = expanded === m.id;
  const display    = isExpanded ? m.content : paras.slice(0, 3).join("\n\n");
  const isEditingAssistant = m.id === regeneratingId && m.role === "assistant";

  // Auto-resize editor when it appears or content changes


  // ——— USER MESSAGE ———
  if (m.role === "user") {
    if (isEditing) {
      return (
        <div key={m.id} className="relative w-full">
    {/* --- static, dimmed background bubble --- */}
    <div
      ref={originalRef}
      className="bg-[#fcfbf7] dark:bg-gray-800 rounded-lg p-4 whitespace-pre-wrap text-2xl font-grotesk font-semibold"
    >
      {m.content}
    </div>


          {/* Overlay editor */}
          <div className="absolute inset-0 w-full bg-[#fcfbf7] dark:bg-gray-800 rounded-lg p-4 z-10 shadow-lg overflow-hidden">
      <textarea
        ref={editingTaRef}
        className="
          w-full
          resize-none
          bg-transparent
          focus:outline-none
          whitespace-pre-wrap
          text-2xl font-grotesk font-medium
        "
        value={editingContent}
        onChange={e => setEditingContent(e.target.value)}
        onInput={e => {
          // still let it grow beyond the question height if user types more
          const ta = e.currentTarget;
          ta.style.height = "auto";
          ta.style.height = `${Math.max(
            ta.scrollHeight,
            originalRef.current?.getBoundingClientRect().height || 0
          )}px`;
        }}
      />

      {/* ✓ / ✕ in the top-right */}
      <div className="absolute bottom-3 right-3 flex space-x-0">
        <button onClick={saveEdit} className="flex items-center gap-1 px-3 py-1 hover:bg-gray-100">
          <Check className="w-5 h-5 text-green-900"/> 
        </button>
        <button onClick={cancelEdit} className="flex items-center gap-1 px-3 py-1 hover:bg-gray-100">
          <X className="w-5 h-5 text-red-900"/>
        </button>
      </div>
    </div>
        </div>
      );
    }

    // normal (non-editing) user message UI
    return (
      <div key={m.id} className="relative group mb-6 bg-[#fcfbf7] rounded-lg p-4">
        <div
          className={
            !isExpanded && tooLong
              ? "text-2xl font-grotesk font-medium line-clamp-2 overflow-hidden"
              : "text-2xl font-grotesk font-medium"
          }
        >
          {display}
        </div>
        {tooLong && !isExpanded && (
          <button
            className="mt-1 text-blue-900 hover:underline"
            onClick={() => setExpanded(m.id)}
          >
            Show more
          </button>
        )}
        {tooLong && isExpanded && (
          <button
            className="mt-1 text-blue-800 hover:underline"
            onClick={() => setExpanded(null)}
          >
            Show less
          </button>
        )}
        {/* pencil + copy icons bottom-right */}
        <div className="absolute bottom-2 right-2 flex space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={() => startEdit(m)}
            className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
            aria-label="Edit question"
          >
            <Pencil className="w-4 h-4 text-gray-500 hover:text-gray-700" />
          </button>
          <button
            onClick={() => {
              navigator.clipboard.writeText(m.content);
              setCopiedQ(m.id);
              setTimeout(() => setCopiedQ(null), 2000);
            }}
            className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
            aria-label="Copy question"
          >
            {copiedQ === m.id ? (
              <Check className="w-4 h-4 text-gray-600" />
            ) : (
              <Copy className="w-4 h-4 text-gray-500 hover:text-gray-700" />
            )}
          </button>
        </div>
      </div>
    );
  }

  if (isEditingAssistant) {
    return (
      <div key={m.id} className="flex items-start px-4 space-x-2 mt-2">
        <span
          className="inline-block w-1.5 h-1.5 bg-gray-700 rounded-full animate-bounce"
          style={{ animationDelay: "0ms" }}
        />
        <span
          className="inline-block w-1.5 h-1.5 bg-gray-700 rounded-full animate-bounce"
          style={{ animationDelay: "200ms" }}
        />
        <span
          className="inline-block w-1.5 h-1.5 bg-gray-700 rounded-full animate-bounce"
          style={{ animationDelay: "400ms" }}
        />
      </div>
    );
  }

  // ——— ASSISTANT MESSAGE ———
  return (
    <div key={m.id} className="pt-4 pb-6">
      <MarkdownRenderer content={m.content} />
      {m.suggestions && m.suggestions.length > 0 && (
        <RelatedQueries suggestions={m.suggestions} onSelect={handleSuggestionClick} />
      )}
      {!(streaming && isLast) && (
        <>
          <div className="flex justify-between items-center text-gray-800 dark:text-gray-400 mt-5">
            {/* share + export */}
            <div className="flex space-x-5 mt-3">
              <button
                aria-label="Share answer"
                onClick={handleShareUnderChat}
                className="flex items-center space-x-1 px-2 py-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
              >
                {sharedUnderChat ? (
                  <Check className="w-4 h-4 text-gray-800" />
                ) : (
                  <Share className="w-4 h-4" />
                )}
                <span className="text-sm">Share</span>
              </button>

              <div className="relative">
                <button
                  ref={el => {
                    exportBtnRefs.current[m.id] = el;
                  }}
                  onClick={() => toggleExportMenu(m.id)}
                  className="flex items-center space-x-1 px-2 py-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                >
                  <File className="w-4 h-4" />
                  <span className="text-sm">Export</span>
                </button>
                <FloatingMenu
                  referenceElement={exportBtnRefs.current[m.id]}
                  isOpen={openExportDropdownId === m.id}
                >
                  <button
                    onClick={exportAnswerPdf.bind(null, m)}
                    className="flex items-center w-full px-4 py-1 space-x-3 bg-[#fcfbf7] hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                  >
                    <File className="w-4 h-4" />
                    <span className="text-sm">Export as PDF</span>
                  </button>
                  <button
                    onClick={exportAnswerDocx.bind(null, m)}
                    className="flex items-center w-full px-4 py-1 space-x-3 bg-[#fcfbf7] hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                  >
                    <FileText className="w-4 h-4" />
                    <span className="text-sm">Export as DOCX</span>
                  </button>
                </FloatingMenu>
              </div>
            </div>

            {/* like / dislike / copy / more */}
            <div className="flex space-x-4">
              <button
                onClick={() => handleReact(m.id, "like")}
                className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <ThumbsUp 
                  className={`w-4 h-4 ${
                    messageReactions[m.id] === "like"
                      ? "text-blue-500 fill-blue-500"
                      : "text-gray-500 dark:text-gray-400 stroke-current"
                  }`}
                />
              </button>
              <button
                onClick={() => handleReact(m.id, "dislike")}
                className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <ThumbsDown 
                  className={`w-4 h-4 ${
                    messageReactions[m.id] === "dislike"
                      ? "text-red-500 fill-red-600"
                      : "text-gray-500 dark:text-gray-400 stroke-current"
                  }`}
                />
              </button>
              <button
                onClick={() => handleCopyAnswer(m.content)}
                className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                {copiedUnderChat ? (
                  <Check className="w-4 h-4 text-gray-800" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
              <div className="relative">
                <button
                  ref={el => {
                    optionsBtnRefs.current[m.id] = el;
                  }}
                  onClick={() =>
                    setOpenOptionsMenuId(prev =>
                      prev === m.id ? null : m.id
                    )
                  }
                  className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <Ellipsis className="w-4 h-4" />
                </button>
                <FloatingMenu
                  referenceElement={optionsBtnRefs.current[m.id]}
                  isOpen={openOptionsMenuId === m.id}
                  onClose={() => setOpenOptionsMenuId(null)}
                >
                  <button
                    onClick={() => {
                      setReportingMessageId(m.id);
                      setInitialFeedback({
                        reasons: m.user_feedback?.reasons || [],
                        comments:
                          m.user_feedback?.additional_comments || "",
                      });
                      setFeedbackOpen(true);
                      setOpenOptionsMenuId(null);
                    }}
                    className="flex items-center w-full px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded bg-[#fcfbf7] text-left"
                  >
                    <Flag className="w-3 h-3 text-gray-900 mr-2" />
                    <span className="text-sm">Report</span>
                  </button>
                </FloatingMenu>
              </div>
            </div>
          </div>
          <hr className="border-t border-gray-200 my-4" />
          {openReasonForId === m.id && (
  <div className="mt-2 relative border border-gray-300 dark:border-gray-700 rounded-lg p-4 bg-[#fcfbf7] dark:bg-gray-800">
    {/* Close icon */}
    <button
      onClick={() => setOpenReasonForId(null)}
      className="absolute top-2 right-2 text-gray-600 hover:bg-gray-200 dark:text-gray-400 dark:hover:text-gray-200"
    >
      <X className="w-4 h-4" />
    </button>

    <p className="mb-2 text-sm text-gray-700 dark:text-gray-300">
      What {pendingReactionType === 'like' ? 'did you like' : "didn't you like"} about this response? (optional)
    </p>

    <div className="grid grid-cols-3 gap-2">
      {(pendingReactionType === 'like'
        ? [
            ['up_to_date','Up to date'],
            ['accurate','Accurate'],
            ['helpful','Helpful'],
            ['followed_instructions','Followed instructions'],
            ['good_sources','Good sources'],
            ['like_other','Other…'],
          ]
        : [
            ['out_of_date','Out of date'],
            ['inaccurate','Inaccurate'],
            ['wrong_sources','Wrong sources'],
            ['too_long','Too long'],
            ['too_short','Too short'],
            ['dis_other','Other…'],
          ]
      ).map(([value,label]) => (
        <button
          key={value}
          onClick={() => {
            setSelectedReason(value);
            // if Other… needs a comment, open textarea then wait for blur?
            // otherwise immediately submit
            if (!value.endsWith('_other')) {
              submitReaction({
                reason: value
              });
            }
          }}
          className={`px-3 py-1 font-cormorant text-medium font-base border rounded ${
            selectedReason === value
              ? 'bg-blue-100 dark:bg-blue-900'
              : 'bg-transparent'
          }`}
        >
          {label}
        </button>
      ))}
    </div>

    {/* Optional textarea for "Other…" */}
    {selectedReason.endsWith('_other') && (
      <div className="relative mt-2">
          <textarea
            rows={5}
            className="
              w-full
              p-2
              border
              rounded
              bg-[#fcfbf7] dark:bg-gray-700
              text-gray-900 dark:text-gray-100
              resize-none
              overflow-y-auto
              scrollbar-thin scrollbar-thumb-gray-400
            "
            placeholder="Add specific details"
            value={otherComment}
            onChange={e => setOtherComment(e.target.value)}
          />
      
          {/* arrow-up inside a circle, bottom-right */}
          <button
            onClick={() => submitReaction({ reason: selectedReason, comments: otherComment })}
            className={`
              absolute bottom-2 right-2
              w-8 h-8 flex items-center justify-center
              rounded-full
              transition-colors mb-2
              ${otherComment
                ? 'bg-blue-400'
                : 'bg-gray-200 dark:bg-gray-600'}
            `}
          >
            <ArrowUp
              className={`
                w-4 h-4
                transition-colors
                ${otherComment
                  ? 'text-gray-900'
                  : 'text-gray-400 dark:text-gray-300'}
              `}
            />
          </button>
        </div>
    )}
  </div>
)}


        </>
      )}
    </div>
  );
})}


              {/* typing loader */}
              {streaming && regeneratingId === null && (
                <div className="flex items-start px-4 space-x-2 mt-2">
                  <span className="inline-block w-1.5 h-1.5 bg-gray-700 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="inline-block w-1.5 h-1.5 bg-gray-700 rounded-full animate-bounce" style={{ animationDelay: "200ms" }} />
                  <span className="inline-block w-1.5 h-1.5 bg-gray-700 rounded-full animate-bounce" style={{ animationDelay: "400ms" }} />
                </div>
              )}

              <div ref={endRef} />
            </div>
            <form
    onSubmit={sendMessage}
    className="mt-auto sticky bottom-0 p-2 z-10 bg-[#fcfbf7] dark:bg-gray-900 w-full"
  >
    <div className="w-full max-w-[650px] mx-auto">
      <div className="flex flex-col bg-[#fcfbf7] dark:bg-[#2A2C3E] border border-gray-600 dark:border-gray-700 rounded-2xl p-4">
        <textarea
          rows={1}
          className="w-full bg-transparent text-gray-900 dark:text-gray-100 placeholder-gray-600 dark:placeholder-gray-500 resize-none overflow-y-auto max-h-36 focus:outline-none scrollbar-thin scrollbar-thumb-gray-700 dark:scrollbar-thumb-gray-900"
          placeholder="Type your question…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={streaming}
          onInput={(e) => {
            const ta = e.currentTarget;
            ta.style.height = "auto";
            ta.style.height = `${ta.scrollHeight}px`;
          }}
        />

        {/* ← usage on the left, controls on the right */}
        <div className="flex justify-between items-center mt-4">
          <div className="text-sm text-gray-600">
            🔢 {used} / {limit} used this month
            {outOfQuota && (
              <div className="mt-1 text-red-600 text-sm">
                You've reached your monthly limit.{" "}
                <a href="/pro" className="underline">
                  Upgrade to Pro
                </a>{" "}
                to continue.
              </div>
            )}
          </div>

          <div className="flex items-center space-x-4">
          <div className="relative inline-flex flex-col items-center group">
  <button
    type="button"
    aria-label="Mic"
    onClick={stopStream}
    className="p-1 rounded"
  >
    <Mic className="w-5 h-5" />
  </button>
  <span className="
      absolute top-full mt-1
      bg-black text-white text-xs
      px-2 py-1 rounded
      opacity-0 group-hover:opacity-100
      transition-opacity
    ">
    Mic
  </span>
</div>
            {streaming ? (
              <div className="relative inline-flex flex-col items-center group">
              <button
                type="button"
                aria-label="Stop streaming"
                onClick={stopStream}
                className="p-1 rounded text-red-600"
              >
                <StopCircle className="w-5 h-5" />
              </button>
              <span className="
                  absolute top-full mt-1
                  bg-black text-white text-xs
                  px-2 py-1 rounded
                  opacity-0 group-hover:opacity-100
                  transition-opacity
                ">
                Stop
              </span>
            </div>
            ) : (
              <div className="relative inline-flex flex-col items-center group">
  <button
    type="submit"
    aria-label="Send answer"
    className="p-1 rounded"
  >
    <Send className="w-5 h-5" />
  </button>
  <span className="
      absolute top-full mt-1
      bg-black text-white text-xs
      px-2 py-1 rounded
      opacity-0 group-hover:opacity-100
      transition-opacity
    ">
    Send
  </span>
</div>
            )}
          </div>
        </div>
      </div>
    </div>
  </form>
          </div>
        </main>

        {/* Edit Title Modal */}
        {editOpen && (
          <div className="fixed inset-0 bg-black bg-opacity-20 backdrop-blur-sm flex items-center justify-center z-40">
            <div
              className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-lg p-6 w-full max-w-xl relative"
              style={{ fontFamily: "'Space Grotesk', sans-serif" }}
            >
              <button
                className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                onClick={() => setEditOpen(false)}
              >
                <X className="w-5 h-5" />
              </button>
              <h3 className="text-2xl font-grotesk text-gray-900 dark:text-gray-100 mb-4">
                Edit Session Title
              </h3>
              <input
                type="text"
                className="w-full h-12 px-4 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-900 dark:text-gray-100"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                placeholder="Enter session title…"
              />
              <div className="flex justify-end space-x-2 mt-6">
                <button
                  type="button"
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
                  onClick={saveTitle}
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {confirmDeleteOpen && (
          <div className="fixed inset-0 bg-black bg-opacity-20 backdrop-blur-sm flex items-center justify-center z-50">
            <div
              className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-lg p-6 w-full max-w-lg"
              style={{ fontFamily: "'Space Grotesk', sans-serif" }}
            >
              <h3 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Are you sure?
              </h3>
              <p className="text-gray-700 dark:text-gray-300 mb-6">
                This will permanently delete the session and its entire chat history.
              </p>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={closeDeleteConfirm}
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
                >
                  Cancel
                </button>
                <button
                  onClick={deleteSession}
                  className="px-5 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}

<FeedbackModal
  open={feedbackOpen}
  initialValues={initialFeedback}
  onClose={() => setFeedbackOpen(false)}
  onSubmit={async (values: FeedbackValues) => {
    if (!slug || reportingMessageId == null) return;
    await api.post(
      `/sessions/${slug}/messages/${reportingMessageId}/feedback/`,
      {
        message: reportingMessageId,
        reasons: values.reasons,
        additional_comments: values.comments,
      }
    );

    setHistory(h =>
      h.map(msg =>
        msg.id === reportingMessageId
          ? { ...msg, user_feedback: { reasons: values.reasons, additional_comments: values.comments } }
          : msg
      )
    );
    setToastMessage("Thanks for your feedback!");
    setToastVisible(true);
    setFeedbackOpen(false);
  }}
/>
        
      </div>
    );
  }


