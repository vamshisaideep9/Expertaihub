"use client"

import { useEffect, useState } from "react"
import ResponsiveSidebar from "@/components/ResponsiveSidebar"
import api from "@/lib/apiprivate"
import Link from "next/link"
import { Loader2 } from "lucide-react"

export default function LibraryPage() {
const [chats, setChats] = useState([])
const [loading, setLoading] = useState(true)

useEffect(() => {
async function fetchChats() {
try {
const res = await api.get("/library/list/")
setChats(res.data)
} catch (err) {
console.error("Failed to load chats.", err)
} finally {
setLoading(false)
}
}
fetchChats()
}, \[])

return ( <div className="flex min-h-screen"> <ResponsiveSidebar /> <main className="flex-1 px-6 py-12 bg-[#f9fafb] dark:bg-[#0f0f0f]"> <h1 className="text-3xl font-bold mb-8">📚 Your Chat Library</h1>
    {loading ? (
      <div className="flex items-center justify-center text-muted-foreground">
        <Loader2 className="animate-spin mr-2" /> Loading chats…
      </div>
    ) : chats.length === 0 ? (
      <p className="text-muted-foreground">You haven't saved any chats yet. Start a conversation to see them here.</p>
    ) : (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {chats.map((chat) => (
            <Link
                key={chat.slug}
                href={`/library/${chat.slug}/`}
                className="p-4 rounded-xl border bg-white dark:bg-zinc-900 hover:shadow-md transition"
            >
                <h2 className="font-semibold text-lg mb-2 line-clamp-2">{chat.prompt}</h2>
                <p className="text-sm text-muted-foreground line-clamp-3">{chat.answer}</p>
                <div className="flex items-center justify-between text-xs text-muted-foreground mt-4">
                <span>{chat.advisor || "Advisor"}</span>
                <span>{chat.country?.toUpperCase() || "USA"}</span>
                </div>
            </Link>
            ))}
        </div>
        )}
    </main>
    </div>
)
}
