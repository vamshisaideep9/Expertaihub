import { Metadata, Viewport } from "next";

export const metadata: Metadata = {
  title: "ExpertAIHub - Chat Library",
  description: "View and manage your chat sessions",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function LibraryLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
} 