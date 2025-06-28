"use client";

import { useEffect, useState } from "react";
import api from "@/lib/apiprivate";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Check, Pencil } from "lucide-react";

/* ─── colour helper ───────────────────────────────────────── */
const avatarColors = [
  "bg-red-500",
  "bg-green-500",
  "bg-blue-500",
  "bg-yellow-500",
  "bg-purple-500",
  "bg-pink-500",
  "bg-indigo-500",
];
const getAvatarColor = (name: string) =>
  avatarColors[
    name.split("").reduce((acc, c) => acc + c.charCodeAt(0), 0) %
      avatarColors.length
  ];

/* ─── types ───────────────────────────────────────────────── */
type Tier = "free" | "pro" | "premium";
interface UserMe {
  id: number;
  full_name: string;
  username: string;
  email: string;
  membership: {
    membership_type: Tier;
    start_date: string;
    end_date: string | null;
    is_active: boolean;
  };
}

export default function AccountDetailsPanel() {
  const [me, setMe] = useState<UserMe | null>(null);
  const [editingName, setEditingName] = useState(false);
  const [fullName, setFullName] = useState("");

  /* fetch profile once */
  useEffect(() => {
    api.get<UserMe>("/users/me/").then(({ data }) => {
      setMe(data);
      setFullName(data.full_name);
    });
  }, []);

  const saveName = () =>
    api
      .patch("/users/me/", { full_name: fullName })
      .then(() => setMe((u) => (u ? { ...u, full_name: fullName } : u)))
      .finally(() => setEditingName(false));

  if (!me) return <div className="flex-1 p-8">Loading…</div>;

  /* ─────────────────────────────── UI ─────────────────────────────── */
  return (
    <div className="flex-1 w-full overflow-y-auto py-12">
      {/* centre everything in a max-width column */}
      <div className="mx-auto w-full max-w-3xl px-6">

        {/* === Account ================================================= */}
        <h2 className="text-xl font-semibold mb-6">Account</h2>

        {/* avatar row */}
        <div className="grid grid-cols-[170px_1fr_auto] gap-x-8 gap-y-6 items-center">
          {/* Avatar + name block */}
          <div className="col-span-2 flex items-center space-x-4">
            <div
              className={`
                h-16 w-16 rounded-full flex items-center justify-center
                text-white text-2xl shrink-0
                ${getAvatarColor(me.full_name)}
              `}
            >
              {me.full_name[0].toUpperCase()}
            </div>
            <div>
              <div className="font-medium text-gray-900">{me.full_name}</div>
              <div className="text-sm text-muted-foreground">
                {me.username}
              </div>
            </div>
          </div>

          <Button variant="outline" size="sm">
            Change avatar
          </Button>

          {/* Full Name row */}
          <div className="text-sm font-medium text-gray-600">Full Name</div>
          <div>
            {!editingName ? (
              <span>{me.full_name}</span>
            ) : (
              <Input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-56"
              />
            )}
          </div>
          <div>
            {!editingName ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setEditingName(true)}
              >
                Edit
              </Button>
            ) : (
              <Button size="icon" onClick={saveName}>
                <Check className="w-4 h-4" />
              </Button>
            )}
          </div>

          {/* Username row */}
          <div className="text-sm font-medium text-gray-600">Username</div>
          <div>{me.username}</div>
          <div>
            <Button variant="outline" size="sm">
              Change username
            </Button>
          </div>

          {/* Email row */}
          <div className="text-sm font-medium text-gray-600">Email</div>
          <div>{me.email}</div>
          <div /> {/* keeps 3-col grid aligned */}
        </div>

        {/* === Subscription =========================================== */}
        <h2 className="text-xl font-semibold mt-12 mb-4">Subscription</h2>
        <div className="grid grid-cols-[1fr_auto] items-center gap-4 py-2 border-t">
          <div>
            Unlock the most powerful experience with&nbsp;
            <span className="font-medium capitalize">
              {me.membership.membership_type} plan
            </span>
          </div>
          <Button variant="outline" onClick={() => location.assign("/pricing")}>
            Manage plan
          </Button>
        </div>
      </div>
    </div>
  );
}
