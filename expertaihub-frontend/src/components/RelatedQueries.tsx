"use client";

import { Button } from "@/components/ui/button";

export function RelatedQueries({
  suggestions,
  onSelect,
}: {
  suggestions: string[];
  onSelect: (q: string) => void;
}) {
  if (!suggestions.length) return null;

  return (
    <div className="flex flex-wrap gap-2 mt-4">
      {suggestions.map((s, i) => (
        <Button
          key={i}
          type="button"
          variant="outline"
          size="sm"
          onClick={() => onSelect(s)}
        >
          {s}
        </Button>
      ))}
    </div>
  );
}
