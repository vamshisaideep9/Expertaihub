// components/SettingsSideNavBar.tsx
"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { cn } from "@/lib/utils"; // utility to concat classNames – replace if you use a different helper

// Lucide icons
import {
  UserCircle,
  Settings2,
  Wand2,
  CreditCard,
  Settings,
  ChevronLeft,
} from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
}

const NAV_ITEMS: NavItem[] = [
  { label: "My account", href: "/account/details", icon: UserCircle },
  { label: "Preferences", href: "/account/preferences", icon: Settings2 },
  { label: "Personalize", href: "/account/personalize", icon: Wand2 },
  { label: "Purchases", href: "/account/purchases", icon: CreditCard },
  { label: "Settings", href: "/account/settings", icon: Settings },
];

export default function SettingsSideNavBar() {
  const pathname = usePathname();

  return (
    <aside
      className="flex h-full w-64 shrink-0 flex-col border-r bg-[#fcfbf7] p-4 text-sm min-h-screen"
    >
      <Link
        href="/home"
        className="flex items-center gap-1 mt-1 text-gray-500 hover:text-gray-900 mb-4 text-lg"
      >
        <ChevronLeft className="h-6 w-6 text-gray-500 hover:text-gray-900"/>
        <span>Back</span>
      </Link>
      <div className="mt-5 mb-2 ml-3">
        <span className="text-sm font-base text-gray-900">Account</span>
      </div>
      <nav className="flex flex-col gap-1 flex-1">
        {NAV_ITEMS.map(({ label, href, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 transition-colors text-[11px] font-base",
                "hover:bg-blue-50 hover:text-blue-700",
                active && "bg-blue-100 text-blue-700"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

/*
Utility – cn(): If you don't already have a helper for className concatenation, add this to /lib/utils.ts:

export function cn(...classes: (string | undefined | false)[]) {
  return classes.filter(Boolean).join(" ");
}
*/
