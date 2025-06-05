// components/FloatingMenu.tsx
"use client";

import { ReactNode, useState, useLayoutEffect } from "react";
import { createPortal } from "react-dom";
import {
  useFloating,
  offset,
  flip,
  shift,
  autoUpdate,
} from "@floating-ui/react";

export function FloatingMenu({
  referenceElement,
  isOpen,
  children,
}: {
  referenceElement: HTMLElement | null;
  isOpen: boolean;
  children: ReactNode;
}) {
  const [popperElement, setPopperElement] = useState<HTMLDivElement | null>(null);

  const { x, y, strategy } = useFloating({
    elements: {
      reference: referenceElement,
      floating: popperElement,
    },
    placement: "bottom-end",
    middleware: [offset(8), flip(), shift()],
    whileElementsMounted: autoUpdate,
  });

  if (!isOpen) return null;

  return createPortal(
    <div
      ref={setPopperElement}
      style={{
        position: strategy,
        top: y ?? 0,
        left: x ?? 0,
        zIndex: 50,
      }}
      className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg overflow-hidden"
    >
      {children}
    </div>,
    document.body
  );
}
