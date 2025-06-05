"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import rehypeRaw from "rehype-raw";

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, remarkBreaks]}
      rehypePlugins={[rehypeRaw]}
      components={{
        // ### headings
        h3: ({ node, ...props }) => (
          <h3
            {...props}
            className="text-xl font-base leading-tight font-cormorant mt-4 mb-2"
          />
        ),
        // bold
        strong: ({ node, ...props }) => (
          <strong {...props} className="font-semibold" />
        ),
        // paragraphs
        p: ({ node, ...props }) => (
          <p
            {...props}
            className="mt-2 text-lg font-base whitespace-pre-wrap font-cormorant"
          />
        ),
        // unordered lists
        ul: ({ node, ...props }) => (
          <ul {...props} className="list-disc ml-6 space-y-1" />
        ),
        // ordered lists
        ol: ({ node, ...props }) => (
          <ol {...props} className="list-decimal ml-6 space-y-1" />
        ),
        // list items
        li: ({ node, ...props }) => (
          <li {...props} className="mt-1 marker:font-semibold">
            {props.children}
          </li>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
