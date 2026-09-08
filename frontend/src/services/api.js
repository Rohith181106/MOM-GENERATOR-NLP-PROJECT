import axios from "axios";

const rawApiUrl = import.meta.env.VITE_API_URL ? import.meta.env.VITE_API_URL.replace(/\/+$/, "") : "";
export const BASE_API_URL = rawApiUrl ? `${rawApiUrl}/api` : "/api";

const API = axios.create({
  baseURL: BASE_API_URL,
});

API.interceptors.request.use((config) => {
  const token = localStorage.getItem("mom_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  login: (email, password) => API.post("/auth/login", { email, password }),
  register: (name, email, password) => API.post("/auth/register", { name, email, password }),
  getMe: () => API.get("/auth/me"),
};

export const meetingAPI = {
  list: () => API.get("/meetings"),
  create: (data) => API.post("/meetings", data),
  get: (id) => API.get(`/meetings/${id}`),
  delete: (id) => API.delete(`/meetings/${id}`),
  start: (id) => API.post(`/meetings/${id}/start`),
  end: (id) => API.post(`/meetings/${id}/end`),
  process: (id) => API.post(`/meetings/${id}/process`),
  upload: (formData) => API.post("/meetings/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  }),
  getMoM: (id) => API.get(`/meetings/${id}/mom`),
  updateMoM: (id, data) => API.put(`/meetings/${id}/mom`, data),
  search: (query) => API.get(`/meetings/search?q=${encodeURIComponent(query)}`),
  exportDocx: async (id, filename = "meeting_mom.docx") => {
    const response = await API.post(`/meetings/${id}/export/docx`, {}, { responseType: "blob" });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },
  exportPdf: async (id, filename = "meeting_mom.pdf") => {
    const response = await API.post(`/meetings/${id}/export/pdf`, {}, { responseType: "blob" });
    const url = window.URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },
  getBenchmark: () => API.get("/benchmark"),
};

export default API;
