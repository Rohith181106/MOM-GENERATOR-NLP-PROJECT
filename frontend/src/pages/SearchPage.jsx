import React, { useState } from "react";
import { Search, Sparkles, Calendar, MessageSquare, ArrowRight, Database, Loader2 } from "lucide-react";
import { meetingAPI } from "../services/api";

export default function SearchPage({ onSelectMeeting }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const sampleQueries = [
    "Show my meetings about API",
    "Find meetings where Dharun had action items",
    "Find decisions related to database",
    "Sprint planning and deployment deliverables",
  ];

  const handleSearch = async (searchQuery) => {
    const q = searchQuery || query;
    if (!q.trim()) return;

    setLoading(true);
    setHasSearched(true);
    try {
      const res = await meetingAPI.search(q);
      setResults(res.data.results || []);
    } catch (err) {
      console.error("Search error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-y-auto bg-slate-950 text-slate-100 p-8">
      <div className="max-w-4xl mx-auto w-full space-y-6">
        <div className="space-y-2 text-center">
          <div className="w-12 h-12 mx-auto rounded-2xl bg-gradient-to-tr from-purple-500 to-indigo-500 flex items-center justify-center shadow-lg shadow-purple-500/30">
            <Database className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Meeting Memory & Vector Retrieval</h1>
          <p className="text-xs text-slate-400">
            Query across your meetings using FAISS semantic similarity and database text filtering.
          </p>
        </div>

        {/* Search Input Bar */}
        <div className="relative">
          <Search className="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="Ask anything (e.g. 'Show meetings about API', 'Find Dharun action items')..."
            className="w-full pl-12 pr-28 py-3.5 rounded-2xl bg-slate-900 border border-slate-700/80 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/30 shadow-xl transition-all"
          />
          <button
            onClick={() => handleSearch()}
            disabled={loading || !query.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-all shadow-md active:scale-95 disabled:opacity-50 flex items-center gap-1.5"
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <span>Search</span>}
          </button>
        </div>

        {/* Sample query pills */}
        <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
          <span className="text-[11px] text-slate-400 mr-1">Suggestions:</span>
          {sampleQueries.map((sq, i) => (
            <button
              key={i}
              onClick={() => {
                setQuery(sq);
                handleSearch(sq);
              }}
              className="px-3 py-1 rounded-full bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-[11px] text-slate-300 transition-colors"
            >
              {sq}
            </button>
          ))}
        </div>

        {/* Search Results List */}
        <div className="space-y-3 pt-4">
          {loading && (
            <div className="text-center py-12 text-xs text-slate-400 flex items-center justify-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
              <span>Scanning semantic vector space and meeting records...</span>
            </div>
          )}

          {!loading && hasSearched && results.length === 0 && (
            <div className="text-center py-12 text-xs text-slate-400 p-8 rounded-2xl glass-card border border-slate-800">
              <p>No meeting records matched your query.</p>
              <p className="text-[11px] text-slate-400 mt-1">Try another keyword or broader topic.</p>
            </div>
          )}

          {!loading && results.map((res, idx) => (
            <div
              key={idx}
              onClick={() => onSelectMeeting(res.id)}
              className="p-5 rounded-2xl glass-card hover:bg-slate-800/60 border border-slate-800 transition-all cursor-pointer space-y-2 group"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2.5">
                  <h3 className="font-bold text-sm text-white group-hover:text-indigo-300 transition-colors">
                    {res.title}
                  </h3>
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                    {res.match_type}
                  </span>
                </div>
                <span className="text-[11px] font-mono text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded">
                  Score: {Math.round(res.similarity * 100)}%
                </span>
              </div>

              <p className="text-xs text-slate-300 bg-slate-900/60 p-3 rounded-xl border border-slate-800/60 leading-relaxed italic">
                "{res.snippet}"
              </p>

              <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                <span>Meeting ID: #{res.id} • {res.date || "2026-09-08"}</span>
                <span className="text-indigo-400 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                  Open Workspace <ArrowRight className="w-3 h-3" />
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
