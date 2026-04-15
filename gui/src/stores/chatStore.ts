import { create } from "zustand";
import { Message, ConversationSummary, ConnectionStatus, VoiceState } from "@/types";
import { ws } from "@/services/websocket";
import { api } from "@/services/api";

interface ChatStore {
  // Connection
  connectionStatus: ConnectionStatus;

  // Conversations
  conversations: ConversationSummary[];
  activeConversationId: string | null;
  messages: Message[];

  // Streaming
  isGenerating: boolean;
  streamingContent: string;

  // Voice
  voiceState: VoiceState;

  // Error notification
  errorMessage: string | null;

  // Actions
  connect: () => Promise<void>;
  loadConversations: () => Promise<void>;
  selectConversation: (id: string) => Promise<void>;
  newConversation: () => void;
  deleteConversation: (id: string) => Promise<void>;
  sendMessage: (text: string) => void;
  stopGeneration: () => void;
  setVoiceState: (state: VoiceState) => void;
  clearError: () => void;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  connectionStatus: "disconnected",
  conversations: [],
  activeConversationId: null,
  messages: [],
  isGenerating: false,
  streamingContent: "",
  voiceState: "idle",
  errorMessage: null,

  connect: async () => {
    // Guard against duplicate handler registration (React StrictMode calls effects twice)
    if (get().connectionStatus === "connecting" || get().connectionStatus === "connected") {
      return;
    }

    set({ connectionStatus: "connecting" });

    ws.on("_connected", () => {
      set({ connectionStatus: "connected" });
    });

    ws.on("_disconnected", () => {
      set({ connectionStatus: "disconnected" });
    });

    // Handle streaming tokens
    ws.on("chat_stream", (msg) => {
      const token = msg.data.token as string;
      const convId = msg.data.conversation_id as string;

      set((state) => {
        // Update active conversation ID if this is a new conversation
        const newState: Partial<ChatStore> = {
          streamingContent: state.streamingContent + token,
          isGenerating: true,
        };

        if (!state.activeConversationId && convId) {
          newState.activeConversationId = convId;
        }

        return newState as ChatStore;
      });
    });

    // Handle stream end
    ws.on("chat_end", (msg) => {
      const fullContent = msg.data.full_content as string;
      const messageId = msg.data.message_id as string;
      const convId = msg.data.conversation_id as string;

      set((state) => {
        const assistantMsg: Message = {
          id: messageId,
          role: "assistant",
          content: fullContent,
          source: "text",
          timestamp: new Date().toISOString(),
          isStreaming: false,
        };

        return {
          messages: [...state.messages, assistantMsg],
          isGenerating: false,
          streamingContent: "",
          activeConversationId: convId,
        };
      });

      // Refresh sidebar
      get().loadConversations();
    });

    // Handle status updates
    ws.on("status", (msg) => {
      const convId = msg.data.conversation_id as string;
      if (convId && !get().activeConversationId) {
        set({ activeConversationId: convId });
      }
    });

    // Handle TTS audio
    ws.on("tts_audio", (msg) => {
      const audioB64 = msg.data.audio as string;
      if (audioB64) {
        playAudioBase64(audioB64);
      }
    });

    // Handle title updates (LLM-generated smart titles)
    ws.on("title_update", (msg) => {
      const convId = msg.data.conversation_id as string;
      const title = msg.data.title as string;
      if (convId && title) {
        // Update the conversation title in the sidebar list
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === convId ? { ...c, title } : c
          ),
        }));
      }
    });

    // Handle errors
    ws.on("error", (msg) => {
      const errorText = msg.data.message as string;
      console.error("Server error:", errorText);
      set({ isGenerating: false, streamingContent: "", errorMessage: errorText });
      // Auto-clear after 8 seconds
      setTimeout(() => {
        set((state) => state.errorMessage === errorText ? { errorMessage: null } : {});
      }, 8000);
    });

    try {
      await ws.connect();
    } catch {
      set({ connectionStatus: "disconnected" });
    }
  },

  loadConversations: async () => {
    try {
      const conversations = await api.listConversations();
      set({ conversations });
    } catch (e) {
      console.error("Failed to load conversations:", e);
    }
  },

  selectConversation: async (id: string) => {
    try {
      const conversation = await api.getConversation(id);
      const messages: Message[] = (conversation.messages as unknown as Array<Record<string, unknown>>).map((m) => ({
        id: m.id as string,
        role: m.role as Message["role"],
        content: m.content as string,
        source: (m.source as Message["source"]) || "text",
        timestamp: m.timestamp as string,
        isStreaming: false,
      }));
      set({ activeConversationId: id, messages });
    } catch (e) {
      console.error("Failed to load conversation:", e);
    }
  },

  newConversation: () => {
    set({ activeConversationId: null, messages: [], streamingContent: "" });
  },

  deleteConversation: async (id: string) => {
    try {
      await api.deleteConversation(id);
      const state = get();
      if (state.activeConversationId === id) {
        set({ activeConversationId: null, messages: [] });
      }
      await state.loadConversations();
    } catch (e) {
      console.error("Failed to delete conversation:", e);
    }
  },

  sendMessage: (text: string) => {
    const state = get();
    if (state.isGenerating || !text.trim()) return;

    // Add user message to local state immediately
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text.trim(),
      source: "text",
      timestamp: new Date().toISOString(),
    };

    set((s) => ({
      messages: [...s.messages, userMsg],
      isGenerating: true,
      streamingContent: "",
    }));

    // Send via WebSocket
    ws.send("chat", {
      message: text.trim(),
      conversation_id: state.activeConversationId,
    });
  },

  stopGeneration: () => {
    set({ isGenerating: false, streamingContent: "" });
  },

  setVoiceState: (voiceState: VoiceState) => {
    set({ voiceState });
  },

  clearError: () => {
    set({ errorMessage: null });
  },
}));

// ---- Audio playback helper ----

const audioQueue: string[] = [];
let isPlaying = false;

function playAudioBase64(base64: string) {
  audioQueue.push(base64);
  if (!isPlaying) {
    playNext();
  }
}

function playNext() {
  if (audioQueue.length === 0) {
    isPlaying = false;
    return;
  }

  isPlaying = true;
  const base64 = audioQueue.shift()!;
  const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0));
  const blob = new Blob([bytes], { type: "audio/wav" });
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);

  audio.onended = () => {
    URL.revokeObjectURL(url);
    playNext();
  };

  audio.onerror = () => {
    URL.revokeObjectURL(url);
    playNext();
  };

  audio.play().catch(() => playNext());
}
