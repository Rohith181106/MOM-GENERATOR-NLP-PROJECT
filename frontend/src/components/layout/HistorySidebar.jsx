import React, { useState } from "react";
import { Plus, Search, MessageSquare, Calendar, Clock, LogOut, ChevronRight, Sparkles, FolderArchive } from "lucide-react";
import { useMeetings } from "../../context/MeetingContext";
import { useAuth } from "../../context/AuthContext";

export default function HistorySidebar({ onSelectMeeting, onNewMeeting, onOpenSearch, activeId }) {
  const { meetings, loadingMeetings } = useMeetings();
  const { user, logout } = useAuth();
  const [filterQuery, setFilterQuery] = useState("");

  const filtered = meetings.filter((m) =>
    m.title.toLowerCase().includes(filterQuery.toLowerCase())
  );

  // Group into Recent (last 7 days or first 3) vs Older
  const recentMeetings = filtered.slice(0, 4);
  const olderMeetings = filtered.slice(4);

  return (
    <aside className="w-72 h-screen flex flex-col bg-slate-900/95 border-r border-slate-800 text-slate-200 select-none z-20 shrink-0">
      {/* App Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight text-white flex items-center gap-1.5">
              MoM AI Studio
              <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">v1.0</span>
            </h1>
            <p className="text-[11px] text-slate-400">Meeting Intelligence</p>
          </div>
        </div>
      </div>

      {/* New Meeting CTA & Search */}
      <div className="p-3 space-y-2">
        <button
          onClick={onNewMeeting}
          className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white font-medium text-sm transition-all shadow-md shadow-indigo-950/50 hover:shadow-indigo-500/25 active:scale-[0.98]"
        >
          <Plus className="w-4 h-4 stroke-[2.5]" />
          <span>New Meeting</span>
        </button>

        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search meetings..."
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            onFocus={onOpenSearch}
            className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 transition-all"
          />
        </div>
      </div>

      {/* Meeting History List */}
      <div className="flex-1 overflow-y-auto px-2 py-1 space-y-4">
        {loadingMeetings && (
          <div className="text-center py-6 text-xs text-slate-400 animate-pulse">
            Loading meeting history...
          </div>
        )}

        {/* Recent Meetings */}
        <div>
          <div className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Clock className="w-3 h-3" />
            Recent Meetings
          </div>
          <div className="space-y-0.5 mt-1">
            {recentMeetings.map((meeting) => (
              <button
                key={meeting.id}
                onClick={() => onSelectMeeting(meeting.id)}
                className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-all flex items-center justify-between group ${
                  activeId === meeting.id
                    ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 font-medium"
                    : "text-slate-300 hover:bg-slate-800/70 hover:text-white"
                }`}
              >
                <div className="flex items-center space-x-2.5 min-w-0">
                  <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${activeId === meeting.id ? "text-indigo-400" : "text-slate-400 group-hover:text-slate-300"}`} />
                  <span className="truncate">{meeting.title}</span>
                </div>
                <ChevronRight className="w-3 h-3 text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity" />
              </button>
            ))}
            {recentMeetings.length === 0 && !loadingMeetings && (
              <p className="px-3 py-2 text-xs text-slate-500 italic">No meetings yet</p>
            )}
          </div>
        </div>

        {/* Older Meetings */}
        {olderMeetings.length > 0 && (
          <div>
            <div className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <FolderArchive className="w-3 h-3" />
              Older Meetings
            </div>
            <div className="space-y-0.5 mt-1">
              {olderMeetings.map((meeting) => (
                <button
                  key={meeting.id}
                  onClick={() => onSelectMeeting(meeting.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-all flex items-center justify-between group ${
                    activeId === meeting.id
                      ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 font-medium"
                      : "text-slate-400 hover:bg-slate-800/70 hover:text-white"
                  }`}
                >
                  <div className="flex items-center space-x-2.5 min-w-0">
                    <Calendar className="w-3.5 h-3.5 shrink-0 text-slate-400 group-hover:text-slate-300" />
                    <span className="truncate">{meeting.title}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* User Footer with Profile & Logout */}
      <div className="p-3 border-t border-slate-800 bg-slate-900/60 flex items-center justify-between">
        <div className="flex items-center space-x-2.5 min-w-0">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center font-bold text-xs text-white uppercase shadow">
            {user?.name ? user.name[0] : "U"}
          </div>
          <div className="min-w-0">
            <p className="text-xs font-semibold text-slate-200 truncate">{user?.name || "User"}</p>
            <p className="text-[10px] text-slate-400 truncate">{user?.email || ""}</p>
          </div>
        </div>
        <button
          onClick={logout}
          title="Sign out"
          className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
}
