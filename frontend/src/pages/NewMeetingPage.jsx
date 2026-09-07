import React, { useState } from "react";
import { Mic, Upload, Calendar, Clock, Users, ArrowRight, Sparkles } from "lucide-react";
import { meetingAPI } from "../services/api";

export default function NewMeetingPage({ onStartLive, onUploadRecording }) {
  const [meetingType, setMeetingType] = useState("LIVE");
  const [title, setTitle] = useState("Sprint Planning & Architecture Sync");
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [participants, setParticipants] = useState("Rohith, Dharun, Priya, Rahul");
  const [loading, setLoading] = useState(false);

  const handleCreate = async () => {
    if (!title.trim()) return;
    setLoading(true);
    try {
      const roster = participants.split(",").map((p) => p.trim()).filter(Boolean);
      const res = await meetingAPI.create({
        title,
        date,
        meeting_type: meetingType,
        participants: roster
      });
      if (meetingType === "LIVE") {
        onStartLive(res.data);
      } else {
        onUploadRecording(res.data);
      }
    } catch (err) {
      console.error("Create meeting error:", err);
      alert("Failed to initialize meeting session.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-y-auto bg-slate-950 text-slate-100 p-8">
      <div className="max-w-2xl mx-auto w-full my-auto space-y-6">
        <div className="space-y-2 text-center">
          <div className="w-12 h-12 mx-auto rounded-2xl bg-gradient-to-tr from-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Initiate New Meeting</h1>
          <p className="text-xs text-slate-400">
            Select meeting type and configure session metadata for precise speaker attribution.
          </p>
        </div>

        {/* Meeting Type Selection */}
        <div className="grid grid-cols-2 gap-4">
          <div
            onClick={() => setMeetingType("LIVE")}
            className={`p-5 rounded-2xl border cursor-pointer transition-all flex flex-col items-center text-center space-y-2 ${
              meetingType === "LIVE"
                ? "bg-indigo-600/20 border-indigo-500 shadow-xl shadow-indigo-950/60"
                : "bg-slate-900/60 border-slate-800 hover:border-slate-700"
            }`}
          >
            <div className="p-3 rounded-full bg-red-500/10 text-red-400 border border-red-500/20">
              <Mic className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-bold text-white">Start Live Meeting</h3>
            <p className="text-[11px] text-slate-400">
              Conduct live session with microphone audio and real-time live transcript.
            </p>
          </div>

          <div
            onClick={() => setMeetingType("UPLOAD")}
            className={`p-5 rounded-2xl border cursor-pointer transition-all flex flex-col items-center text-center space-y-2 ${
              meetingType === "UPLOAD"
                ? "bg-indigo-600/20 border-indigo-500 shadow-xl shadow-indigo-950/60"
                : "bg-slate-900/60 border-slate-800 hover:border-slate-700"
            }`}
          >
            <div className="p-3 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <Upload className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-bold text-white">Upload Recording</h3>
            <p className="text-[11px] text-slate-400">
              Ingest recorded MP3, WAV, M4A, MP4, or WebM meeting files.
            </p>
          </div>
        </div>

        {/* Metadata Form */}
        <div className="p-6 rounded-2xl glass-panel border border-slate-800/80 space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300">Meeting Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Sprint Planning & Architecture Sync"
              className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">Meeting Date</label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">Participant Roster (Comma-separated)</label>
              <input
                type="text"
                value={participants}
                onChange={(e) => setParticipants(e.target.value)}
                placeholder="Rohith, Dharun, Priya, Rahul"
                className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <button
            onClick={handleCreate}
            disabled={loading || !title.trim()}
            className="w-full mt-2 flex items-center justify-center space-x-2 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white font-semibold text-xs tracking-wide shadow-xl shadow-indigo-950 active:scale-95 transition-all disabled:opacity-50"
          >
            <span>{meetingType === "LIVE" ? "Launch Live Meeting Room" : "Proceed to File Upload"}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
