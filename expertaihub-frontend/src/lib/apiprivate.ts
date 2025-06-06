// src/lib/apiprivate.ts
import axios from "axios";

const apiprivate = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE,
  withCredentials: true,         // send your JWT cookie automatically
  headers: { "Content-Type": "application/json" },
});

// on every request, read the `token` cookie and add an Authorization header
apiprivate.interceptors.request.use((config) => {
  if (typeof document !== "undefined") {
    const match = document.cookie.match(/(?:^|; )token=([^;]+)/);
    const token = match?.[1];
    if (token) {
      config.headers!["Authorization"] = `Bearer ${token}`;
    }
  }
  return config;
});

export default apiprivate;
