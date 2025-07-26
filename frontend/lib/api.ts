import axios from "axios";
import {
  ChatSession,
  ConversationSummary,
  DashboardStats,
  MessageHistory,
} from "../types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("admin_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Chat API
export const chatApi = {
  getSession: async (userId: string): Promise<ChatSession> => {
    const response = await api.get(`/chat/session/${userId}`);
    return response.data;
  },

  sendMessage: async (
    sessionId: string,
    message: string,
    maxTokens: number = 150
  ) => {
    const response = await api.post(`/chat/message/${sessionId}`, {
      message,
      max_tokens: maxTokens,
    });
    return response.data;
  },

  getResponseStatus: async (taskId: string) => {
    const response = await api.get(`/chat/response/${taskId}`);
    return response.data;
  },

  createDeviceSession: async (deviceId: string, customPrompt: string) => {
    const response = await api.post("/user/device-session", {
      device_id: deviceId,
      custom_prompt: customPrompt,
    });
    return response.data;
  },
};

// Admin API
export const adminApi = {
  login: async (username: string, password: string) => {
    const response = await api.post("/admin/login", { username, password });
    return response.data;
  },

  getConversations: async (
    skip: number = 0,
    limit: number = 50
  ): Promise<ConversationSummary[]> => {
    const response = await api.get(
      `/admin/conversations?skip=${skip}&limit=${limit}`
    );
    return response.data;
  },

  getConversationDetails: async (
    sessionId: string
  ): Promise<MessageHistory> => {
    const response = await api.get(`/admin/conversation/${sessionId}`);
    return response.data;
  },

  intervene: async (sessionId: string, message: string) => {
    const response = await api.post("/admin/intervene", {
      session_id: sessionId,
      message,
    });
    return response.data;
  },

  blockUser: async (userId: string, block: boolean = true) => {
    const response = await api.post("/admin/block-user", {
      user_id: userId,
      block,
    });
    return response.data;
  },

  getStats: async (): Promise<DashboardStats> => {
    const response = await api.get("/admin/stats");
    return response.data;
  },
};

export default api;
