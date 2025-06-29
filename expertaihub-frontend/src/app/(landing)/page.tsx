'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import {
  Brain,
  Gavel,
  Plane,
  ReceiptText,
  Briefcase,
  GraduationCap,
  Globe,
  FileText,
  Bot,
  FileSearch,
  Layers,
  Sun,
  Moon,
} from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function LandingPage() {
  /* ─────────────────────────  theme toggle  ───────────────────────── */
  const [isDark, setIsDark] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem('theme')
    if (saved) setIsDark(saved === 'dark')
  }, [])

  useEffect(() => {
    localStorage.setItem('theme', isDark ? 'dark' : 'light')
    document.documentElement.classList.toggle('dark', isDark)
  }, [isDark])

  /* ─────────────────────────  data models  ───────────────────────── */
  const useCases = [
    {
      title: 'Immigration Info',
      icon: (
        <Plane className="w-[20px] h-[20px] mb-[8px] text-primary" />
      ),
      desc:
        'Explore US visa requirements and timelines (attorney review recommended).',
      active: true,
    },
    {
      title: 'Legal Research',
      icon: (
        <Gavel className="w-[20px] h-[20px] mb-[8px] text-muted-foreground" />
      ),
      desc:
        'Draft custody-agreement templates under California law (coming soon).',
      active: false,
    },
    {
      title: 'Tax Research',
      icon: (
        <ReceiptText className="w-6 h-6 mb-[8px] text-muted-foreground" />
      ),
      desc:
        'Generate a sales-tax exemption letter outline for Texas (coming soon).',
      active: false,
    },
    {
      title: 'Grant Writing',
      icon: (
        <Briefcase className="w-[20px] h-[20px] mb-[8px] text-muted-foreground" />
      ),
      desc: 'Draft a GreenTech grant proposal under $100 K (coming soon).',
      active: false,
    },
    {
      title: 'Education & Study',
      icon: (
        <GraduationCap className="w-[20px] h-[20px] mb-[8px] text-muted-foreground" />
      ),
      desc:
        'Step-by-step help on Canadian study-permit paperwork (coming soon).',
      active: false,
    },
    {
      title: 'Form Drafting',
      icon: (
        <FileText className="w-[20px] h-[20px] mb-[8px] text-muted-foreground" />
      ),
      desc: 'Automate EOIR-29 and other complex forms (coming soon).',
      active: false,
    },
  ]

  const pricingPlans = [
    {
      name: 'Free 🆓',
      price: '$0 / mo',
      features: [
        'Access to limited AI advisors',
        '8 queries / month',
        'Basic answer formatting',
        'Simple guidance only',
        'Community forum',
      ],
    },
    {
      name: 'Plus 🌟',
      price: '$49 / mo',
      features: [
        'All core AI advisors (immigration, basic legal, tax)',
        '50 queries / month',
        'Form-Drafting Assistant (up to 12 forms)',
        'Built-in templates & guides',
        'Email support (24 h SLA)',
      ],
    },
    {
      name: 'Pro+ 🚀',
      price: '$199 / mo',
      features: [
        'Unlimited queries',
        'Research Copilot for advanced workflows',
        'Dedicated workspace & analytics',
        'AI document review with red-flagging',
        'Fast-track expert escalation (≤ 24 h)',
        'Early access to new features',
      ],
    },
  ]

  /* ─────────────────────────  ui  ───────────────────────── */
  return (
    <div className="min-h-screen bg-[#fcfbf7] text-foreground scroll-smooth">
      {/* global disclaimer */}
      <div className="w-full bg-yellow-50 text-yellow-900 text-center text-xs py-2 px-2">
        AI content is for general information only—NOT legal, tax, medical, or
        financial advice. Always consult a qualified professional.
      </div>

      {/* nav */}
      <nav className="sticky top-0 z-[100] w-full flex items-center justify-between py-[12px] md:px-[24px] border-b border-muted bg-[#fcfbf7] shadow-sm">
        <Link href="/">
          <img
            src="/Expertaihub-1.png"
            alt="Expertaihub Logo"
            className="h-8 w-auto cursor-pointer"
          />
        </Link>

        <div className="flex items-center space-x-[18px] text-muted-foreground text-sm">
          {['Features', 'Use Cases', 'Pricing'].map((section) => (
            <span
              key={section}
              className="hover:text-foreground cursor-pointer hidden md:inline"
              onClick={() =>
                document
                  .getElementById(section.toLowerCase().replace(' ', ''))
                  ?.scrollIntoView({ behavior: 'smooth' })
              }
            >
              {section}
            </span>
          ))}

          <Link href="/signin">
            <Button variant="outline" className="bg-[#fcfbf7]">
              Sign in
            </Button>
          </Link>
          <Link href="/signup">
            <Button>Sign up</Button>
          </Link>
          <Button variant="ghost" size="icon" onClick={() => setIsDark(!isDark)}>
            {isDark ? (
              <Sun className="w-[20px] h-[20px]" />
            ) : (
              <Moon className="w-[20px] h-[20px]" />
            )}
          </Button>
        </div>
      </nav>

      {/* hero */}
      <header className="max-w-[500px] mx-auto text-center md:px-0 py-[12px]">
        <h1 className="text-[65px] font-base mb-[10px] font-cormorant">
          Expertaihub
        </h1>
        <p className="text-[10px] md:text-[20px] text-muted-foreground mx-auto font-cormorant">
          AI-powered research assistant with source-linked “Expert Brain”
          templates. Launching with immigration—ready to expand to any regulated
          domain worldwide.
        </p>
      </header>

      {/* features */}
      <main
        id="features"
        className="max-w-[990px] mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-[25px]"
      >
        {[
          {
            icon: (
              <Brain className="w-[20px] h-[20px] mb-[12px]" />
            ),
            title: 'ExpertBrainTemplate Marketplace',
            desc:
              'Browse or publish domain-tuned templates; each draft is review-ready, not final advice.',
          },
          {
            icon: (
              <Globe className="w-[20px] h-[20px] mb-[12px]" />
            ),
            title: 'Locality-Aware Information',
            desc:
              'Answers adjust to jurisdiction so professionals verify the right rule set faster.',
          },
          {
            icon: (
              <FileText className="w-[20px] h-[20px] mb-[12px]" />
            ),
            title: 'Form Drafting Assistant',
            desc:
              'Creates export-ready drafts from your inputs—final review by a pro still required.',
          },
          {
            icon: (
              <Bot className="w-[20px] h-[20px] mb-[12px]" />
            ),
            title: 'Conversational UX',
            desc:
              'Chat like with a human expert—context memory, follow-ups, polite hedging.',
          },
          {
            icon: (
              <FileSearch className="w-[20px] h-[20px] mb-[12px]" />
            ),
            title: 'Explainability Engine',
            desc:
              'Breaks down statutes and acronyms in plain English with links to primary sources.',
          },
          {
            icon: (
              <Layers className="w-[20px] h-[20px] mb-[12px]" />
            ),
            title: 'Multi-Domain Roadmap',
            desc:
              'Architecture ready to add finance, tax, grants, and real-estate verticals over time.',
          },
        ].map(({ icon, title, desc }) => (
          <motion.div
            key={title}
            whileHover={{ scale: 1.03 }}
            transition={{ type: 'spring', stiffness: 200 }}
            className="border rounded-[20px] p-[20px] hover:shadow-lg"
          >
            <div className="text-primary">{icon}</div>
            <h3 className="text-xl font-semibold mb-2">{title}</h3>
            <p className="text-muted-foreground">{desc}</p>
          </motion.div>
        ))}
      </main>

      {/* use-cases */}
      <section id="usecases" className="max-w-6xl mx-auto px-6 md:px-0 mt-24">
        <h2 className="text-[24px] font-semibold font-cormorant text-center mb-[18px]">
          Use Cases
        </h2>
        <p className="text-muted-foreground text-center mb-[14px] max-w-[640px] mx-auto">
          Start with US immigration, then expand to tax, legal, grant writing
          and beyond—each with its own ExpertBrainTemplate.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {useCases.map(({ icon, title, desc, active }) => (
            <motion.div
              key={title}
              whileHover={active ? { scale: 1.03 } : {}}
              transition={{ type: 'spring', stiffness: 200 }}
              className={`border rounded-xl p-6 flex flex-col justify-between ${
                active
                  ? 'bg-[#fcfbf7] text-foreground'
                  : 'bg-muted/30 text-muted-foreground opacity-60'
              }`}
            >
              <div>
                {icon}
                <h3 className="text-xl font-semibold mb-2">{title}</h3>
                <p className="text-sm mb-4">{desc}</p>
              </div>

              {active ? (
                <Link
                  href={`/signup?usecase=${encodeURIComponent(
                    title.toLowerCase()
                  )}`}
                >
                  <Button variant="outline" className="bg-[#fcfbf7]">
                    Try Demo
                  </Button>
                </Link>
              ) : (
                <Button variant="ghost" size="sm" disabled>
                  🔒 Coming Soon
                </Button>
              )}
            </motion.div>
          ))}
        </div>
      </section>

      {/* pricing */}
      <section id="pricing" className="max-w-6xl mx-auto px-6 md:px-0 mt-24">
        <h2 className="text-3xl font-bold text-center mb-4">Pricing</h2>
        <p className="text-muted-foreground text-center mb-12 max-w-2xl mx-auto">
          Choose the plan that fits your workflow—from a free sandbox to a
          fully-featured professional suite.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {pricingPlans.map(({ name, price, features }) => (
            <motion.div
              key={name}
              whileHover={{ scale: 1.03 }}
              transition={{ type: 'spring', stiffness: 200 }}
              className="border rounded-xl p-6 hover:shadow-lg flex flex-col"
            >
              <h3 className="text-2xl font-semibold mb-1 text-center">
                {name}
              </h3>
              <p className="text-xl font-bold mb-4 text-center">{price}</p>

              <ul className="text-sm space-y-2 flex-1">
                {features.map((f) => (
                  <li key={f} className="flex">
                    • <span className="pl-1">{f}</span>
                  </li>
                ))}
              </ul>

              {name.startsWith('Free') ? (
                <Link href="/signup">
                  <Button className="mt-6 w-full">Get Started</Button>
                </Link>
              ) : (
                <Button className="mt-6 w-full">Upgrade</Button>
              )}
            </motion.div>
          ))}
        </div>
      </section>

      {/* footer */}
      <footer className="text-center text-muted-foreground mt-24 pb-10 px-4">
        <p>© 2025 Expertaihub. Built for faster research & drafting.</p>
      </footer>
    </div>
  )
}
