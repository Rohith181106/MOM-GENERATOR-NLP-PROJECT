import React, { useState, useEffect } from "react";
import { CheckCircle, Circle, Loader2, Sparkles, ArrowRight } from "lucide-react";

export default function ProcessingTracker({ onComplete }) {
  const stages = [
    { id: 1, label: "Audio Preprocessing & Ingestion", duration: 800 },
    { id: 2, label: "Speech-to-Text Recognition (faster-whisper)", duration: 1100 },
    { id: 3, label: "Speaker Diarization & Audio Segmentation", duration: 900 },
    { id: 4, label: "Transcript + Speaker Alignment", duration: 700 },
    { id: 5, label: "Action Item Detection (DeBERTa-v3)", duration: 900 },
    { id: 6, label: "Decision & Act Classification (DeBERTa-v3)", duration: 800 },
    { id: 7, label: "Owner & Deadline Resolution (Normalized)", duration: 700 },
    { id: 8, label: "Semantic Topic Segmentation (all-MiniLM-L6-v2)", duration: 800 },
    { id: 9, label: "MoM Synthesis & Evidence Grounding (Qwen)", duration: 1100 },
  ];

  const [currentStageIndex, setCurrentStageIndex] = useState(0);

  useEffect(() => {
    if (currentStageIndex < stages.length) {
      const timer = setTimeout(() => {
        setCurrentStageIndex((prev) => prev + 1);
      }, stages[currentStageIndex].duration);
      return () => clearTimeout(timer);
    } else {
      const finishTimer = setTimeout(() => {
        if (onComplete) onComplete();
      }, 700);
      return () => clearTimeout(finishTimer);
    }
  }, [currentStageIndex]);

  const progressPercent = Math.min(100, Math.round((currentStageIndex / stages.length) * 100));

  return (
    <div className="max-w-xl mx-auto my-12 p-8 rounded-2xl glass-panel shadow-2xl border border-slate-800 text-center space-y-6 animate-in fade-in zoom-in-95 duration-500">
      <div className="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-tr from-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/30">
        <Sparkles className="w-7 h-7 text-white animate-spin" style={{ animationDuration: "6s" }} />
      </div>

      <div className="space-y-1.5">
        <h2 className="text-xl font-bold text-white tracking-tight">AI Pipeline Processing</h2>
        <p className="text-xs text-slate-400">
          Running task-specific NLP models to transcribe, diarize, and generate Minutes of Meeting.
        </p>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden p-0.5">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-cyan-400 rounded-full transition-all duration-300"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <div className="flex justify-between text-[11px] font-mono text-slate-400">
          <span>{progressPercent}% Completed</span>
          <span>Stage {Math.min(stages.length, currentStageIndex + 1)} of {stages.length}</span>
        </div>
      </div>

      {/* Stages List */}
      <div className="text-left space-y-2.5 pt-2">
        {stages.map((stage, idx) => {
          const isDone = idx < currentStageIndex;
          const isCurrent = idx === currentStageIndex;

          return (
            <div
              key={stage.id}
              className={`flex items-center space-x-3 text-xs p-2 rounded-lg transition-colors ${
                isCurrent
                  ? "bg-indigo-600/20 text-indigo-200 font-medium border border-indigo-500/30"
                  : isDone
                  ? "text-slate-300"
                  : "text-slate-400"
              }`}
            >
              {isDone ? (
                <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
              ) : isCurrent ? (
                <Loader2 className="w-4 h-4 text-indigo-400 animate-spin shrink-0" />
              ) : (
                <Circle className="w-4 h-4 text-slate-600 shrink-0" />
              )}
              <span>{stage.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
