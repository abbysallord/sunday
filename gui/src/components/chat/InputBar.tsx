import { useState, useRef, useCallback } from "react";
import { useChatStore } from "@/stores/chatStore";
import { Send } from "lucide-react";

export function InputBar() {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { sendMessage, isGenerating } = useChatStore();

  const handleSend = useCallback(() => {
    if (!text.trim() || isGenerating) return;
    sendMessage(text);
    setText("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [text, isGenerating, sendMessage]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    // Auto-resize
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 150) + "px";
  };

  return (
    <div className="flex-1 flex items-end gap-2 bg-sunday-surface border border-sunday-border rounded-xl px-3 py-2 focus-within:border-sunday-accent/50 transition-colors">
      <textarea
        ref={textareaRef}
        value={text}
        onChange={handleInput}
        onKeyDown={handleKeyDown}
        placeholder="Message SUNDAY..."
        rows={1}
        disabled={isGenerating}
        className="flex-1 bg-transparent text-sm text-sunday-text placeholder-sunday-text-muted
                   resize-none outline-none max-h-[150px] leading-relaxed py-1"
      />

      <button
        onClick={handleSend}
        disabled={!text.trim() || isGenerating}
        className="p-2 rounded-lg bg-sunday-accent hover:bg-sunday-accent-hover
                   disabled:opacity-30 disabled:cursor-not-allowed
                   text-white transition-all duration-150 flex-shrink-0"
      >
        <Send size={16} />
      </button>
    </div>
  );
}
