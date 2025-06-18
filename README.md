# 🧠 Expertaihub – AI-Synthesized Domain Experts on Demand

> One Platform. 500+ AI Advisors. Trained Like Real Experts.

![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)
![Contributions Welcome](https://img.shields.io/badge/Contributions-Welcome-brightgreen)
![Built with Django](https://img.shields.io/badge/Backend-Django-informational)

---

## 🚀 What is Expertaihub?

**Expertaihub** is a powerful open-source platform for deploying ultra-specialized AI advisors trained on real-world expertise across domains.

Whether it's **Immigration, Legal, Finance, Parenting, Healthcare, or Startup Grants**, each advisor simulates the thinking patterns of a domain expert — delivering localized, trustworthy, and document-ready help.

---

## 🌍 Supported Niches (Examples from 500+)

- 🇺🇸 Immigration AI Advisor
- 🏛️ Legal Advisor (Contract Drafting, Dispute Resolution)
- 📈 Small Business Tax Advisor
- 🇨🇦 Canadian Grant Writer AI
- 🍼 Parenting & Childcare Consultant
- 📚 Academic Research Mentor
- 🏥 Health Insurance Planner
- 🏡 Real Estate Legal Advisor

Want to add your own? Just plug in your expert documents — and deploy.

---

## ⚙️ Tech Stack

| Layer       | Stack                          |
|------------|-------------------------------|
| Frontend   | Next.js + shadcn/ui           |
| Backend    | Django + FastAPI              |
| Vector DB  | FAISS                         |
| LLM Engine | GPT-4-turbo or Claude Opus    |
| Document QA | LangChain + RAG              |
| DB         | PostgreSQL                    |

---

## 📦 Core Features

- 🧠 **Expert Brain Templates** – Load new niches with ease
- 🌐 **Geo-Aware Responses** – Custom logic by country/state
- 📄 **Smart Document Generator** – Forms, Letters, Contracts
- 🔍 **Explainable AI** – Clear reasoning for every answer
- 💬 **Conversational UI** – Feels like chatting with a real expert
- 🛠️ **Pluggable Niches** – Just drop in docs and prompts

---

## 💡 How It Works

1. Add documents for your niche (PDF, text, URLs)
2. Our system chunks, embeds, and indexes them
3. Ask a question → get context-aware, expert-style responses
4. Auto-generate legal-grade docs or workflows

---

## ❓ Building FAQ Suggestions

Run the management command to generate or update the FAQ index:

```
python manage.py build_faq_index
```

This stores the FAISS files under `expertaihub_backend/suggestions/vectorstores/free/`.
You can set up a Celery beat task to run `suggestions.tasks.build_faq_index` periodically so the index stays fresh.

---
