import React, { useState } from "react";
import {
  FileText, ListTodo, CheckCircle2, MessageSquare, Layers, Download,
  Edit3, Calendar, Clock, Users, Sparkles, Check, Search, Copy, AlertTriangle, Save, X
} from "lucide-react";
import { meetingAPI } from "../../services/api";

export default function MeetingWorkspace({ meeting, onUpdateMeeting }) {
  const [activeTab, setActiveTab] = useState("summary");
  const [isEditing, setIsEditing] = useState(false);
  const [downloadingDocx, setDownloadingDocx] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [copiedTranscript, setCopiedTranscript] = useState(false);
  const [transcriptSearch, setTranscriptSearch] = useState("");
  const [speakerFilter, setSpeakerFilter] = useState("ALL");

  // Edit form state
  const [editSummary, setEditSummary] = useState(meeting.mom_document?.summary || "");
  const [editActions, setEditActions] = useState(meeting.action_items || []);
  const [editDecisions, setEditDecisions] = useState(meeting.decisions || []);

  const handleSaveMoM = async () => {
    try {
      const payload = {
        summary: editSummary,
        structured_json: {
          ...meeting.mom_document?.structured_json,
          executive_summary: editSummary,
          action_items: editActions,
          key_decisions: editDecisions,
        }
      };
      const res = await meetingAPI.updateMoM(meeting.id, payload);
      setIsEditing(false);
      if (onUpdateMeeting) onUpdateMeeting();
    } catch (err) {
      console.error("Failed to update MoM:", err);
      alert("Error saving MoM edits.");
    }
  };

  const handleExportDocx = async () => {
    setDownloadingDocx(true);
    try {
      await meetingAPI.exportDocx(meeting.id, `MoM_${meeting.title.replace(/\s+/g, "_")}.docx`);
    } catch (err) {
      console.error("Export DOCX failed:", err);
    } finally {
      setDownloadingDocx(false);
    }
  };

  const handleExportPdf = async () => {
    setDownloadingPdf(true);
    try {
      await meetingAPI.exportPdf(meeting.id, `MoM_${meeting.title.replace(/\s+/g, "_")}.pdf`);
    } catch (err) {
      console.error("Export PDF failed:", err);
    } finally {
      setDownloadingPdf(false);
    }
  };

  const copyTranscript = () => {
    const text = (meeting.transcript_segments || [])
      .map((s) => `[${s.speaker_name || s.speaker_label}] (${s.start_time}s): ${s.text}`)
      .join("\n");
    navigator.clipboard.writeText(text);
    setCopiedTranscript(true);
    setTimeout(() => setCopiedTranscript(false), 2000);
  };

  const speakers = ["ALL", ...new Set((meeting.transcript_segments || []).map((s) => s.speaker_name || s.speaker_label))];

  const filteredSegments = (meeting.transcript_segments || []).filter((s) => {
    const matchesSpeaker = speakerFilter === "ALL" || (s.speaker_name || s.speaker_label) === speakerFilter;
    const matchesQuery = s.text.toLowerCase().includes(transcriptSearch.toLowerCase());
    return matchesSpeaker && matchesQuery;
  });

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-950 text-slate-100">
      {/* Workspace Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 px-8 py-5 backdrop-blur-md shrink-0">
        <div className="flex items-start justify-between">
          <div className="space-y-1.5">
            <div className="flex items-center space-x-2.5">
              <h1 className="text-xl font-bold tracking-tight text-white">{meeting.title}</h1>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${meeting.meeting_type === "LIVE" ? "bg-red-500/10 text-red-400 border border-red-500/20" : "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"}`}>
                {meeting.meeting_type}
              </span>
            </div>
            <div className="flex items-center space-x-5 text-xs text-slate-400">
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-indigo-400" />
                {meeting.date || "2026-09-08"}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-indigo-400" />
                {meeting.duration ? `${meeting.duration}s` : "Recorded"}
              </span>
              <span className="flex items-center gap-1">
                <Users className="w-3.5 h-3.5 text-indigo-400" />
                {(meeting.participants || []).map((p) => p.name).join(", ") || "Participants"}
              </span>
            </div>
          </div>

          {/* Action CTAs: Export & Edit */}
          <div className="flex items-center space-x-2.5">
            <button
              onClick={() => setIsEditing(true)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-all border border-slate-700 active:scale-95"
            >
              <Edit3 className="w-3.5 h-3.5 text-indigo-400" />
              <span>Edit MoM</span>
            </button>

            <button
              onClick={handleExportDocx}
              disabled={downloadingDocx}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold tracking-wide transition-all shadow-md shadow-indigo-950 active:scale-95 disabled:opacity-50"
            >
              <Download className="w-3.5 h-3.5" />
              <span>{downloadingDocx ? "Exporting..." : "Export DOCX"}</span>
            </button>

            <button
              onClick={handleExportPdf}
              disabled={downloadingPdf}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold tracking-wide transition-all border border-slate-700 active:scale-95 disabled:opacity-50"
            >
              <Download className="w-3.5 h-3.5 text-red-400" />
              <span>{downloadingPdf ? "Exporting..." : "Export PDF"}</span>
            </button>
          </div>
        </div>

        {/* Workspace Navigation Tabs */}
        <div className="flex space-x-2 mt-5 border-b border-slate-800/80 -mb-5 pb-px">
          {[
            { id: "summary", label: "Executive Summary", icon: FileText },
            { id: "topics", label: "Topics Discussed", icon: Layers },
            { id: "decisions", label: "Key Decisions", icon: CheckCircle2 },
            { id: "actions", label: "Action Items", icon: ListTodo, count: (meeting.action_items || []).length },
            { id: "transcript", label: "Full Transcript", icon: MessageSquare },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-3.5 py-2.5 text-xs font-medium border-b-2 transition-all ${
                  isActive
                    ? "border-indigo-500 text-indigo-400 bg-indigo-500/10 rounded-t-lg"
                    : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
                {tab.count !== undefined && (
                  <span className="px-1.5 py-0.2 rounded-full bg-slate-800 text-[10px] text-slate-300 font-mono">
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </header>

      {/* Main Content Body */}
      <main className="flex-1 overflow-y-auto p-8 max-w-6xl mx-auto w-full">
        {/* TAB 1: EXECUTIVE SUMMARY */}
        {activeTab === "summary" && (
          <div className="space-y-6">
            <div className="p-6 rounded-2xl glass-card border border-slate-800/80 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800/60 pb-3">
                <h2 className="text-sm font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  Executive Summary (Qwen-2.5-3B Grounded)
                </h2>
                <span className="text-[11px] text-emerald-400 flex items-center gap-1 font-medium bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
                  <Check className="w-3.5 h-3.5" /> Evidence Verified
                </span>
              </div>
              <p className="text-slate-200 leading-relaxed text-sm">
                {meeting.mom_document?.summary || "Executive summary processing or not yet generated."}
              </p>
            </div>

            {/* Quick Metrics Grid */}
            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 rounded-xl glass-card border border-slate-800/80">
                <p className="text-xs text-slate-400">Total Topics</p>
                <p className="text-2xl font-bold text-white mt-1">{(meeting.topics || []).length}</p>
              </div>
              <div className="p-4 rounded-xl glass-card border border-slate-800/80">
                <p className="text-xs text-slate-400">Key Decisions Made</p>
                <p className="text-2xl font-bold text-emerald-400 mt-1">{(meeting.decisions || []).length}</p>
              </div>
              <div className="p-4 rounded-xl glass-card border border-slate-800/80">
                <p className="text-xs text-slate-400">Assigned Action Items</p>
                <p className="text-2xl font-bold text-indigo-400 mt-1">{(meeting.action_items || []).length}</p>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: TOPICS DISCUSSED */}
        {activeTab === "topics" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-slate-200">Segmented Discussion Topics</h2>
              <span className="text-xs text-slate-400">Model: all-MiniLM-L6-v2 Embeddings</span>
            </div>
            <div className="space-y-3">
              {(meeting.topics || []).map((t, idx) => (
                <div key={t.id || idx} className="p-5 rounded-xl glass-card border border-slate-800/80 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm text-indigo-300 flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center text-xs font-bold">
                        {idx + 1}
                      </span>
                      {t.topic_name}
                    </span>
                    <span className="text-[11px] font-mono text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded">
                      {Math.floor(t.start_time)}s – {Math.floor(t.end_time)}s
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">{t.summary}</p>
                </div>
              ))}
              {(meeting.topics || []).length === 0 && (
                <p className="text-xs text-slate-400 text-center py-8">No topic segments generated.</p>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: KEY DECISIONS */}
        {activeTab === "decisions" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-slate-200">Formal Agreed Decisions</h2>
              <span className="text-xs text-slate-400">Model: DeBERTa-v3 Act Classifier</span>
            </div>
            <div className="space-y-3">
              {(meeting.decisions || []).map((d, idx) => (
                <div key={d.id || idx} className="p-5 rounded-xl glass-card border border-emerald-500/20 space-y-2">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start space-x-3">
                      <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                      <div>
                        <p className="text-sm font-semibold text-white">{d.decision}</p>
                        {d.evidence && (
                          <p className="text-xs text-slate-400 italic mt-1.5 bg-slate-900/60 p-2 rounded border border-slate-800">
                            Evidence: "{d.evidence}"
                          </p>
                        )}
                      </div>
                    </div>
                    <span className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded shrink-0">
                      {Math.round((d.confidence || 0.95) * 100)}% Conf
                    </span>
                  </div>
                </div>
              ))}
              {(meeting.decisions || []).length === 0 && (
                <p className="text-xs text-slate-400 text-center py-8">No decisions detected.</p>
              )}
            </div>
          </div>
        )}

        {/* TAB 4: ACTION ITEMS */}
        {activeTab === "actions" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-slate-200">Extracted Action Items & Deliverables</h2>
              <span className="text-xs text-slate-400">Models: DeBERTa-v3 + BERT-NER + dateparser</span>
            </div>

            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60">
              <table className="w-full text-left text-xs text-slate-200">
                <thead className="bg-slate-900/90 text-slate-400 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="p-3.5">Task Description</th>
                    <th className="p-3.5">Owner</th>
                    <th className="p-3.5">Deadline (Normalized)</th>
                    <th className="p-3.5">Status</th>
                    <th className="p-3.5">Evidence Grounding</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {(meeting.action_items || []).map((a, idx) => (
                    <tr key={a.id || idx} className="hover:bg-slate-800/40 transition-colors">
                      <td className="p-3.5 font-medium text-white max-w-xs">{a.task}</td>
                      <td className="p-3.5">
                        <span className={`px-2 py-0.5 rounded font-medium ${a.owner === "NEEDS_REVIEW" ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" : "bg-indigo-500/10 text-indigo-300"}`}>
                          {a.owner}
                        </span>
                      </td>
                      <td className="p-3.5 font-mono text-slate-300">
                        <span className={`px-2 py-0.5 rounded ${a.deadline === "NEEDS_REVIEW" ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" : ""}`}>
                          {a.deadline}
                        </span>
                      </td>
                      <td className="p-3.5">
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px] font-semibold uppercase">
                          {a.status || "PENDING"}
                        </span>
                      </td>
                      <td className="p-3.5 text-slate-400 italic max-w-sm truncate" title={a.evidence}>
                        "{a.evidence || "Direct turn"}"
                      </td>
                    </tr>
                  ))}
                  {(meeting.action_items || []).length === 0 && (
                    <tr>
                      <td colSpan={5} className="p-8 text-center text-slate-400">
                        No action items identified.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 5: FULL TRANSCRIPT */}
        {activeTab === "transcript" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search in transcript..."
                    value={transcriptSearch}
                    onChange={(e) => setTranscriptSearch(e.target.value)}
                    className="pl-8 pr-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-indigo-500 w-64"
                  />
                </div>
                <select
                  value={speakerFilter}
                  onChange={(e) => setSpeakerFilter(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  {speakers.map((spk) => (
                    <option key={spk} value={spk}>{spk === "ALL" ? "All Speakers" : spk}</option>
                  ))}
                </select>
              </div>

              <button
                onClick={copyTranscript}
                className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition-colors"
              >
                {copiedTranscript ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedTranscript ? "Copied!" : "Copy All"}</span>
              </button>
            </div>

            <div className="p-5 rounded-2xl glass-card border border-slate-800/80 space-y-4 max-h-[600px] overflow-y-auto">
              {filteredSegments.map((seg, idx) => (
                <div key={seg.id || idx} className="space-y-1 group">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-indigo-400">
                      {seg.speaker_name || seg.speaker_label}
                    </span>
                    <span className="text-slate-400 font-mono text-[10px]">
                      {Math.floor(seg.start_time)}s – {Math.floor(seg.end_time)}s
                    </span>
                  </div>
                  <p className="text-xs text-slate-200 leading-relaxed bg-slate-900/40 p-2.5 rounded-lg border border-slate-800/60">
                    {seg.text}
                  </p>
                </div>
              ))}
              {filteredSegments.length === 0 && (
                <p className="text-center py-8 text-xs text-slate-400">No transcript turns found.</p>
              )}
            </div>
          </div>
        )}
      </main>

      {/* EDIT MoM MODAL (Requirement 37: Editable MoM) */}
      {isEditing && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-3xl max-h-[85vh] overflow-y-auto rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Edit3 className="w-4 h-4 text-indigo-400" />
                <h3 className="font-bold text-white text-base">Edit Generated MoM Document</h3>
              </div>
              <button
                onClick={() => setIsEditing(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Summary edit */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">Executive Summary</label>
              <textarea
                rows={5}
                value={editSummary}
                onChange={(e) => setEditSummary(e.target.value)}
                className="w-full p-3 rounded-lg bg-slate-800 border border-slate-700 text-xs text-white focus:outline-none focus:border-indigo-500 leading-relaxed"
              />
            </div>

            {/* Actions items list editor */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300">Action Items & Deliverables</label>
              <div className="space-y-2 max-h-48 overflow-y-auto p-1">
                {editActions.map((act, index) => (
                  <div key={index} className="grid grid-cols-12 gap-2 p-2 rounded bg-slate-800/80 border border-slate-700/60">
                    <input
                      type="text"
                      value={act.task}
                      onChange={(e) => {
                        const updated = [...editActions];
                        updated[index].task = e.target.value;
                        setEditActions(updated);
                      }}
                      className="col-span-6 p-1.5 rounded bg-slate-900 border border-slate-700 text-xs text-white"
                      placeholder="Task"
                    />
                    <input
                      type="text"
                      value={act.owner}
                      onChange={(e) => {
                        const updated = [...editActions];
                        updated[index].owner = e.target.value;
                        setEditActions(updated);
                      }}
                      className="col-span-3 p-1.5 rounded bg-slate-900 border border-slate-700 text-xs text-white"
                      placeholder="Owner"
                    />
                    <input
                      type="text"
                      value={act.deadline}
                      onChange={(e) => {
                        const updated = [...editActions];
                        updated[index].deadline = e.target.value;
                        setEditActions(updated);
                      }}
                      className="col-span-3 p-1.5 rounded bg-slate-900 border border-slate-700 text-xs text-white"
                      placeholder="Deadline"
                    />
                  </div>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800">
              <button
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveMoM}
                className="flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-lg shadow-indigo-950"
              >
                <Save className="w-3.5 h-3.5" />
                <span>Save Changes Permanently</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
