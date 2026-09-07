import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { meetingAPI } from "../services/api";
import { useAuth } from "./AuthContext";

const MeetingContext = createContext(null);

export const MeetingProvider = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [meetings, setMeetings] = useState([]);
  const [activeMeeting, setActiveMeeting] = useState(null);
  const [loadingMeetings, setLoadingMeetings] = useState(false);

  const fetchMeetings = useCallback(async () => {
    if (!isAuthenticated) {
      setMeetings([]);
      return;
    }
    setLoadingMeetings(true);
    try {
      const res = await meetingAPI.list();
      setMeetings(res.data);
    } catch (err) {
      console.error("Failed to load meeting history:", err);
    } finally {
      setLoadingMeetings(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    fetchMeetings();
  }, [fetchMeetings]);

  const loadMeetingDetails = async (id) => {
    try {
      const res = await meetingAPI.get(id);
      setActiveMeeting(res.data);
      return res.data;
    } catch (err) {
      console.error("Failed to fetch meeting details:", err);
      throw err;
    }
  };

  return (
    <MeetingContext.Provider
      value={{
        meetings,
        activeMeeting,
        loadingMeetings,
        fetchMeetings,
        loadMeetingDetails,
        setActiveMeeting,
      }}
    >
      {children}
    </MeetingContext.Provider>
  );
};

export const useMeetings = () => useContext(MeetingContext);
