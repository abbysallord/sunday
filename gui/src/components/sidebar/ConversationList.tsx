import { useEffect } from "react";
import { useChatStore } from "@/stores/chatStore";
import { Trash2, MessageSquare } from "lucide-react";

export function ConversationList() {
  const {
    conversations,
    activeConversationId,
    loadConversations,
    selectConversation,
    deleteConversation,
    connectionStatus,
  } = useChatStore();

  useEffect(() => {
    if (connectionStatus === "connected") {
      loadConversations();
    }
  }, [connectionStatus, loadConversations]);

  if (conversations.length === 0) {
    return (
      <div className="p-4 text-center text-sunday-text-muted text-sm">
        <MessageSquare size={24} className="mx-auto mb-2 opacity-40" />
        <p>No conversations yet</p>
        <p className="text-xs mt-1">Start a new chat above</p>
      </div>
    );
  }

  return (
    <div className="p-2 space-y-0.5">
      {conversations.map((conv) => (
        <div
          key={conv.id}
          onClick={() => selectConversation(conv.id)}
          className={`group flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer
                      transition-colors duration-100 ${
                        activeConversationId === conv.id
                          ? "bg-sunday-accent-glow border border-sunday-accent/30"
                          : "hover:bg-sunday-surface-hover"
                      }`}
        >
          <div className="flex-1 min-w-0">
            <p className="text-sm truncate text-sunday-text">{conv.title}</p>
            <p className="text-xs text-sunday-text-muted truncate mt-0.5">
              {conv.preview || `${conv.message_count} messages`}
            </p>
          </div>

          <button
            onClick={(e) => {
              e.stopPropagation();
              deleteConversation(conv.id);
            }}
            className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-sunday-error/20
                       text-sunday-text-muted hover:text-sunday-error transition-all duration-150"
          >
            <Trash2 size={13} />
          </button>
        </div>
      ))}
    </div>
  );
}
