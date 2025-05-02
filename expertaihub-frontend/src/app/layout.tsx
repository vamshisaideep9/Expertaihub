// src/app/layout.tsx

import "./globals.css"
import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import { ThemeProvider } from "next-themes"        // ← import here

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
})
const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
})

export const metadata: Metadata = {
  title: "Expertaihub",
  description: "Ultra-specialized AI advisors on demand.",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      {/* ThemeProvider injects the correct class before React hydrates */}
      <ThemeProvider attribute="class" enableSystem>
        <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
          {children}
        </body>
      </ThemeProvider>
    </html>
  )
}
