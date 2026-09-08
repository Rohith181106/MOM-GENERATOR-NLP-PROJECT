import React, { useState } from "react";
import { Upload, FileAudio, Check, AlertCircle, ArrowRight, Loader2, Sparkles } from "lucide-react";
import { meetingAPI } from "../services/api";

export default function UploadMeetingPage({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState("");
  const [participants, setParticipants] = useState("");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      setError("");
      if (!title) {
        setTitle(selected.name.replace(/\.[^/.]+$/, ""));
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a meeting audio or video file.");
      return;
    }

    setUploading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("title", title.trim() || file.name.replace(/\.[^/.]+$/, ""));
      if (participants.trim()) {
        formData.append("participants", participants.trim());
      }

      const res = await meetingAPI.upload(formData);
      if (onUploadSuccess) {
        onUploadSuccess(res.data);
      }
    } catch (err) {
      console.error("Upload error:", err);
      setError(err.response?.data?.detail || "Upload failed. Check audio format.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-y-auto bg-slate-950 text-slate-100 p-8">
      <div className="max-w-2xl mx-auto w-full my-auto space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 mx-auto rounded-2xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/30">
            <Upload className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Upload Previous Meeting</h1>
          <p className="text-xs text-slate-400">
            Ingest meeting recordings for speech recognition, speaker diarization, and MoM generation.
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="p-6 rounded-2xl glass-panel border border-slate-800/80 space-y-5">
          {/* Drag & Drop File Zone */}
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300">Recording File (MP3, WAV, M4A, MP4, WebM)</label>
            <div className="relative border-2 border-dashed border-slate-700 hover:border-indigo-500/60 rounded-2xl p-8 text-center transition-colors bg-slate-900/40">
              <input
                type="file"
                accept=".mp3,.wav,.m4a,.mp4,.webm"
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <div className="flex flex-col items-center space-y-2">
                <div className="p-3 rounded-xl bg-slate-800 text-indigo-400">
                  <FileAudio className="w-8 h-8" />
                </div>
                {file ? (
                  <div className="space-y-1">
                    <p className="text-xs font-bold text-emerald-400 flex items-center justify-center gap-1">
                      <Check className="w-3.5 h-3.5" /> {file.name}
                    </p>
                    <p className="text-[11px] text-slate-400">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                  </div>
                ) : (
                  <div>
                    <p className="text-xs font-semibold text-white">Click or drag & drop meeting audio</p>
                    <p className="text-[11px] text-slate-400 mt-0.5">Supports MP3, WAV, M4A, MP4, WebM up to 500MB</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300">Meeting Title</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Sprint Architecture Sync"
              className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300">Participants (Optional Roster Mapping)</label>
            <input
              type="text"
              value={participants}
              onChange={(e) => setParticipants(e.target.value)}
              placeholder="e.g. Alice, Bob, Charlie (Leave blank for auto-detected speakers)"
              className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <button
            type="submit"
            disabled={uploading}
            className="w-full flex items-center justify-center space-x-2 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white font-semibold text-xs tracking-wide shadow-xl shadow-indigo-950 active:scale-95 transition-all disabled:opacity-50"
          >
            {uploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Uploading & Processing AI Pipeline...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Upload & Generate MoM</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
