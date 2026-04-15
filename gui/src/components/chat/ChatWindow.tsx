import { useEffect, useRef } from "react";
import { useChatStore } from "@/stores/chatStore";
import { MessageBubble } from "./MessageBubble";
import { StreamingBubble } from "./StreamingBubble";
import { InputBar } from "./InputBar";
import { VoiceButton } from "@/components/voice/VoiceButton";
import { Sun, X, AlertTriangle } from "lucide-react";

export function ChatWindow() {
  const { messages, isGenerating, streamingContent, errorMessage, clearError } =
    useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 && !isGenerating ? (
          <WelcomeScreen />
        ) : (
          <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {isGenerating && streamingContent && (
              <StreamingBubble content={streamingContent} />
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Error toast */}
      {errorMessage && (
        <div className="max-w-3xl mx-auto px-4 w-full animate-slide-up">
          <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-sunday-error/10 border border-sunday-error/30 text-sm text-sunday-error">
            <AlertTriangle size={16} className="flex-shrink-0" />
            <p className="flex-1">{errorMessage}</p>
            <button
              onClick={clearError}
              className="p-1 rounded-lg hover:bg-sunday-error/20 transition-colors flex-shrink-0"
            >
              <X size={14} />
            </button>
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="border-t border-sunday-border bg-sunday-surface/50 backdrop-blur-sm">
        <div className="max-w-3xl mx-auto px-4 py-3">
          <div className="flex items-end gap-2">
            <VoiceButton />
            <InputBar />
          </div>
          <p className="text-[10px] text-sunday-text-muted text-center mt-2 select-none opacity-60">
            Press <kbd className="px-1 py-0.5 rounded bg-sunday-surface-hover text-sunday-text-muted">/</kbd> to focus
            {" · "}
            <kbd className="px-1 py-0.5 rounded bg-sunday-surface-hover text-sunday-text-muted">Ctrl+Shift+N</kbd> new chat
            {" · "}
            <kbd className="px-1 py-0.5 rounded bg-sunday-surface-hover text-sunday-text-muted">Esc</kbd> stop
          </p>
        </div>
      </div>
    </div>
  );
}

function WelcomeScreen() {
  return (
    <div className="flex flex-col items-center justify-center h-full animate-fade-in">
      <div className="w-16 h-16 rounded-2xl bg-sunday-accent/20 flex items-center justify-center mb-6">
        <Sun size={32} className="text-sunday-accent" />
      </div>
      <h1 className="text-2xl font-semibold text-sunday-text mb-2">Good day!</h1>
      <p className="text-sunday-text-muted text-center max-w-md">
        I'm <span className="text-sunday-accent font-medium">SUNDAY</span>, your personal AI
        assistant. Type a message or press the mic button to start talking.
      </p>
      <div className="mt-6 flex flex-wrap gap-2 justify-center max-w-md">
        <SuggestionChip text="What can you help me with?" />
        <SuggestionChip text="Explain quantum computing simply" />
        <SuggestionChip text="Write a haiku about coding" />
      </div>
    </div>
  );
}

function SuggestionChip({ text }: { text: string }) {
  const sendMessage = useChatStore((s) => s.sendMessage);

  return (
    <button
      onClick={() => sendMessage(text)}
      className="px-4 py-2 rounded-xl border border-sunday-border bg-sunday-surface
                 hover:border-sunday-accent/40 hover:bg-sunday-surface-hover
                 text-sm text-sunday-text-muted hover:text-sunday-text
                 transition-all duration-200"
    >
      {text}
    </button>
  );
}

