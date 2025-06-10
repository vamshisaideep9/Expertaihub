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
        table: ({ node, ...props }) => (
          <table
            {...props}
            className="
              w-full
              table-auto
              border-separate
              border-spacing-0
              my-6
              border
              border-gray-400
              rounded-lg
              bg-[#fcfbf7]
              font-cormorant
              text-[1.1rem]
            "
          />
        ),
        thead: (props) => <thead {...props} />,  
        tbody: (props) => <tbody {...props} />,  
        tr: ({ node, ...props }) => (
          <tr
            {...props}
            className="
              odd:bg-[#faf9f5]
              even:bg-[#fcfbf7]
            "
          />
        ),
        th: ({ node, ...props }) => (
          <th
            {...props}
            className="
              px-4
              py-2
              bg-gray-100
              font-semibold
              text-left
              border-b-2
              border-gray-400
              border-r
              border-gray-400
              last:border-r-0
            "
          />
        ),
        td: ({ node, ...props }) => (
          <td
            {...props}
            className="
              px-4
              py-2
              border-b
              border-gray-400
              border-r
              border-gray-400
              last:border-r-0
              align-top
              whitespace-pre-wrap
            "
          />
        ),
        h3: (p) => (
          <h3
            {...p}
            className="mt-5 mb-2 text-2xl font-base leading-tight font-cormorant"
          />
        ),

        strong: (p) => <strong {...p} className="font-semibold" />,

        p: (p) => (
          <p
            {...p}
            className="mt-2 text-[1.2rem] leading-relaxed font-cormorant"
          />
        ),

        ul: (p) => (
          <ul
            {...p}
            className="list-disc ml-6 space-y-1 marker:font-base text-lg [&>li]:font-normal [&_ol>li]:!font-normal [&_ol]:marker:font-semibold"
          />
        ),

        ol: (p) => (
          <ol
            {...p}
            className="list-decimal ml-6 space-y-1 marker:font-semibold [&>li]:font-semibold"
          />
        ),

        li: (p) => <li {...p} className="mt-1">{p.children}</li>,

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
