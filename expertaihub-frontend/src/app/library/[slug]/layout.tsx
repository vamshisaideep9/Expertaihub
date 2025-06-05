import { Metadata, Viewport } from "next";

export const metadata: Metadata = {
  title: "ExpertAIHub - Chat Session",
  description: "View and interact with your chat session",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function ChatSessionLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
} 