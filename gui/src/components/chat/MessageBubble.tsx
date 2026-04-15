import { Message } from "@/types";
import { User, Bot } from "lucide-react";
import ReactMarkdown from "react-markdown";

interface Props {
  message: Message;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 animate-slide-up ${isUser ? "justify-end" : "justify-start"}`}>
      {/* Avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-lg bg-sunday-accent/20 flex items-center justify-center flex-shrink-0 mt-1">
          <Bot size={16} className="text-sunday-accent" />
        </div>
      )}

      {/* Bubble */}
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 message-content ${
          isUser
            ? "bg-sunday-user text-sunday-text rounded-br-md"
            : "bg-sunday-assistant text-sunday-text rounded-bl-md border border-sunday-border"
        }`}
      >
        {isUser ? (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="text-sm leading-relaxed prose-invert">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}

        {/* Timestamp */}
        <p className="text-[10px] text-sunday-text-muted mt-1.5 select-none">
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
          {message.source === "voice" && " 🎤"}
        </p>
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="w-8 h-8 rounded-lg bg-sunday-user flex items-center justify-center flex-shrink-0 mt-1">
          <User size={16} className="text-sunday-text" />
        </div>
      )}
    </div>
  );
}
