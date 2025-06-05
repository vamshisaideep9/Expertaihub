"use client";
import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import ResponsiveSidebar from "@/components/ResponsiveSidebar";
import apiPrivate from "@/lib/apiprivate";
import {
  Search,
  Sliders,
  User,
  Brain,
  ChevronDown,
  Globe,
  Check,
} from "lucide-react";

type Advisor = {
  id: number;
  name: string;
  slug: string;
  description: string;
  is_active: boolean;
  country: string;
};

type Country = {
  id: number;
  name: string;
  code: string;
  is_active: boolean;
  advisors: Omit<Advisor, "country">[];
};

export default function AdvisorsPage() {
  const [advisors, setAdvisors] = useState<Advisor[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterOpen, setFilterOpen] = useState(false);
  const [nicheMenuOpen, setNicheMenuOpen] = useState(false);
  const [countryMenuOpen, setCountryMenuOpen] = useState(false);
  const [selectedNiches, setSelectedNiches] = useState<string[]>([]);
  const [selectedCountries, setSelectedCountries] = useState<string[]>([]);
  const [hoveredAdvisorId, setHoveredAdvisorId] = useState<number | null>(null);
  const filterRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Fetch and flatten
  useEffect(() => {
    apiPrivate
      .get<Country[]>("/country/")
      .then((res) => {
        const flat: Advisor[] = res.data.flatMap((country) =>
          country.advisors.map((adv) => ({ ...adv, country: country.name }))
        );
        setAdvisors(flat);
      })
      .catch(console.error);
  }, []);

  // close filters on outside click
  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (filterOpen && filterRef.current && !filterRef.current.contains(e.target as Node)) {
        setFilterOpen(false);
        setNicheMenuOpen(false);
        setCountryMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [filterOpen]);

  // build lists
  const niches = Array.from(new Set(advisors.map((a) => a.name)));
  const countries = Array.from(new Set(advisors.map((a) => a.country)));

  // filter
  const filteredAdvisors = advisors.filter((advisor) => {
    const t = searchTerm.toLowerCase();
    const okSearch =
      advisor.name.toLowerCase().includes(t) ||
      advisor.description.toLowerCase().includes(t);
    const okNiche = selectedNiches.length === 0 || selectedNiches.includes(advisor.name);
    const okCountry = selectedCountries.length === 0 || selectedCountries.includes(advisor.country);
    return okSearch && okNiche && okCountry;
  });


  const countryToIso: Record<string,string> = {
    USA: "us",
    CANADA: "ca",
    INDIA: "in",
    // …etc
  }
  // toggles
  const toggleNiche = (n: string) =>
    setSelectedNiches((prev) =>
      prev.includes(n) ? prev.filter((x) => x !== n) : [...prev, n]
    );
  const toggleCountry = (c: string) =>
    setSelectedCountries((prev) =>
      prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]
    );
  const clearFilters = () => {
    setSelectedNiches([]);
    setSelectedCountries([]);
  };

  return (
    <div className="flex bg-[#fcfbf7] min-h-screen">
      <ResponsiveSidebar />

      <main className="ml-10 flex-1 flex flex-col">
        {/* HEADER */}
        <div className="sticky top-0 z-10 bg-[#fcfbf7] border-b border-gray-200 h-[60px] flex items-center">
          <div className="max-w-5xl w-full mx-auto px-6 flex items-center justify-between">
            <h1 className="flex items-center text-3xl font-serif text-gray-900">
              <User className="w-7 h-7 mr-4" /> Advisors
            </h1>
            <div className="flex items-center space-x-4">
              {/* Search */}
              <div className="relative w-full max-w-sm">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-800 w-5 h-5" />
                <input
                  className="w-full pl-12 pr-40 h-10 bg-[#fcfbf7] border border-gray-600 rounded-full focus:ring-0 focus:border-gray-300"
                  placeholder="Search your advisors…"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              {/* Filters */}
              <div className="relative inline-block" ref={filterRef}>
                <Sliders
                  className="w-6 h-6 text-gray-700 hover:text-gray-900 cursor-pointer hover:bg-gray-100 rounded"
                  onClick={() => setFilterOpen((o) => !o)}
                />
                {filterOpen && (
                  <div className="absolute right-0 mt-2 w-64 bg-[#fcfbf7] border border-gray-200 rounded-2xl shadow-lg p-4 space-y-4 z-30">
                    {/* Clear */}
                    <div className="pt-2 border-t border-gray-200 text-right">
                      <button
                        onClick={clearFilters}
                        className="text-sm text-blue-600 hover:underline"
                      >
                        Clear filters
                      </button>
                    </div>

                

                    {/* Country */}
                    <div className="relative">
  <button
    onClick={() => {
      setCountryMenuOpen((o) => !o);
      setNicheMenuOpen(false);
    }}
    className="w-full flex justify-between items-center px-3 py-2 border border-gray-300 rounded-md bg-[#fcfbf7]"
  >
    <Globe className="w-4 h-4 mr-2 text-gray-700" />
    <span className="text-sm text-gray-800 mr-[3.8rem]">Select Country</span>
    <ChevronDown
      size={16}
      className={`text-gray-500 transform transition ${
        countryMenuOpen ? "rotate-180" : ""
      }`}
    />
  </button>
  {countryMenuOpen && (
    <div className="absolute left-0 top-full mt-1 w-full bg-[#fcfbf7] border border-gray-200 rounded-md shadow-sm max-h-40 overflow-auto z-20 divide-y divide-gray-100">
      {countries.map((c) => {
        const iso = countryToIso[c] ?? c.toLowerCase().slice(0,2);
        return (
          <div
            key={c}
            onClick={() => toggleCountry(c)}
            className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer"
          >
            <span className={`fi fi-${iso} w-3 h-3 mr-2`} />
            <span className="text-sm flex-1 text-gray-800">{c}</span>
            {selectedCountries.includes(c) && (
              <Check className="text-green-600 w-4 h-4" />
            )}
          </div>
        );
      })}
    </div>
  )}
</div>

                    <div className="relative">
                      <button
                        onClick={() => {
                          setNicheMenuOpen((o) => !o);
                          setCountryMenuOpen(false);
                        }}
                        className="w-full flex justify-between items-center px-3 py-2 border border-gray-300 rounded-md bg-[#fcfbf7]"
                      >
                        <span className="flex items-center space-x-2">
                          <Brain className="w-4 h-4 text-gray-700" />
                          <span className="text-sm text-gray-800">Select Advisor</span>
                        </span>
                        <ChevronDown
                          size={16}
                          className={`text-gray-500 transform transition ${
                            nicheMenuOpen ? "rotate-180" : ""
                          }`}
                        />
                      </button>
                      {nicheMenuOpen && (
                        <div className="absolute left-0 top-full mt-1 w-full bg-[#fcfbf7] border border-gray-200 rounded-md shadow-sm max-h-40 overflow-auto z-20 divide-y divide-gray-100">
                          {niches.map((n) => (
                            <div
                              key={n}
                              onClick={() => toggleNiche(n)}
                              className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer"
                            >
                              <Brain className="w-4 h-4 mr-2 text-gray-700" />
                              <span className="text-sm flex-1 text-gray-800">{n}</span>
                              {selectedNiches.includes(n) && (
                                <Check className="text-green-600 w-4 h-4" />
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* CARDS GRID */}
        <div className="max-w-6xl w-full mx-auto p-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
  {filteredAdvisors.map((advisor) => (
    <div
      key={advisor.id}
      className="relative flex flex-col bg-[#fcfbf7] dark:bg-gray-800
                 border border-gray-200 dark:border-gray-700 rounded-2xl
                 p-6 shadow hover:shadow-lg transition"
    >
      {/* Active/Inactive indicator */}
      <div className="absolute top-4 right-4">
        {advisor.is_active ? (
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
          </span>
        ) : (
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
          </span>
        )}
      </div>

      {/* Title row */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center space-x-2">
          <Brain className="w-5 h-5 text-gray-700 mt-1" />
          <h2 className="text-xl font-base font-cormorant text-gray-900 dark:text-gray-100 mt-1">
            {advisor.name}
          </h2>
        </div>
        <div className="flex items-center space-x-2 text-gray-700 dark:text-gray-300">
        <span
      className={`fi fi-${countryToIso[advisor.country] ?? advisor.country} w-3 h-3 mt-2`}
    />
          <span className="text-sm font-base font-cormorant text-gray-900 mt-2">
            {advisor.country}
          </span>
        </div>
      </div>

      {/* Description (always clamped to 3 lines) */}
      <p className="text-sm text-gray-600 dark:text-gray-400 flex-1 mb-6 line-clamp-3">
        {advisor.description ||
          "Expert guidance on your questions, tailored just for you."}
      </p>

      {/* Continue button */}
      <button
        onClick={() => advisor.is_active && router.push(`/home/?advisor=${advisor.slug}`)}
        disabled={!advisor.is_active}
        className="mt-auto px-4 py-2 bg-indigo-600 text-white font-medium rounded-lg
                   hover:bg-indigo-700 transition
                   disabled:bg-gray-400 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Continue to Chat
      </button>
    </div>
  ))}
</div>
      </main>
    </div>
  );
}
