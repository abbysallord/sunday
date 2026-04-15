// ---- Message types ----

export type Role = "user" | "assistant" | "system";
export type MessageSource = "text" | "voice";

export interface Message {
  id: string;
  role: Role;
  content: string;
  source: MessageSource;
  timestamp: string;
  isStreaming?: boolean;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export interface ConversationSummary {
  id: string;
  title: string;
  updated_at: string;
  message_count: number;
  preview: string;
}

// ---- WebSocket protocol ----

export type WSMessageType =
  | "chat"
  | "chat_stream"
  | "chat_end"
  | "voice_start"
  | "voice_audio"
  | "voice_end"
  | "tts_audio"
  | "tts_end"
  | "error"
  | "status";

export interface WSMessage {
  type: string;
  data: Record<string, unknown>;
}

// ---- App state ----

export type ConnectionStatus = "connected" | "connecting" | "disconnected";
export type VoiceState = "idle" | "listening" | "transcribing" | "processing" | "speaking";
