import React, { useState } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { MeetingProvider, useMeetings } from "./context/MeetingContext";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import Dashboard from "./pages/Dashboard";
import NewMeetingPage from "./pages/NewMeetingPage";
import UploadMeetingPage from "./pages/UploadMeetingPage";
import SearchPage from "./pages/SearchPage";
import HistorySidebar from "./components/layout/HistorySidebar";
import LiveMeetingRoom from "./components/live/LiveMeetingRoom";
import ProcessingTracker from "./components/processing/ProcessingTracker";
import MeetingWorkspace from "./components/workspace/MeetingWorkspace";
import { meetingAPI } from "./services/api";

function MainApp() {
  const { isAuthenticated, loading } = useAuth();
  const { loadMeetingDetails, fetchMeetings } = useMeetings();

  // Navigation state: "landing" | "login" | "register" | "dashboard" | "new_meeting" | "upload" | "live" | "processing" | "workspace" | "search"
  const [currentView, setCurrentView] = useState("dashboard");
  const [activeMeeting, setActiveMeeting] = useState(null);

  if (loading) {
    return (
      <div className="h-screen w-screen bg-slate-950 flex items-center justify-center text-slate-400 text-sm">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
          <span>Initializing MoM Studio...</span>
        </div>
      </div>
    );
  }

  // Unauthenticated Views
  if (!isAuthenticated) {
    if (currentView === "login") {
      return (
        <LoginPage
          onSwitchToRegister={() => setCurrentView("register")}
          onSuccess={() => setCurrentView("dashboard")}
        />
      );
    }
    if (currentView === "register") {
      return (
        <RegisterPage
          onSwitchToLogin={() => setCurrentView("login")}
          onSuccess={() => setCurrentView("dashboard")}
        />
      );
    }
    return (
      <LandingPage
        onGetStarted={() => setCurrentView("login")}
        onStartLive={() => setCurrentView("login")}
        onUpload={() => setCurrentView("login")}
      />
    );
  }

  // Authenticated Handlers
  const handleSelectMeeting = async (meetingId) => {
    try {
      const details = await loadMeetingDetails(meetingId);
      setActiveMeeting(details);
      setCurrentView("workspace");
    } catch (err) {
      alert("Failed to load meeting details.");
    }
  };

  const handleStartLive = (meetingData) => {
    setActiveMeeting(meetingData);
    setCurrentView("live");
  };

  const handleEndLiveMeeting = async () => {
    if (!activeMeeting) return;
    setCurrentView("processing");
    try {
      const res = await meetingAPI.end(activeMeeting.id);
      setActiveMeeting(res.data);
      await fetchMeetings();
    } catch (err) {
      console.error("Error ending meeting:", err);
      setCurrentView("workspace");
    }
  };

  const handleUploadSuccess = (processedMeeting) => {
    setActiveMeeting(processedMeeting);
    setCurrentView("processing");
    fetchMeetings();
  };

  const handleProcessingComplete = () => {
    setCurrentView("workspace");
  };

  return (
    <div className="flex h-screen w-screen bg-slate-950 overflow-hidden font-sans text-slate-100">
      {/* ChatGPT-like Persistent History Sidebar */}
      {currentView !== "live" && (
        <HistorySidebar
          activeId={activeMeeting?.id}
          onSelectMeeting={handleSelectMeeting}
          onNewMeeting={() => setCurrentView("new_meeting")}
          onOpenSearch={() => setCurrentView("search")}
        />
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {currentView === "dashboard" && (
          <Dashboard
            onStartLive={() => setCurrentView("new_meeting")}
            onUpload={() => setCurrentView("upload")}
            onSelectMeeting={handleSelectMeeting}
            onViewHistory={() => setCurrentView("search")}
          />
        )}

        {currentView === "new_meeting" && (
          <NewMeetingPage
            onStartLive={handleStartLive}
            onUploadRecording={(data) => {
              setActiveMeeting(data);
              setCurrentView("upload");
            }}
          />
        )}

        {currentView === "upload" && (
          <UploadMeetingPage onUploadSuccess={handleUploadSuccess} />
        )}

        {currentView === "live" && activeMeeting && (
          <LiveMeetingRoom
            meeting={activeMeeting}
            onEndMeeting={handleEndLiveMeeting}
          />
        )}

        {currentView === "processing" && (
          <div className="flex-1 flex items-center justify-center p-8 overflow-y-auto">
            <ProcessingTracker onComplete={handleProcessingComplete} />
          </div>
        )}

        {currentView === "workspace" && activeMeeting && (
          <MeetingWorkspace
            meeting={activeMeeting}
            onUpdateMeeting={() => handleSelectMeeting(activeMeeting.id)}
          />
        )}

        {currentView === "search" && (
          <SearchPage onSelectMeeting={handleSelectMeeting} />
        )}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <MeetingProvider>
        <MainApp />
      </MeetingProvider>
    </AuthProvider>
  );
}
