"use client";

import SettingsSideBar from "@/components/SettingsSideNavBar";
import AccountDetailsPanel from "@/components/AccountDetailsPanel";

export default function SettingsDetailPage() {
  return (
    <div className="flex bg-[#fcfbf7] min-h-screen">
      <SettingsSideBar />
      <AccountDetailsPanel />
    </div>
  );
}
