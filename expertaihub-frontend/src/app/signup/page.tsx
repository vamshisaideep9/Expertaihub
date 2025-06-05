'use client'

import { useState, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import apipublic from "@/lib/apipublic"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Eye, EyeOff, Mail, User, Lock } from "lucide-react"

export default function SignupPage() {
  const router   = useRouter()
  const initialQ = useSearchParams().get("question") || ""
  const [form, setForm]       = useState({ email: "", full_name: "", password: "" })
  const [message, setMessage] = useState("")
  const [showPass, setShow]   = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    document.cookie = 'token=; path=/; max-age=0'
    document.cookie = 'refresh_token=; path=/; max-age=0'
  }, [])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value })
    setMessage("")
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      // 1️⃣ Register only
      const res = await apipublic.post("users/register/", form)
      setMessage(res.data.message)  // e.g. "Check your email to verify your account."
    } catch (err: any) {
      setMessage(
        err.response?.data?.email?.[0] ||
        err.response?.data?.full_name?.[0] ||
        err.response?.data?.password?.[0] ||
        err.response?.data?.non_field_errors?.[0] ||
        "Registration failed."
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <Card className="w-full max-w-md">
        <CardContent className="py-10">
          <h1 className="text-2xl font-bold mb-2 text-center">Sign Up</h1>

          {initialQ && (
            <p className="text-sm text-center mb-4 text-primary">
              You asked: “{decodeURIComponent(initialQ)}”
            </p>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18}/>
              <Input
                type="email"
                name="email"
                placeholder="Email"
                required
                value={form.email}
                onChange={handleChange}
                className="pl-10"
              />
            </div>

            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18}/>
              <Input
                type="text"
                name="full_name"
                placeholder="Full Name"
                required
                value={form.full_name}
                onChange={handleChange}
                className="pl-10"
              />
            </div>

            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18}/>
              <Input
                type={showPass ? "text" : "password"}
                name="password"
                placeholder="Password"
                required
                value={form.password}
                onChange={handleChange}
                className="pl-10 pr-10"
              />
              <button
                type="button"
                onClick={() => setShow(p => !p)}
                className="absolute right-3 top-1/2 -translate-y-1/2"
              >
                {showPass ? <EyeOff size={18}/> : <Eye size={18}/>}
              </button>
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Signing up…" : "Sign Up"}
            </Button>
          </form>

          {message && (
            <p className={`mt-4 text-center text-sm ${
              message.toLowerCase().includes("check your email")
                ? "text-green-600"
                : "text-red-500"
            }`}>
              {message}
            </p>
          )}

          <p className="mt-6 text-center text-sm">
            Already have an account?{" "}
            <a
              href={`/signin${initialQ ? `?question=${encodeURIComponent(initialQ)}` : ""}`}
              className="underline text-primary"
            >
              Sign in here
            </a>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

