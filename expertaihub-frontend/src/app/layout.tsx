// src/app/layout.tsx
import "./globals.css";
import { UserProvider } from "@/context/UserContext";

export const metadata = { viewport: 'width=device-width, initial-scale=1' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="flex min-h-screen">
        <UserProvider>
          {/* Main content */}
          <main className="flex-1">
            {children}
          </main>
        </UserProvider>
      </body>
    </html>
  );
}

