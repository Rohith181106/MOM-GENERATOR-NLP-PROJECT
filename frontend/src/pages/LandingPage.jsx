import React from "react";
import { Sparkles, Mic, Upload, FileText, ShieldCheck, Database, Layers, ArrowRight, Play, Cpu, CheckCircle } from "lucide-react";
import HeroScene from "../components/3d/HeroScene";

export default function LandingPage({ onGetStarted, onStartLive, onUpload }) {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col relative overflow-hidden">
      {/* 3D Interactive Three.js Background */}
      <HeroScene />

      {/* Top Navigation */}
      <header className="relative z-10 max-w-7xl mx-auto w-full px-6 py-6 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="font-bold text-lg text-white tracking-tight">MoM AI Studio</span>
            <span className="ml-2 px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">Enterprise NLP</span>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <button
            onClick={onGetStarted}
            className="text-xs font-semibold text-slate-300 hover:text-white px-3 py-1.5 transition-colors"
          >
            Sign In
          </button>
          <button
            onClick={onGetStarted}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white font-semibold text-xs tracking-wide shadow-lg shadow-indigo-950/60 active:scale-95 transition-all"
          >
            Get Started Free
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <main className="relative z-10 flex-1 max-w-5xl mx-auto px-6 pt-16 pb-24 flex flex-col items-center text-center space-y-8">
        <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-slate-700/60 text-xs text-indigo-300 backdrop-blur-md shadow-inner">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          <span>Task-Specific Multi-Model NLP Pipeline</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight max-w-4xl">
          Automated Minutes of Meeting <br />
          <span className="bg-gradient-to-r from-indigo-400 via-purple-300 to-cyan-400 bg-clip-text text-transparent">
            Engineered with Deep ML
          </span>
        </h1>

        <p className="text-slate-400 text-sm sm:text-base max-w-2xl leading-relaxed">
          Not a generic one-shot AI prompt. A precision-built NLP pipeline integrating faster-whisper ASR,
          pyannote diarization, DeBERTa action & decision classifiers, MiniLM topic segmentation, and evidence-grounded Qwen MoM generation.
        </p>

        {/* Hero CTAs */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
          <button
            onClick={onStartLive}
            className="flex items-center space-x-2.5 px-6 py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white font-semibold text-sm shadow-xl shadow-indigo-500/25 active:scale-95 transition-all"
          >
            <Mic className="w-4 h-4" />
            <span>Start Live Meeting</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </button>

          <button
            onClick={onUpload}
            className="flex items-center space-x-2.5 px-6 py-3.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-white font-semibold text-sm border border-slate-700/80 shadow-lg active:scale-95 transition-all backdrop-blur-md"
          >
            <Upload className="w-4 h-4 text-cyan-400" />
            <span>Upload Meeting Audio/Video</span>
          </button>
        </div>

        {/* Live Feature Badges */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 w-full pt-12">
          {[
            { title: "Live Streaming ASR", desc: "faster-whisper real-time partials", icon: Mic },
            { title: "Speaker Diarization", desc: "pyannote turn-taking alignment", icon: Layers },
            { title: "DeBERTa Task Extract", desc: "Owner, deadline, and act detection", icon: Cpu },
            { title: "Persistent DB Memory", desc: "Permanent user-isolated history", icon: Database },
          ].map((feature, i) => {
            const Icon = feature.icon;
            return (
              <div key={i} className="p-4 rounded-xl glass-card text-left space-y-1.5 border border-slate-800/80">
                <Icon className="w-5 h-5 text-indigo-400" />
                <h3 className="text-xs font-bold text-white">{feature.title}</h3>
                <p className="text-[11px] text-slate-400">{feature.desc}</p>
              </div>
            );
          })}
        </div>

        {/* Pipeline Visual Flow Card */}
        <div className="w-full mt-12 p-6 rounded-2xl glass-panel border border-slate-800/80 text-left space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-2">
              <Cpu className="w-4 h-4" />
              Core NLP/ML System Architecture
            </h2>
            <span className="text-[11px] text-emerald-400 flex items-center gap-1 font-mono">
              <CheckCircle className="w-3.5 h-3.5" /> Benchmarked Pipeline
            </span>
          </div>

          <div className="flex items-center justify-between overflow-x-auto py-3 gap-2 text-xs font-medium text-slate-300">
            <span className="px-3 py-1.5 rounded-lg bg-slate-800/90 border border-slate-700">Audio Stream</span>
            <span className="text-slate-600">?</span>
            <span className="px-3 py-1.5 rounded-lg bg-indigo-950/60 border border-indigo-800 text-indigo-300">Whisper ASR</span>
            <span className="text-slate-600">?</span>
            <span className="px-3 py-1.5 rounded-lg bg-purple-950/60 border border-purple-800 text-purple-300">Diarization</span>
            <span className="text-slate-600">?</span>
            <span className="px-3 py-1.5 rounded-lg bg-cyan-950/60 border border-cyan-800 text-cyan-300">DeBERTa Classifier</span>
            <span className="text-slate-600">?</span>
            <span className="px-3 py-1.5 rounded-lg bg-emerald-950/60 border border-emerald-800 text-emerald-300">Evidence Grounding</span>
            <span className="text-slate-600">?</span>
            <span className="px-3 py-1.5 rounded-lg bg-amber-950/60 border border-amber-800 text-amber-300">Qwen MoM</span>
          </div>
        </div>
      </main>
    </div>
  );
}
