// src/app/layout.tsx
import "./globals.css";

export const metadata = { viewport: 'width=device-width, initial-scale=1' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="flex min-h-screen">
        {/* Sidebar always visible */}

        {/* Main content */}
        <main className="flex-1">
          {children}
        </main>
      </body>
    </html>
  );
}

