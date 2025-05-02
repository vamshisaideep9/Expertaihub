'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/apipublic'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Eye, EyeOff, Lock, Mail } from 'lucide-react'

export default function LoginPage() {
  const [form, setForm] = useState({ email: '', password: '' })
  const [rememberMe, setRememberMe] = useState(false)
  const [error, setError] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const router = useRouter()

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value })
    setError('')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const res = await api.post('users/login/', form)

      const accessToken = res.data.access;
      const refreshToken = res.data.refresh;

      // Save tokens in cookies
      document.cookie = `token=${accessToken}; path=/; max-age=${rememberMe ? 604800 : 86400}; secure; samesite=strict`;
      document.cookie = `refresh_token=${refreshToken}; path=/; max-age=${rememberMe ? 604800 : 86400}; secure; samesite=strict`;

      router.push('/home')

    } catch (err: any) {
      console.error(err);

      if (err.response?.data?.error) {
        setError(err.response.data.error); // Show backend error (user does not exist, wrong password, etc.)
      } else {
        setError('Something went wrong. Please try again.');
      }
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-foreground px-4">
      <Card className="w-full max-w-md shadow-md">
        <CardContent className="py-10">
          <h1 className="text-2xl font-bold mb-4 text-center">Login</h1>
          <p className="text-muted-foreground text-center mb-6">
            Welcome back to Expertaihub.
          </p>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="relative">
              <Input
                type="email"
                name="email"
                placeholder="Email"
                required
                onChange={handleChange}
                value={form.email}
                className="focus:ring-2 focus:ring-primary pl-10"
              />
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
            </div>

            <div className="relative">
              <Input
                type={showPassword ? 'text' : 'password'}
                name="password"
                placeholder="Password"
                required
                onChange={handleChange}
                value={form.password}
                className="focus:ring-2 focus:ring-primary pr-10 pl-10"
              />
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground focus:outline-none cursor-pointer"
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-sm">
                <Checkbox
                  checked={rememberMe}
                  onCheckedChange={(checked) => setRememberMe(!!checked)}
                />
                Remember me
              </label>
              <a
                href="/forgot-password"
                className="text-sm text-primary underline hover:text-primary/90"
              >
                Forgot password?
              </a>
            </div>

            <Button type="submit" className="w-full cursor-pointer hover:bg-primary/90 focus:outline-none transition-all">
              Login
            </Button>
          </form>

          {error && (
            <p className="text-sm text-center mt-4 text-red-500">{error}</p>
          )}

          <p className="text-sm text-center text-muted-foreground mt-6">
            Don't have an account?{' '}
            <a
              href="/signup"
              className="text-primary underline hover:text-primary/90"
            >
              Sign up here
            </a>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
