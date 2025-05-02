'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import api from '@/lib/apipublic'
import { Loader2, CheckCircle2, AlertTriangle } from 'lucide-react'

export default function VerifyEmailPage() {
  const { uid, token } = useParams<{ uid: string; token: string }>()
  const [message, setMessage] = useState('Verifying your email...')
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const router = useRouter()

  useEffect(() => {
    const verify = async () => {
      try {
        const res = await api.get(`users/verify-email/${uid}/${token}/`)
        setStatus('success')
        setMessage(res.data.message)
        setTimeout(() => router.push('/signin/'), 3000)
      } catch (err: any) {
        const error = err.response?.data?.error || 'Verification failed.'
        setStatus('error')
        setMessage(error)
      }
    }

    if (uid && token) verify()
  }, [uid, token, router])

  const renderIcon = () => {
    if (status === 'loading') return <Loader2 className="w-12 h-12 animate-spin text-primary" />
    if (status === 'success') return <CheckCircle2 className="w-12 h-12 text-green-500" />
    if (status === 'error') return <AlertTriangle className="w-12 h-12 text-red-500" />
    return null
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-foreground px-4">
      <div className="text-center max-w-sm space-y-6">
        <div className="flex justify-center">{renderIcon()}</div>
        <h1 className="text-2xl font-bold">Email Verification</h1>
        <p className="text-muted-foreground text-lg">{message}</p>
        {status === 'success' && (
          <p className="text-sm text-muted-foreground">
            Redirecting to your signin page...
          </p>
        )}
      </div>
    </div>
  )
}
