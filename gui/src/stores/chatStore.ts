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
  isContinuousVoiceActive: boolean;

  // TTS for text chat
  ttsEnabled: boolean;

  // Error notification
  errorMessage: string | null;

  // Background Jobs
  activeJobs: Record<string, BackgroundJob>;

  // Actions
  connect: () => Promise<void>;
  loadConversations: () => Promise<void>;
  selectConversation: (id: string) => Promise<void>;
  newConversation: () => void;
  deleteConversation: (id: string) => Promise<void>;
  sendMessage: (text: string) => void;
  stopGeneration: () => void;
  setVoiceState: (state: VoiceState) => void;
  setContinuousVoiceActive: (active: boolean) => void;
  stopAudio: () => void;
  toggleTTS: () => void;
  clearError: () => void;

  // Settings
  isSettingsOpen: boolean;
  setSettingsOpen: (open: boolean) => void;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  connectionStatus: "disconnected",
  conversations: [],
  activeConversationId: null,
  messages: [],
  isGenerating: false,
  streamingContent: "",
  voiceState: "idle",
  isContinuousVoiceActive: false,
  ttsEnabled: false,
  errorMessage: null,
  isSettingsOpen: false,
  activeJobs: {},

  setSettingsOpen: (open) => set({ isSettingsOpen: open }),

  toggleTTS: () => {
    const newState = !get().ttsEnabled;
    set({ ttsEnabled: newState });
    // Notify the backend of the toggle
    ws.send("tts_toggle", { enabled: newState });
  },

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
          // Reset voice state if we were in a voice flow
          voiceState: state.voiceState !== "idle" ? "idle" : state.voiceState,
        };
      });

      // Refresh sidebar
      get().loadConversations();
    });

    // TTS done — voice flow complete
    ws.on("tts_end", () => {
      if (!get().isContinuousVoiceActive) {
        set({ voiceState: "idle" });
      }
    });

    // Handle status updates — also drives voiceState transitions
    ws.on("status", (msg) => {
      const convId = msg.data.conversation_id as string;
      const status = msg.data.status as string;
      if (convId && !get().activeConversationId) {
        set({ activeConversationId: convId });
      }
      if (status === "listening") set({ voiceState: "listening" });
      else if (status === "transcribing") set({ voiceState: "transcribing" });
      else if (status === "processing") set({ voiceState: "processing" });
      else if (status === "idle" && !get().isContinuousVoiceActive) set({ voiceState: "idle" });
    });

    // Handle TTS audio
    ws.on("tts_audio", (msg) => {
      const audioB64 = msg.data.audio as string;
      if (audioB64) {
        set({ voiceState: "speaking" });
        playAudioBase64(audioB64);
      }
    });

    // Handle voice barge-in (interrupted by user speaking)
    ws.on("voice_barge_in", () => {
      stopAudioPlayback();
      set({ voiceState: "listening" });
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

    // Handle background jobs
    ws.on("job_status", (msg) => {
      const jobId = msg.data.job_id as string;
      const status = msg.data.status as string;
      const message = msg.data.message as string;
      
      set((state) => {
        if (status === "cancelled") {
          const newJobs = { ...state.activeJobs };
          delete newJobs[jobId];
          return { activeJobs: newJobs };
        }
        
        return {
          activeJobs: {
            ...state.activeJobs,
            [jobId]: { id: jobId, status, message }
          }
        };
      });
    });

    ws.on("job_result", (msg) => {
      const jobId = msg.data.job_id as string;
      const result = msg.data.result as string;
      
      set((state) => {
        const newJobs = { ...state.activeJobs };
        delete newJobs[jobId];
        
        // When a job finishes, we inject its result directly into the chat
        const assistantMsg: Message = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `**Research Job Completed**\n\n${result}`,
          source: "text",
          timestamp: new Date().toISOString(),
          isStreaming: false,
        };
        
        return { 
          activeJobs: newJobs,
          messages: [...state.messages, assistantMsg] 
        };
      });
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

    // Send via WebSocket — include TTS preference
    ws.send("chat", {
      message: text.trim(),
      conversation_id: state.activeConversationId,
      tts_enabled: state.ttsEnabled,
    });
  },

  stopGeneration: () => {
    set({ isGenerating: false, streamingContent: "" });
  },

  setVoiceState: (voiceState: VoiceState) => {
    set({ voiceState });
  },

  setContinuousVoiceActive: (active: boolean) => {
    set({ isContinuousVoiceActive: active });
  },

  stopAudio: () => {
    stopAudioPlayback();
  },

  clearError: () => {
    set({ errorMessage: null });
  },
}));

// ---- Audio playback helper ----

const audioQueue: string[] = [];
let isPlaying = false;
let currentAudio: HTMLAudioElement | null = null;

export function stopAudioPlayback() {
  audioQueue.length = 0; // Clear the queue
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }
  isPlaying = false;
}

function playAudioBase64(base64: string) {
  audioQueue.push(base64);
  if (!isPlaying) {
    playNext();
  }
}

function playNext() {
  if (audioQueue.length === 0) {
    isPlaying = false;
    const state = useChatStore.getState();
    if (state.isContinuousVoiceActive) {
      ws.send("continuous_voice_resume_listening", {});
      state.setVoiceState("listening");
    } else {
      state.setVoiceState("idle");
    }
    return;
  }

  isPlaying = true;
  useChatStore.getState().setVoiceState("speaking");
  
  const base64 = audioQueue.shift()!;
  const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0));
  const blob = new Blob([bytes], { type: "audio/wav" });
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  currentAudio = audio;

  audio.onended = () => {
    URL.revokeObjectURL(url);
    if (currentAudio === audio) currentAudio = null;
    playNext();
  };

  audio.onerror = () => {
    URL.revokeObjectURL(url);
    if (currentAudio === audio) currentAudio = null;
    playNext();
  };

  audio.play().catch(() => {
    if (currentAudio === audio) currentAudio = null;
    playNext();
  });
}
