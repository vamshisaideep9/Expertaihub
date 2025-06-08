/*─────────────────────────────────────────────
  MarkdownRenderer – tuned list / table weights
──────────────────────────────────────────────*/
"use client";

import React         from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm     from "remark-gfm";

interface MarkdownRendererProps { content: string }

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        /*────────── side-headings (###) ──────────*/
        h3: p => (
          <h3
            {...p}
            className="mt-5 mb-2 text-2xl font-semibold leading-tight font-cormorant"
          />
        ),

        /*────────── inline <strong> ─────────────*/
        strong: p => <strong {...p} className="font-semibold" />,

        /*────────── paragraphs ──────────────────*/
        p: p => (
          <p
            {...p}
            className="mt-2 text-[1.15rem] leading-relaxed font-cormorant"
          />
        ),

        /*────────── UL  – everything regular ─────*/
        ul: p => (
          <ul
            {...p}
            className="
              list-disc ml-6 space-y-1
              marker:font-normal                 /* bullet regular        */
              [&>li]:font-normal                 /* top-level text regular*/
              [&_ol>li]:!font-normal              /* nested-OL text regular*/
              [&_ol]:marker:font-semibold        /* BUT nested-OL numbers bold */
            "
          />
        ),

        /*────────── OL  – top-level items bold ───*/
        ol: p => (
          <ol
            {...p}
            className="
              list-decimal ml-6 space-y-1
              marker:font-semibold               /* number marker bold   */
              [&>li]:font-semibold               /* top-level text bold  */
            "
          />
        ),

        /*────────── list item base tweaks ────────*/
        li: p => <li {...p} className="mt-1">{p.children}</li>,

        /*────────── table – Step # bold only ─────*/
        table: p => (
          <table
            {...p}
            className="
              w-full mt-3 mb-4 text-left border-collapse
              font-cormorant text-[1.05rem]
              [&>thead>tr>th]:font-semibold      /* header bold          */
              [&>tbody>tr>td:first-child]:font-semibold  /* first col (Step) bold */
            "
          />
        ),
        th: p => <th {...p} className="pb-1 pr-3 border-b" />,
        td: p => <td {...p} className="py-1 pr-3" />,
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
