export interface User {
  id: string;
  tally_response_id: string;
  created_at: string;
  is_blocked: boolean;
  last_active: string;
  email?: string;
}

export interface ChatMessage {
  id: string;
  content: string;
  is_from_user: boolean;
  created_at: string;
  is_admin_intervention: boolean;
}

export interface ChatSession {
  id: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  messages: ChatMessage[];
}

export interface ConversationSummary {
  session_id: string;
  user_id: string;
  user_email?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message?: string;
  is_active: boolean;
  user_blocked: boolean;
}

export interface DashboardStats {
  total_users: number;
  active_sessions: number;
  total_messages: number;
  blocked_users: number;
  messages_today: number;
  new_users_today: number;
}

export interface AdminUser {
  id: string;
  username: string;
  email: string;
  created_at: string;
  is_active: boolean;
}

export interface MessageHistory {
  messages: ChatMessage[];
  session_info: ChatSession;
  user_info: User;
}
