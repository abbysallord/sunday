import { useEffect } from "react";
import { useChatStore } from "@/stores/chatStore";

/**
 * Global keyboard shortcuts for SUNDAY.
 *
 * Ctrl+Shift+N — New conversation
 * Escape       — Stop generation / clear input focus
 * Ctrl+Shift+V — Toggle voice input (future)
 * /            — Focus input bar (when not already focused)
 */
export function useKeyboardShortcuts() {
  const {
    newConversation,
    stopGeneration,
    isGenerating,
  } = useChatStore();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const isTyping =
        target.tagName === "TEXTAREA" ||
        target.tagName === "INPUT" ||
        target.isContentEditable;

      // Ctrl+Shift+N — New conversation (works globally)
      if (e.ctrlKey && e.shiftKey && e.key === "N") {
        e.preventDefault();
        newConversation();
        // Focus the input bar after creating new conversation
        setTimeout(() => {
          const input = document.querySelector<HTMLTextAreaElement>(
            '[placeholder="Message SUNDAY..."]'
          );
          input?.focus();
        }, 50);
        return;
      }

      // Escape — Stop generation or blur input
      if (e.key === "Escape") {
        if (isGenerating) {
          e.preventDefault();
          stopGeneration();
        } else if (isTyping) {
          (target as HTMLElement).blur();
        }
        return;
      }

      // "/" — Focus input bar (only when NOT already typing)
      if (e.key === "/" && !isTyping && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        const input = document.querySelector<HTMLTextAreaElement>(
          '[placeholder="Message SUNDAY..."]'
        );
        input?.focus();
        return;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [newConversation, stopGeneration, isGenerating]);
}
