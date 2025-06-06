"use client";
import { createContext, useState, useEffect, ReactNode } from "react";
import api from "@/lib/apiprivate";

export interface User {
  id: number;
  full_name: string;
  email: string;
  membership: {
    membership_type: string;
    start_date: string | null;
    end_date: string | null;
    is_active: boolean;
  };
}

interface UserContextValue {
  user: User | null;
  loading: boolean;
}

export const UserContext = createContext<UserContextValue>({
  user: null,
  loading: true,
});

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("user");
      if (saved) {
        try {
          return JSON.parse(saved) as User;
        } catch {}
      }
    }
    return null;
  });

  const [loading, setLoading] = useState(user === null);

  useEffect(() => {
    async function fetchUser() {
      try {
        const { data } = await api.get<User>("/users/me/");
        setUser(data);
        if (typeof window !== "undefined") {
          localStorage.setItem("user", JSON.stringify(data));
        }
      } catch (err) {
        console.error("Error fetching user", err);
        setUser(null);
      } finally {
        setLoading(false);
      }
    }
    fetchUser();
  }, []);

  return (
    <UserContext.Provider value={{ user, loading }}>
      {children}
    </UserContext.Provider>
  );
}
