'use client'

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Brain, Gavel, Plane, ReceiptText, Briefcase, GraduationCap, Globe, FileText, Bot, FileSearch, Layers, DollarSign, CreditCard, BarChart3, Sun, Moon, Plus} from "lucide-react"
import Link from "next/link"
import { motion } from "framer-motion"

export default function LandingPage() {
  const [isDark, setIsDark] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem("theme")
    if (saved) setIsDark(saved === "dark")
  }, [])

  useEffect(() => {
    localStorage.setItem("theme", isDark ? "dark" : "light")
    document.documentElement.classList.toggle("dark", isDark)
  }, [isDark])

  const useCases = [
    { title: "Immigration", icon: <Plane className="w-6 h-6 mb-3 text-primary" />, desc: "Apply for a UK Tier 2 visa as a healthcare worker.", active: true },
    { title: "Legal Help", icon: <Gavel className="w-6 h-6 mb-3 text-muted-foreground" />, desc: "Generate a custody agreement for California family law.", active: false },
    { title: "Tax & Compliance", icon: <ReceiptText className="w-6 h-6 mb-3 text-muted-foreground" />, desc: "Create a sales tax exemption letter for your Texas business.", active: false },
    { title: "Grant Writing", icon: <Briefcase className="w-6 h-6 mb-3 text-muted-foreground" />, desc: "Write a GreenTech grant proposal under $100K.", active: false },
    { title: "Education & Study", icon: <GraduationCap className="w-6 h-6 mb-3 text-muted-foreground" />, desc: "Get step-by-step help on Canadian student visa applications.", active: false },
    { title: "Appeals & Forms", icon: <FileText className="w-6 h-6 mb-3 text-muted-foreground" />, desc: "Fill EOIR-29 appeals and other complex legal forms automatically.", active: false }
  ]

  const pricingPlans = [
    {
      name: "Free 🆓",
      price: "$0 / mo",
      features: [
        "🔢 15 queries / month",
        "📚 RAG Depth: 2 docs",
        "🧠 Session Memory: in-session only",
        "📝 Form Drafts: locked",
        "⚠️ Compliance: basic safety & intent",
        "💬 Support: community forum",
        "📊 Analytics: none",
        "🛠️ Early Access: none",
      ],
    },
    {
      name: "Pro 🚀",
      price: "$19 / mo",
      features: [
        "🔢 Unlimited queries",
        "📚 RAG Depth: 4 docs",
        "🧠 Session Memory: 7-day summary",
        "📝 Form Drafts: guide-style drafts",
        "⚠️ Compliance: + clarifying questions",
        "💬 Support: email (12 hr SLA)",
        "📊 Analytics: usage dashboard",
        "🛠️ Early Access: no",
      ],
    },
    {
      name: "Premium 🌟",
      price: "$49 / mo",
      features: [
        "🔢 Unlimited queries",
        "📚 RAG Depth: 8 docs",
        "🧠 Session Memory: 30-day & profile",
        "📝 Form Drafts: full pre-filled PDFs",
        "⚠️ Compliance: custom legal rulesets",
        "💬 Support: priority chat & phone (4 hr SLA)",
        "📊 Analytics: advanced & CSV export",
        "🛠️ Early Access: beta features",
      ],
    },
    {
      name: "Expert Templates 🧠",
      price: "Earn with Us",
      features: [
        "🤖 Submit your own AI brain",
        "💸 Earn 30% of revenue per use",
        "📚 Add niche-specific expertise",
        "🔒 Approval & compliance required",
        "🧑‍⚖️ Reviewed by domain experts",
      ],
    },
  ]

  return (
    <div className="min-h-screen bg-background text-foreground scroll-smooth">
      <nav className="w-full flex items-center justify-between py-4 px-6 md:px-12 border-b border-muted">
        <Link href="/">
          <span className="text-xl font-bold cursor-pointer">Expertaihub</span>
        </Link>
        <div className="flex items-center space-x-4 text-muted-foreground text-sm">
          {['Features','Use Cases','Pricing'].map(section => (
            <span
              key={section}
              className="hover:text-foreground cursor-pointer hidden md:inline"
              onClick={() => document.getElementById(section.toLowerCase().replace(' ', ''))?.scrollIntoView({ behavior: 'smooth' })}
            >
              {section}
            </span>
          ))}
          <Link href="/signin"><Button variant="outline">Signin</Button></Link>
          <Link href="/signup"><Button>Signup</Button></Link>
          <Button variant="ghost" size="icon" onClick={() => setIsDark(!isDark)}>
            {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </Button>
        </div>
      </nav>

      <header className="max-w-5xl mx-auto text-center px-6 md:px-0 py-24">
        <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">Expertaihub</h1>
        <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto">
          Ultra-specialized AI advisors on demand. Accurate, local, and human-like expertise — without the consulting fees.
        </p>
      </header>

      <main id="features" className="max-w-6xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8 px-6 md:px-0">
        {[
          { icon: <Brain className="w-6 h-6 mb-3" />, title: "Expert-Brain Templates", desc: "AI advisors fine-tuned on domain-specific data — simulating how real experts think and solve problems." },
          { icon: <Globe className="w-6 h-6 mb-3" />, title: "Locality-Aware Guidance", desc: "Answers personalized to your legal region or country, ensuring accuracy and relevance." },
          { icon: <FileText className="w-6 h-6 mb-3" />, title: "Document Generator", desc: "Auto-generate immigration forms, appeal letters, tax notices, and more — editable and export-ready." },
          { icon: <Bot className="w-6 h-6 mb-3" />, title: "Conversational UX", desc: "Feels like chatting with a human consultant — complete with memory, tone, and follow-ups." },
          { icon: <FileSearch className="w-6 h-6 mb-3" />, title: "Explainability Engine", desc: "Breaks down complex terms and procedures into plain English — so you always understand the 'why'." },
          { icon: <Layers className="w-6 h-6 mb-3" />, title: "Multi-Niche Coverage", desc: "Support for 500+ niches across immigration, finance, law, parenting, grants, and more." }
        ].map(({ icon, title, desc }) => (
          <motion.div
            key={title}
            initial={false}
            whileHover={{ scale: 1.03 }}
            transition={{ type: "spring", stiffness: 200 }}
            className="border rounded-xl p-6 hover:shadow-lg transition"
          >
            <div className="text-primary">{icon}</div>
            <h3 className="text-xl font-semibold mb-2">{title}</h3>
            <p className="text-muted-foreground">{desc}</p>
          </motion.div>
        ))}
      </main>

      <section id="usecases" className="max-w-6xl mx-auto px-6 md:px-0 mt-24">
        <h2 className="text-3xl font-bold text-center mb-4">Use Cases</h2>
        <p className="text-muted-foreground text-center mb-12 max-w-2xl mx-auto">
          From immigration and legal assistance to grant writing and business compliance — Expertaihub is your AI-powered advisor for everything complex, local, and high-stakes.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {useCases.map(({ icon, title, desc, active }) => (
            <motion.div
              key={title}
              initial={false}
              whileHover={active ? { scale: 1.03 } : {}}
              transition={{ type: "spring", stiffness: 200 }}
              className={`border rounded-xl p-6 flex flex-col justify-between transition ${active ? "bg-card text-foreground" : "bg-muted/30 text-muted-foreground opacity-60"}`}
            >
              <div>
                <div>{icon}</div>
                <h3 className="text-xl font-semibold mb-2">{title}</h3>
                <p className="text-sm mb-4">{desc}</p>
              </div>
              {active ? (
                <Link href={`/signup?question=${encodeURIComponent(title.toLowerCase())}`}>
                  <Button variant="outline" size="sm">Try This</Button>
                </Link>
              ) : (
                <Button variant="ghost" size="sm" disabled>🔒 Coming Soon</Button>
              )}
            </motion.div>
          ))}
        </div>
      </section>

      <section id="pricing" className="max-w-6xl mx-auto px-6 md:px-0 mt-24">
        <h2 className="text-3xl font-bold text-center mb-4">Pricing</h2>
        <p className="text-muted-foreground text-center mb-12 max-w-2xl mx-auto">
          Choose the plan that best fits your needs — from quick free trials to full-featured enterprise support.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {pricingPlans.map(({ name, price, features }) => (
            <motion.div
              key={name}
              initial={false}
              whileHover={{ scale: 1.03 }}
              transition={{ type: "spring", stiffness: 200 }}
              className="border rounded-xl p-6 hover:shadow-lg transition flex flex-col"
            >
              <h3 className="text-2xl font-semibold mb-1 text-center">{name}</h3>
              <p className="text-xl font-bold mb-4 text-center">{price}</p>
              <ul className="text-sm space-y-2 flex-1">
                {features.map((f) => (
                  <li key={f} className="flex items-start">
                    <span className="mr-2">{f.split(" ")[0]}</span>
                    <span>{f.substring(f.indexOf(" ") + 1)}</span>
                  </li>
                ))}
              </ul>
              {name.startsWith("Free") ? (
                <Link href="/signup"> <Button className="mt-6 w-full">Get Started</Button> </Link>
              ) : (
                <Button className="mt-6 w-full">Upgrade</Button>
              )}
            </motion.div>
          ))}
        </div>
      </section>

      <footer className="text-center text-muted-foreground mt-24 pb-10 px-4">
        <p>© 2025 Expertaihub. Built for the future of consulting.</p>
      </footer>
    </div>
  )
}
