import { useCallback, useRef } from "react";
import { useChatStore } from "@/stores/chatStore";
import { ws } from "@/services/websocket";
import { Mic, MicOff, Loader2 } from "lucide-react";

export function VoiceButton({ variant = "small" }: { variant?: "small" | "large" }) {
  const { voiceState, setVoiceState, isGenerating, activeConversationId } = useChatStore();
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      });

      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());

        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        const arrayBuffer = await blob.arrayBuffer();

        // Convert to base64 and send
        const base64 = btoa(
          new Uint8Array(arrayBuffer).reduce((data, byte) => data + String.fromCharCode(byte), "")
        );

        ws.send("voice_audio", { audio: base64 });
        ws.send("voice_end", { conversation_id: activeConversationId });

        setVoiceState("transcribing");
      };

      mediaRecorder.start(250); // Collect in 250ms chunks
      mediaRecorderRef.current = mediaRecorder;
      setVoiceState("listening");
    } catch (err) {
      console.error("Failed to start recording:", err);
      setVoiceState("idle");
    }
  }, [activeConversationId, setVoiceState]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }
  }, []);

  const handleClick = () => {
    if (voiceState === "listening") {
      stopRecording();
    } else if (voiceState === "idle" && !isGenerating) {
      startRecording();
    }
  };

  const isActive = voiceState === "listening";
  const isBusy = voiceState === "transcribing" || voiceState === "processing";
  
  const sizeClass = variant === "large" ? "p-5 rounded-full" : "p-3 rounded-xl";
  const iconSize = variant === "large" ? 28 : 18;

  return (
    <div className="relative group">
      {/* Glow Layer */}
      {isActive && (
         <div className={`absolute inset-0 rounded-full bg-sunday-error/30 animate-ping blur-md ${variant === "large" ? 'scale-150' : 'scale-125'}`}></div>
      )}

      <button
        onClick={handleClick}
        disabled={isBusy || isGenerating}
        className={`${sizeClass} transition-all duration-300 flex-shrink-0 flex items-center justify-center relative shadow-xl z-20 ${
          isActive
            ? "bg-sunday-error text-white border border-sunday-error shadow-sunday-error/40 scale-105"
            : isBusy
              ? "bg-sunday-warning/20 text-sunday-warning border border-sunday-warning/40 shadow-none"
              : "bg-sunday-accent border border-transparent text-white hover:bg-sunday-accent-hover hover:scale-110 shadow-sunday-accent/30"
        } disabled:opacity-40 disabled:cursor-not-allowed`}
        title={
          isActive ? "Stop recording" : isBusy ? "Processing..." : "Start voice input"
        }
      >
        {isBusy ? (
          <Loader2 size={iconSize} className="animate-spin" />
        ) : isActive ? (
          <MicOff size={iconSize} />
        ) : (
          <Mic size={iconSize} />
        )}
      </button>
    </div>
  );
}
