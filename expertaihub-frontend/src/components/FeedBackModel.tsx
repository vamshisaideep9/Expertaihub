// src/components/FeedbackModal.tsx
"use client";
import React, { useState, useEffect } from "react";
import { 
  XCircle,        // “Inaccurate”
  Minimize2,      // “Too short”
  Maximize2,      // “Too long”
  Shuffle,        // “Out of context”
  AlertTriangle,  // “Harmful/Offensive”
  MoreHorizontal, // “Other”
 } from "lucide-react";

export type FeedbackValues = {
  reasons: string[];
  comments: string;
};

interface FeedbackModalProps {
  open: boolean;
  initialValues: FeedbackValues;
  onClose: () => void;
  onSubmit: (values: FeedbackValues) => Promise<void>;
}

export const REASONS = [
  { key: "inaccurate",     label: "Inaccurate",        Icon: XCircle },
  { key: "too_short",      label: "Too short",        Icon: Minimize2 },
  { key: "too_long",       label: "Too long",         Icon: Maximize2 },
  { key: "out_of_context", label: "Out of context",   Icon: Shuffle },
  { key: "harmful",        label: "Harmful/Offensive", Icon: AlertTriangle },
  { key: "other",          label: "Other",            Icon: MoreHorizontal },
];

export function FeedbackModal({ open, initialValues, onClose, onSubmit }: FeedbackModalProps) {
  const [reasons, setReasons]       = useState<string[]>(initialValues.reasons);
  const [comments, setComments]     = useState(initialValues.comments);
  const [submitting, setSubmitting] = useState(false);

  // lock body scroll while open
  useEffect(() => {
    // capture whatever the page had before
    const previous = document.body.style.overflow;
    
    if (open) {
      document.body.style.overflow = "hidden";
    }
  
    return () => {
      // restore on close *or* when component unmounts
      document.body.style.overflow = previous;
    };
  }, [open]);

  useEffect(() => {
        if (open) {
          setReasons(initialValues.reasons);
          setComments(initialValues.comments);
        }
      }, [open, initialValues.reasons, initialValues.comments]);

  
  const toggleReason = (key: string) => {
    setReasons(r => r.includes(key) ? r.filter(x=>x!==key) : [...r, key]);
  };

  const handleSubmit = async () => {
    if (reasons.length === 0) return;
    setSubmitting(true);
    try {
      await onSubmit({ reasons, comments });
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      // always mounted, but hidden when open===false
      className={`fixed inset-0 z-50 flex items-center justify-center ${!open && "hidden"}`}
      onClick={onClose}
    >
      {/* backdrop */}
      <div className="absolute inset-0 bg-black bg-opacity-30 backdrop-blur-sm" />

      {/* panel */}
      <div
        className="relative z-10 bg-[#fcfbf7] dark:bg-gray-800 rounded-2xl w-full max-w-[500px] p-6"
        onClick={e => e.stopPropagation()}
      >
        {/* header */}
        <h3 className="text-2xl font-base font-cormorant text-gray-900 dark:text-gray-100 mb-1">
          Help us improve
        </h3>
        <p className="text-base font-cormorant text-gray-500 dark:text-gray-300 mb-4">
          Provide additional feedback on this answer
        </p>
        <div className="border-t border-gray-200 dark:border-gray-700 mb-4" />

        {/* reason buttons */}
        <div className="grid grid-cols-2 gap-3 mb-4">
        {REASONS.map(r => {
  const Icon = r.Icon;
  return (
    <button
      key={r.key}
      type="button"
      onClick={() => toggleReason(r.key)}
      className={`
        flex items-center px-3 py-2 rounded-lg border font-base text-sm transition
        ${reasons.includes(r.key)
          ? "bg-blue-100 border-blue-300 text-blue-800"
          : "bg-[#fcfbf7] border-gray-400 text-gray-800 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200"
        }`}
    >
      <Icon className="w-4 h-4 text-gray-600 dark:text-gray-300 mr-4"/>  
      {r.label}
    </button>
  );
})}
        </div>

        {/* comments */}
        <label className="block text-sm font-cormorant text-gray-700 dark:text-gray-300 mb-1">
          How can the response be improved? <span className="text-gray-500">(optional)</span>
        </label>
        <textarea
          className="w-full p-3 mb-5 resize-none rounded-lg border border-gray-400 dark:border-gray-600 bg-[#fcfbf7] dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none"
          rows={4}
          placeholder="Your feedback matters..."
          value={comments}
          onChange={e => setComments(e.target.value)}
        />

        {/* actions */}
        <div className="border-t border-gray-200 dark:border-gray-700 pt-4 flex justify-end space-x-3">
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            className="px-5 py-2 rounded-lg bg-[#fcfbf7] dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600 transition"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={reasons.length === 0 || submitting}
            className={`px-5 py-2 rounded-lg text-white transition
              ${reasons.length > 0
                ? "bg-blue-600 hover:bg-blue-700"
                : "bg-blue-300 cursor-not-allowed"
              }`}
          >
            {submitting ? "Submitting…" : "Submit"}
          </button>
        </div>
      </div>
    </div>
  );
}
