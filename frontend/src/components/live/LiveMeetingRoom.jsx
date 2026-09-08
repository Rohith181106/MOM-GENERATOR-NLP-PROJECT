import React, { useState, useEffect, useRef } from "react";
import {
  Mic, MicOff, Video, VideoOff, Monitor, Users, PhoneOff,
  Search, Copy, Check, Sparkles, AlertCircle, ArrowDownCircle,
  Clock, ShieldCheck, CheckCircle2, ChevronRight
} from "lucide-react";
import { meetingAPI } from "../../services/api";

export default function LiveMeetingRoom({ meeting, onEndMeeting }) {
  const [micEnabled, setMicEnabled] = useState(true);
  const [cameraEnabled, setCameraEnabled] = useState(true);
  const [screenSharing, setScreenSharing] = useState(false);
  const [meetingTimer, setMeetingTimer] = useState(0);
  const [transcriptSegments, setTranscriptSegments] = useState(meeting.transcript_segments || []);
  const [interimText, setInterimText] = useState("");
  const [interimSpeaker, setInterimSpeaker] = useState(meeting.participants?.[0]?.name || "Speaker (You)");
  const [autoScroll, setAutoScroll] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [copied, setCopied] = useState(false);
  
  // Live Detection Toasts
  const [actionAlert, setActionAlert] = useState(null);
  const [decisionAlert, setDecisionAlert] = useState(null);

  const transcriptBottomRef = useRef(null);
  const wsRef = useRef(null);
  const recognitionRef = useRef(null);
  const videoRef = useRef(null);

  // Roster of participants
  const participants = meeting.participants?.length > 0
    ? meeting.participants
    : [
        { id: 1, name: "Speaker 00 (You)", speaker_label: "SPEAKER_00", role: "Host" },
      ];

  const [activeSpeaker, setActiveSpeaker] = useState(participants[0].name);

  // Meeting timer
  useEffect(() => {
    const interval = setInterval(() => {
      setMeetingTimer((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Web camera feed setup
  useEffect(() => {
    let stream = null;
    if (cameraEnabled && navigator.mediaDevices?.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ video: true, audio: false })
        .then((s) => {
          stream = s;
          if (videoRef.current) videoRef.current.srcObject = s;
        })
        .catch((err) => console.log("Camera not accessible or permission denied:", err));
    }
    return () => {
      if (stream) stream.getTracks().forEach((track) => track.stop());
    };
  }, [cameraEnabled]);

  // WebSocket connection & Web Speech / Microphone ASR Streaming
  useEffect(() => {
    let wsUrl;
    if (import.meta.env.VITE_API_URL) {
      const cleanUrl = import.meta.env.VITE_API_URL.replace(/\/+$/, "");
      const wsProtocol = cleanUrl.startsWith("https") ? "wss:" : "ws:";
      const wsHost = cleanUrl.replace(/^https?:\/\//, "");
      wsUrl = `${wsProtocol}//${wsHost}/ws/meetings/${meeting.id}`;
    } else {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const host = window.location.host;
      wsUrl = `${protocol}//${host}/ws/meetings/${meeting.id}`;
    }

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected to meeting room:", meeting.id);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "transcript_partial") {
          setInterimText(msg.text);
          if (msg.speaker) setInterimSpeaker(msg.speaker);
        } else if (msg.type === "transcript_final") {
          setInterimText("");
          setActiveSpeaker(msg.speaker);
          setTranscriptSegments((prev) => [...prev, {
            id: msg.id || Date.now(),
            speaker_name: msg.speaker,
            speaker_label: msg.speaker_label,
            start_time: msg.start,
            end_time: msg.end,
            text: msg.text
          }]);
        } else if (msg.type === "action_detected") {
          setActionAlert(msg);
          setTimeout(() => setActionAlert(null), 7000);
        } else if (msg.type === "decision_detected") {
          setDecisionAlert(msg);
          setTimeout(() => setDecisionAlert(null), 7000);
        }
      } catch (err) {
        console.error("WS message parse error:", err);
      }
    };

    ws.onerror = (e) => console.log("WebSocket error:", e);
    ws.onclose = () => console.log("WebSocket closed");

    // Live Web Speech Recognition if available in browser
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition && micEnabled) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "en-US";

      recognition.onresult = (event) => {
        let interim = "";
        let final = "";

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            final += event.results[i][0].transcript;
          } else {
            interim += event.results[i][0].transcript;
          }
        }

        if (interim) {
          setInterimText(interim);
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
              type: "client_speech",
              speaker: "Rohith",
              speaker_label: "SPEAKER_00",
              text: interim,
              is_final: false,
              start_time: meetingTimer
            }));
          }
        }

        if (final) {
          setInterimText("");
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
              type: "client_speech",
              speaker: "Rohith",
              speaker_label: "SPEAKER_00",
              text: final,
              is_final: true,
              start_time: meetingTimer,
              end_time: meetingTimer + 3
            }));
          }
        }
      };

      recognition.onerror = (e) => console.log("Speech recognition error:", e);
      try {
        recognition.start();
        recognitionRef.current = recognition;
      } catch (e) {
        console.log("Recognition start error:", e);
      }
    }

    return () => {
      if (recognitionRef.current) recognitionRef.current.stop();
      if (ws.readyState === WebSocket.OPEN) ws.close();
    };
  }, [meeting.id, micEnabled]);

  // Auto-scroll transcript when new items arrive
  useEffect(() => {
    if (autoScroll && transcriptBottomRef.current) {
      transcriptBottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [transcriptSegments, interimText, autoScroll]);

  // Format seconds into HH:MM:SS
  const formatTime = (secs) => {
    const hrs = Math.floor(secs / 3600);
    const mins = Math.floor((secs % 3600) / 60);
    const s = secs % 60;
    return `${hrs.toString().padStart(2, "0")}:${mins.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const copyFullTranscript = () => {
    const text = transcriptSegments.map((s) => `[${s.speaker_name || s.speaker_label}]: ${s.text}`).join("\n");
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Filtered transcript for in-panel search
  const filteredTranscript = transcriptSegments.filter((s) =>
    s.text.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (s.speaker_name && s.speaker_name.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-950 text-slate-100 overflow-hidden">
      {/* Top Bar */}
      <header className="h-14 border-b border-slate-800/80 bg-slate-900/80 px-6 flex items-center justify-between backdrop-blur-md z-10">
        <div className="flex items-center space-x-3">
          <span className="flex h-2.5 w-2.5 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>
          </span>
          <h2 className="font-semibold text-sm text-white">{meeting.title}</h2>
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/20 uppercase tracking-wider">
            Live Stream
          </span>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-800/70 border border-slate-700/60 text-xs text-slate-300 font-mono">
            <Clock className="w-3.5 h-3.5 text-indigo-400" />
            <span>{formatTime(meetingTimer)}</span>
          </div>

          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-800/70 border border-slate-700/60 text-xs text-slate-300">
            <Users className="w-3.5 h-3.5 text-cyan-400" />
            <span>{participants.length} Active</span>
          </div>
        </div>
      </header>

      {/* Main Grid: Video Feeds (Left 60%) + Live Transcript (Right 40%) */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: Video & Participant Workspace */}
        <div className="flex-1 p-4 flex flex-col gap-3 overflow-hidden relative">
          {/* Live Action/Decision Notification Toasts */}
          <div className="absolute top-6 left-6 right-6 z-30 pointer-events-none flex flex-col gap-2">
            {actionAlert && (
              <div className="pointer-events-auto max-w-md mx-auto p-3.5 rounded-xl bg-slate-900/95 border border-indigo-500/40 shadow-xl shadow-indigo-950/80 backdrop-blur-xl flex items-start gap-3 animate-in fade-in slide-in-from-top duration-300">
                <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 shrink-0">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold text-indigo-300">Action Item Detected</p>
                    <span className="text-[10px] text-slate-400">Live AI</span>
                  </div>
                  <p className="text-xs font-medium text-white mt-0.5">{actionAlert.task}</p>
                  <div className="flex items-center gap-3 mt-1.5 text-[11px] text-slate-300">
                    <span>Owner: <strong className="text-indigo-200">{actionAlert.owner}</strong></span>
                    <span>Deadline: <strong className="text-indigo-200">{actionAlert.deadline}</strong></span>
                  </div>
                </div>
              </div>
            )}

            {decisionAlert && (
              <div className="pointer-events-auto max-w-md mx-auto p-3.5 rounded-xl bg-slate-900/95 border border-emerald-500/40 shadow-xl shadow-emerald-950/80 backdrop-blur-xl flex items-start gap-3 animate-in fade-in slide-in-from-top duration-300">
                <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shrink-0">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold text-emerald-300">Decision Detected</p>
                    <span className="text-[10px] text-slate-400">Live AI</span>
                  </div>
                  <p className="text-xs font-medium text-white mt-0.5">{decisionAlert.decision}</p>
                </div>
              </div>
            )}
          </div>

          {/* Participant Video Grid */}
          <div className="flex-1 grid grid-cols-2 gap-3 min-h-0">
          <div className="grid grid-cols-2 gap-4 h-full">
            {participants.map((p, idx) => {
              const isLocalUser = idx === 0;
              const isSpeaking = activeSpeaker === p.name || activeSpeaker === p.speaker_label;
              const initials = p.name ? p.name.charAt(0).toUpperCase() : `S${idx}`;
              const colors = [
                "from-indigo-600 to-cyan-500",
                "from-emerald-600 to-teal-400",
                "from-pink-600 to-purple-400",
                "from-amber-600 to-orange-400"
              ];
              const colorClass = colors[idx % colors.length];

              return (
                <div
                  key={p.id || idx}
                  className={`relative rounded-2xl bg-slate-900/80 border overflow-hidden flex items-center justify-center transition-all ${
                    isSpeaking ? "border-indigo-500 shadow-lg shadow-indigo-500/20" : "border-slate-800/80"
                  }`}
                >
                  {isLocalUser && cameraEnabled ? (
                    <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
                  ) : (
                    <div className="flex flex-col items-center">
                      <div className={`w-16 h-16 rounded-full bg-gradient-to-tr ${colorClass} flex items-center justify-center text-xl font-bold text-white shadow-lg`}>
                        {initials}
                      </div>
                      <p className="text-xs text-slate-300 mt-2 font-medium">{p.name || `Speaker ${idx}`}</p>
                      {p.role && <p className="text-[10px] text-slate-400">{p.role}</p>}
                    </div>
                  )}
                  <div className="absolute bottom-3 left-3 px-2.5 py-1 rounded-md bg-slate-950/70 backdrop-blur-sm text-xs font-medium text-white flex items-center gap-1.5 border border-slate-700/50">
                    <span className={`w-2 h-2 rounded-full ${isLocalUser ? (micEnabled ? "bg-emerald-400" : "bg-red-400") : "bg-emerald-400"}`} />
                    <span>{p.name || `Speaker ${idx}`}</span>
                  </div>
                </div>
              );
            })}
          </div>
          </div>
        </div>

        {/* Right Side: LIVE TRANSCRIPT Panel (Requirement 18, 20, 22) */}
        <div className="w-96 border-l border-slate-800 bg-slate-900/90 flex flex-col backdrop-blur-md">
          {/* Transcript Header */}
          <div className="p-3.5 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">Live Transcript</h3>
            </div>
            <div className="flex items-center space-x-1.5">
              <button
                onClick={copyFullTranscript}
                title="Copy Transcript"
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
              <button
                onClick={() => setAutoScroll(!autoScroll)}
                title={autoScroll ? "Pause auto-scroll" : "Resume auto-scroll"}
                className={`px-2 py-1 rounded text-[11px] font-medium transition-colors ${autoScroll ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30" : "bg-slate-800 text-slate-400"}`}
              >
                {autoScroll ? "Auto-scroll On" : "Paused"}
              </button>
            </div>
          </div>

          {/* Transcript Search Bar */}
          <div className="px-3 py-2 border-b border-slate-800/60 bg-slate-900/50">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search transcript..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1 rounded bg-slate-800/70 border border-slate-700/60 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          {/* Transcript Scroll Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3.5 text-xs">
            {filteredTranscript.map((seg, idx) => (
              <div key={seg.id || idx} className="space-y-1 group">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-semibold text-indigo-400">
                    {seg.speaker_name || seg.speaker_label}
                  </span>
                  <span className="text-slate-400 font-mono text-[10px]">
                    {formatTime(Math.floor(seg.start_time || 0))}
                  </span>
                </div>
                <div className="p-2 rounded-lg bg-slate-800/50 border border-slate-800 text-slate-200 leading-relaxed group-hover:border-slate-700 transition-colors">
                  {seg.text}
                </div>
              </div>
            ))}

            {/* Interim Transcript (Currently Recognized Speech) */}
            {interimText && (
              <div className="space-y-1 animate-pulse">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-semibold text-amber-400 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
                    {interimSpeaker} (Speaking...)
                  </span>
                  <span className="text-slate-400 font-mono text-[10px]">Interim</span>
                </div>
                <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-200 italic leading-relaxed">
                  {interimText}
                </div>
              </div>
            )}

            {filteredTranscript.length === 0 && !interimText && (
              <div className="text-center py-12 text-slate-400 text-xs">
                <p>Live audio streaming active.</p>
                <p className="text-[11px] text-slate-400 mt-1">Speak into microphone to view transcription.</p>
              </div>
            )}
            <div ref={transcriptBottomRef} />
          </div>
        </div>
      </div>

      {/* Bottom Meeting Controls Bar */}
      <footer className="h-16 border-t border-slate-800 bg-slate-900/90 px-6 flex items-center justify-between backdrop-blur-md">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setMicEnabled(!micEnabled)}
            className={`p-3 rounded-full transition-all ${micEnabled ? "bg-slate-800 hover:bg-slate-700 text-white" : "bg-red-500/20 text-red-400 border border-red-500/30"}`}
            title={micEnabled ? "Mute Microphone" : "Unmute Microphone"}
          >
            {micEnabled ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
          </button>

          <button
            onClick={() => setCameraEnabled(!cameraEnabled)}
            className={`p-3 rounded-full transition-all ${cameraEnabled ? "bg-slate-800 hover:bg-slate-700 text-white" : "bg-red-500/20 text-red-400 border border-red-500/30"}`}
            title={cameraEnabled ? "Turn Off Camera" : "Turn On Camera"}
          >
            {cameraEnabled ? <Video className="w-4 h-4" /> : <VideoOff className="w-4 h-4" />}
          </button>

          <button
            onClick={() => setScreenSharing(!screenSharing)}
            className={`p-3 rounded-full transition-all ${screenSharing ? "bg-indigo-600 text-white" : "bg-slate-800 hover:bg-slate-700 text-slate-300"}`}
            title="Share Screen"
          >
            <Monitor className="w-4 h-4" />
          </button>
        </div>

        {/* End Meeting Button (Triggers Post-Meeting Processing) */}
        <div>
          <button
            onClick={onEndMeeting}
            className="flex items-center space-x-2 px-5 py-2.5 rounded-full bg-red-600 hover:bg-red-500 text-white text-xs font-semibold tracking-wide transition-all shadow-lg shadow-red-950/60 active:scale-95"
          >
            <PhoneOff className="w-4 h-4" />
            <span>End Meeting</span>
          </button>
        </div>
      </footer>
    </div>
  );
}
