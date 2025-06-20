"use client";

import { ListOrdered, Plus } from "lucide-react";
import { cn } from "@/lib/utils";          // ← if you already have a helper; else drop this

export function RelatedQueries({
  suggestions,
  onSelect,
}: {
  suggestions: string[];
  onSelect: (q: string) => void;
}) {
  if (!suggestions?.length) return null;

  return (
    <section className="mt-8">
      {/* ───── Heading ───── */}
      <div className="flex items-center gap-2 mb-3">
        <ListOrdered className="w-5 h-5 shrink-0 text-gray-700 dark:text-gray-300" />
        <h2 className="text-lg font-semibold font-grotesk tracking-tight">Related</h2>
      </div>

      {/* ───── List ───── */}
      <ul className="divide-y divide-gray-200 dark:divide-gray-700">
        {suggestions.map((text, i) => (
          <li key={i}>
            <button
              type="button"
              onClick={() => onSelect(text)}
              className={cn(
                "flex w-full items-center justify-between py-3 text-left",
                "hover:bg-gray-50 dark:hover:bg-gray-800 group"
              )}
            >
              {/* question text */}
              <span className="flex-1 pr-4 text-lg leading-snug font-cormorant">
                {text}
              </span>

              {/* plus icon */}
              <Plus className="w-5 h-5 shrink-0 text-gray-400 group-hover:text-blue-600" />
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
