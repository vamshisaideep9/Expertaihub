// src/lib/apipublic.ts
import axios from "axios";

const apipublic = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE,
  withCredentials: false,        // public endpoints don’t rely on cookies
  headers: { "Content-Type": "application/json" },
});

export default apipublic;
