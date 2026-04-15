import { Conversation, ConversationSummary } from "@/types";

const BASE = "";

async function fetchJSON<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API Error ${res.status}: ${text}`);
  }

  return res.json();
}

export const api = {
  health: () => fetchJSON<{ status: string; app: string; version: string }>("/health"),

  listConversations: () =>
    fetchJSON<{ conversations: ConversationSummary[] }>("/api/conversations/").then(
      (r) => r.conversations
    ),

  getConversation: (id: string) => fetchJSON<Conversation>(`/api/conversations/${id}`),

  deleteConversation: (id: string) =>
    fetchJSON<{ status: string }>(`/api/conversations/${id}`, { method: "DELETE" }),

  updateTitle: (id: string, title: string) =>
    fetchJSON<{ status: string }>(`/api/conversations/${id}/title`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    }),
};
