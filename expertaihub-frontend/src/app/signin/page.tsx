'use client';

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import apipublic from "@/lib/apipublic";
import apiprivate from "@/lib/apiprivate";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Card, CardContent } from "@/components/ui/card";
import { Eye, EyeOff, Lock, Mail } from "lucide-react";

export default function LoginPage() {
  const router       = useRouter();
  const initialQ     = useSearchParams().get("question") || "";
  const [form, setForm]         = useState({ email: "", password: "" });
  const [rememberMe, setRem]    = useState(false);
  const [error, setError]       = useState("");
  const [showPassword, setShow] = useState(false);


   // ← Clear out any old tokens on mount
  useEffect(() => {
    document.cookie = 'token=; path=/; max-age=0'
    document.cookie = 'refresh_token=; path=/; max-age=0'
  }, [])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {

      document.cookie = 'token=; path=/; max-age=0'
      document.cookie = 'refresh_token=; path=/; max-age=0'
      // 1️⃣ Call public login endpoint
      const res = await apipublic.post("users/login/", form);
      const { access, refresh } = res.data;

      // 2️⃣ Store both tokens in non-HttpOnly cookies
      //    (so apiprivate can read `token`)
      document.cookie = `token=${access}; path=/; max-age=${rememberMe ? 604800 : 86400}; secure; samesite=strict`;
      document.cookie = `refresh_token=${refresh}; path=/; max-age=${rememberMe ? 604800 : 86400}; secure; samesite=strict`;

      // 3️⃣ Fetch current user and stash in localStorage
      const { data: user } = await apiprivate.get("/users/me/");
      if (typeof window !== "undefined") {
        localStorage.setItem("user", JSON.stringify(user));
      }

      // 4️⃣ If the user came in with a question, create a chat
      if (initialQ) {
        const { data } = await apiprivate.post("immigration-ai/create-session/", {
          question: initialQ,
          niche:    "immigration",
          country:  "usa",
        });
        return router.push(`/library/${data.slug}`);
      }

      // 5️⃣ Otherwise go to home
      router.push("/home");
    } catch (err: any) {
      setError(err.response?.data?.error || "Login failed. Please try again.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <Card className="w-full max-w-md">
        <CardContent className="py-10">
          <h1 className="text-2xl font-bold mb-4 text-center">Login</h1>
          {initialQ && (
            <p className="text-sm text-center mb-4 text-primary">
              You asked: “{decodeURIComponent(initialQ)}”
            </p>
          )}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18}/>
              <Input
                type="email" name="email" placeholder="Email" required
                value={form.email} onChange={handleChange}
                className="pl-10"
              />
            </div>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18}/>
              <Input
                type={showPassword?"text":"password"}
                name="password" placeholder="Password" required
                value={form.password} onChange={handleChange}
                className="pr-10 pl-10"
              />
              <button
                type="button"
                className="absolute right-3 top-1/2 -translate-y-1/2"
                onClick={() => setShow((p) => !p)}
              >
                {showPassword ? <EyeOff size={18}/> : <Eye size={18}/>}
              </button>
            </div>
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-sm">
                <Checkbox
                  checked={rememberMe}
                  onCheckedChange={(c) => setRem(!!c)}
                />
                Remember me
              </label>
              <a href="/forgot-password" className="text-sm underline">Forgot password?</a>
            </div>
            <Button type="submit" className="w-full">Login</Button>
          </form>
          {error && <p className="mt-4 text-center text-red-500">{error}</p>}
          <p className="mt-6 text-center text-sm">
            Don’t have an account?{" "}
            <a
              href={`/signup${initialQ ? `?question=${encodeURIComponent(initialQ)}` : ""}`}
              className="underline text-primary"
            >
              Sign up here
            </a>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
