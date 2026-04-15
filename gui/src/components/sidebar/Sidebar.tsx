import { useChatStore } from "@/stores/chatStore";
import { ConversationList } from "./ConversationList";
import { MessageSquarePlus, Wifi, WifiOff, Loader2 } from "lucide-react";

export function Sidebar() {
  const { connectionStatus, newConversation } = useChatStore();

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-sunday-border">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-sunday-accent flex items-center justify-center">
              <span className="text-white font-bold text-sm">S</span>
            </div>
            <span className="font-semibold text-sunday-text">SUNDAY</span>
          </div>
          <ConnectionIndicator status={connectionStatus} />
        </div>

        <button
          onClick={newConversation}
          className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg
                     bg-sunday-accent hover:bg-sunday-accent-hover text-white text-sm font-medium
                     transition-colors duration-150"
        >
          <MessageSquarePlus size={16} />
          New Chat
        </button>
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto">
        <ConversationList />
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-sunday-border">
        <p className="text-xs text-sunday-text-muted text-center">SUNDAY v0.1.0</p>
      </div>
    </div>
  );
}

function ConnectionIndicator({ status }: { status: string }) {
  if (status === "connected") {
    return <Wifi size={14} className="text-sunday-success" />;
  }
  if (status === "connecting") {
    return <Loader2 size={14} className="text-sunday-warning animate-spin" />;
  }
  return <WifiOff size={14} className="text-sunday-error" />;
}
