"use client";
import { useRef } from "react";
import { useTheme } from "next-themes";
import React, { useState, useEffect, useContext } from "react";
import {
  Home,
  FileText,
  MessageCircle,
  ArrowLeftFromLine,
  ArrowRightFromLine,
  Settings,
  User,
  Wand2,
  Palette,
  CreditCard,
  LogOut,
  Plus,
  BookOpen
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { UserContext } from "@/context/UserContext";
import { Button } from '@/components/ui/button';


const navItems = [
  { icon: Home, label: "Home", href: "/home" },
  { icon: BookOpen, label: "Library", href: "/library" },
  { icon: FileText, label: "Documents", href: "/documents" },
  { icon: MessageCircle, label: "Advisors", href: "/advisors" },
];

const avatarColors = ["bg-red-500", "bg-green-500", "bg-blue-500", "bg-yellow-500", "bg-purple-500", "bg-pink-500", "bg-indigo-500"];

function getAvatarColor(name: string) {
  const hash = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return avatarColors[hash % avatarColors.length];
}

type DropdownItemProps = {
  icon: React.ReactNode;
  label: string;
};

function DropdownItem({ icon, label }: DropdownItemProps) {
  return (
    <div className="flex items-center gap-3 p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition">
      {icon}
      <span>{label}</span>
    </div>
  );
}

export default function ResponsiveSidebar() {
  const { theme } = useTheme();
  const router = useRouter();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const { user, loading } = useContext(UserContext);
     
  const [profileOpen, setProfileOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);


  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setProfileOpen(false);
      }
    }
  
    if (profileOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    } else {
      document.removeEventListener("mousedown", handleClickOutside);
    }
  
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [profileOpen]);
  


  const visibleNav = navItems.filter(
    item => !(item.href === "/documents" && user?.membership.membership_type === "free")
  );

  return (
    <div className="fixed top-0 left-0 flex h-screen transition-colors z-20">
      <div className={`relative bg-[#f8f7f1] dark:bg-gray-800 shadow-md flex flex-col justify-between transition-all ease-in-out ${open ? "w-[183px]" : "w-[58px]"}`}>
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between h-20 px-3 pt-2">
            <div className="flex items-center gap-1">
            <img
  src={theme === "dark" ? "/logo-light.png" : "/logo-dark.png"}
  alt="Logo"
  className={`object-contain transition-all duration-300 ${open ? "w-12 h-12" : "w-16 h-16"}`}
/>
              {open && (
                <span className="text-xl font-basic font-serif tracking-wide text-gray-900 dark:text-white transition-all">
                  Expertaihub
                </span>
              )}
            </div>
            {open && (
              <button
                onClick={() => setOpen(false)}
                className="bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 p-1 rounded-full transition-all cursor-pointer ml-2"
              >
                <ArrowLeftFromLine size={16} className="text-black dark:text-white"/>
              </button>
            )}
          </div>

          {!open && (
            <div className="flex justify-center py-2">
              <button
                onClick={() => router.push("/home")}
                className="w-9 h-9 flex items-center justify-center rounded-full bg-[#fcfbf7] text-black dark:bg-black dark:text-white border border-gray-300 dark:border-gray-600 hover:scale-105 transition cursor-pointe hover:scale-105 
    hover:border-blue-500 dark:hover:border-blue-500 
    hover:text-blue-500 dark:hover:text-blue-500 
    transition-colors transition-transformr"
                title="New Chat"
                aria-label="New Chat"
              >
                <Plus className="w-5 h-5"/>
              </button>
            </div>
          )}
           <div className={`flex-1 ${open ? "items-start px-3" : "items-center"} flex flex-col pt-6 gap-3 transition-all duration-300`}>
  {visibleNav.map(({ icon: Icon, label, href }) => {
    const isActive = pathname === href;
    return (
      <Link
        key={label}
        href={href}
        className={`flex ${open ? 'justify-start' : 'justify-center'} items-center w-full gap-3 rounded-lg ${open ? 'px-3' : 'px-0'} py-2 group relative transition-all duration-300
          ${isActive
            ? 'border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
            : 'hover:bg-blue-50 dark:hover:bg-blue-900 hover:text-blue-700 dark:hover:text-blue-300'}`}
      >
        <Icon size={20} strokeWidth={isActive ? 2 : 1.5} className={`transition-all ${isActive ? 'text-blue-500 dark:text-blue-300' : 'text-black dark:text-white group-hover:text-blue-700 dark:group-hover:text-blue-300'}`} />
        {open && <span className="text-sm font-medium">{label}</span>}
        {!open && (
          <span className="absolute left-16 bg-black text-white text-xs rounded-md px-2 py-1 opacity-0 group-hover:opacity-100 transition-all">
            {label}
          </span>
        )}
      </Link>
    );
  })}
</div>



        </div>

        <div className="flex flex-col items-center gap-4 px-4 mb-6">
          {!open && (
            <button
              onClick={() => setOpen(true)}
              className="bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 p-2 rounded-full transition-all cursor-pointer"
            >
              <ArrowRightFromLine size={22} className="text-black dark:text-white" />
            </button>
          )}

          {loading && !open && (
            <div className="w-10 h-10 mx-auto rounded-full bg-gray-300 animate-pulse" />
          )}
          {user && !open && (
            <div className="relative w-full">
              <div
                onClick={() => setProfileOpen(!profileOpen)}
                className={`w-10 h-10 mx-auto cursor-pointer rounded-full flex items-center justify-center font-semibold text-white text-lg ${getAvatarColor(user.full_name)} hover:shadow-lg transition-all`}
              >
                {user.full_name.charAt(0).toUpperCase()}
              </div>
              {profileOpen && (
                <div ref={dropdownRef} className="absolute bottom-12 left-12 transform translate-x-0 w-[13rem] bg-[#fcfbf7] dark:bg-gray-800 shadow-xl rounded-lg py-4 z-50 overflow-hidden">
                  <div className="flex items-center gap-3 px-4 mb-3">
                  <div className={`w-6 h-6 flex-shrink-0 rounded-full ${getAvatarColor(user.full_name)} text-white flex items-center justify-center text-xs font-semibold cursor-pointer`}>
                      {user.full_name.charAt(0).toUpperCase()}
                    </div>
                    <p className="flex-1 text-lg font-base font-cormorant text-gray-900 dark:text-white truncate">
                      {user.full_name}
                    </p>
                  </div>

                  <div className="flex flex-col space-y-1 px-4 text-sm text-gray-700 dark:text-gray-300">
                    <DropdownItem icon={<User size={16} />} label="My Account" />
                    <DropdownItem icon={<Wand2 size={16} />} label="Personalize" />
                    <DropdownItem icon={<Palette size={16} />} label="Appearance" />
                    <DropdownItem icon={<CreditCard size={16} />} label="Purchases" />
                    <DropdownItem icon={<Settings size={16} />} label="Settings" />
                  </div>

                  <div className="border-t border-gray-200 dark:border-gray-700 mt-4 pt-4 flex justify-center">
                  <button
  onClick={() => {
    document.cookie = "token=; Max-Age=0; path=/"; // clear token
    window.location.href = "/"; // redirect to homepage
  }}
  className="flex items-center gap-2 text-red-500 text-sm font-semibold hover:scale-105 transition cursor-pointer"
>
  <LogOut size={16} /> Logout
</button>
                  </div>
                </div>
              )}
            </div>
          )}

          {open && (
            <div className="bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-600 rounded-2xl shadow-inner hover:shadow-lg hover:scale-105 transition-all p-6 text-white text-center space-y-3">
            <p className="text-base font-semibold">You're missing out!</p>
            <p className="text-sm text-indigo-100">
              Upgrade to Pro for more features and faster answers
            </p>
            <Button variant="default" className="bg-white text-blue-600 font-bold rounded-full px-6 py-2 hover:bg-gray-100 transition-all cursor-pointer">
              Upgrade
            </Button>
          </div>
          
          )}

          {open && loading && (
            <div className="flex items-center justify-between w-full">
              <div className="w-7 h-7 rounded-full bg-gray-300 animate-pulse" />
              <div className="flex-1 ml-2 h-4 bg-gray-300 rounded animate-pulse" />
            </div>
          )}
          {open && user && (
            <div className="flex items-center justify-between w-full">
              <div className={`w-7 h-7 cursor-pointer rounded-full flex items-center justify-center font-semibold text-white text-sm ${getAvatarColor(user.full_name)} hover:shadow-lg transition-all`}>
                {user.full_name.charAt(0).toUpperCase()}
              </div>
              <div className="flex items-center justify-between flex-1 ml-2">
                <span className="text-sm font-medium text-gray-900 dark:text-white truncate max-w-[100px] transition-all duration-300">
                  {user.full_name}
                </span>
                <Link href="/settings">
                  <button className="bg-gray-100 hover:scale-110 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-full p-2 transition-all cursor-pointer">
                    <Settings size={16} className="text-black dark:text-white" />
                  </button>
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        <main className="p-8 mt-16">
        </main>
      </div>
    </div>
  );
}
