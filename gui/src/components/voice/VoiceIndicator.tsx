import { useChatStore } from "@/stores/chatStore";
import { Loader2 } from "lucide-react";

const STATE_LABELS: Record<string, string> = {
  listening: "Listening...",
  transcribing: "Transcribing...",
  processing: "Thinking...",
  speaking: "Speaking...",
};

export function VoiceIndicator() {
  const voiceState = useChatStore((s) => s.voiceState);

  if (voiceState === "idle") return null;

  const label = STATE_LABELS[voiceState] ?? voiceState;
  const isSpinner = voiceState === "transcribing" || voiceState === "processing";
  const isPulse = voiceState === "listening";

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-sunday-surface border border-sunday-border text-xs text-sunday-text-muted animate-fade-in">
      {isSpinner && <Loader2 size={12} className="animate-spin text-sunday-accent" />}
      {isPulse && (
        <span className="w-2 h-2 rounded-full bg-sunday-error animate-pulse" />
      )}
      {voiceState === "speaking" && (
        <span className="flex gap-0.5 items-end h-3">
          {[1, 2, 3].map((i) => (
            <span
              key={i}
              className="w-0.5 bg-sunday-accent rounded-full animate-bounce"
              style={{ height: `${4 + i * 3}px`, animationDelay: `${i * 0.1}s` }}
            />
          ))}
        </span>
      )}
      <span>{label}</span>
    </div>
  );
}
