"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeRaw]}
      skipHtml={false}
      components={{
        // H2 styling
        h2: ({ node, ...props }) => (
          <h2
            {...props}
            className="mt-6 mb-4 text-3xl font-semibold font-cormorant leading-tight"
          />
        ),
        // H3 styling
        h3: ({ node, ...props }) => (
          <h3
            {...props}
            className="mt-5 mb-2 text-2xl font-semibold font-cormorant leading-snug"
          />
        ),

        // Table wrapper for scroll + fixed layout
        table: ({ node, ...props }) => (
          <div className="overflow-x-auto my-6">
            <table
              {...props}
              className="
                w-max            /* grow as wide as the content needs           */
        lg:w-full        /* but clamp back to the viewport ≥1024 px     */
        table-auto
        border-collapse
        border border-gray-400
        rounded-lg
        bg-[#fcfbf7]
        font-cormorant
        text-[1.1rem]
        whitespace-nowrap   /* keep each cell on one line 
              "
            />
          </div>
        ),

        thead: (props) => <thead {...props} />,
        tbody: (props) => <tbody {...props} />,

        tr: ({ node, ...props }) => (
          <tr
            {...props}
            className="odd:bg-[#faf9f5] even:bg-[#fcfbf7]"
          />
        ),

        th: ({ node, ...props }) => (
          <th
            {...props}
            className="
              px-4 py-2
              bg-gray-100
              font-semibold
              text-left
              border border-gray-400
            "
          />
        ),

        td: ({ node, ...props }) => (
          <td
            {...props}
            className="
              px-4 py-2
              border border-gray-400
              align-top
              whitespace-normal
            "
          />
        ),

        p: ({ node, ...props }) => (
          <p
            {...props}
            className="mt-2 text-[1.2rem] leading-relaxed font-cormorant"
          />
        ),

        ul: ({ node, ...props }) => (
          <ul
            {...props}
            className="list-disc ml-6 space-y-1 marker:font-base text-lg [&>li]:font-normal"
          />
        ),

        ol: ({ node, ...props }) => (
          <ol
            {...props}
            className="list-decimal ml-6 space-y-1 marker:font-semibold [&>li]:font-semibold"
          />
        ),

        li: ({ node, ...props }) => (
          <li {...props} className="mt-1" />
        ),

        strong: ({ node, ...props }) => (
          <strong {...props} className="font-semibold" />
        ),

        a: ({ node, ...props }) => (
          <a
            {...props}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 underline hover:text-blue-800"
          />
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
