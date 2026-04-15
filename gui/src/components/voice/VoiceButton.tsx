import { useCallback, useRef } from "react";
import { useChatStore } from "@/stores/chatStore";
import { ws } from "@/services/websocket";
import { Mic, MicOff, Loader2 } from "lucide-react";

export function VoiceButton() {
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

  return (
    <button
      onClick={handleClick}
      disabled={isBusy || isGenerating}
      className={`p-3 rounded-xl transition-all duration-200 flex-shrink-0 ${
        isActive
          ? "bg-sunday-error/20 text-sunday-error border border-sunday-error/40 animate-pulse-slow"
          : isBusy
            ? "bg-sunday-warning/20 text-sunday-warning border border-sunday-warning/40"
            : "bg-sunday-surface border border-sunday-border text-sunday-text-muted hover:text-sunday-accent hover:border-sunday-accent/50"
      } disabled:opacity-40 disabled:cursor-not-allowed`}
      title={
        isActive ? "Stop recording" : isBusy ? "Processing..." : "Start voice input"
      }
    >
      {isBusy ? (
        <Loader2 size={18} className="animate-spin" />
      ) : isActive ? (
        <MicOff size={18} />
      ) : (
        <Mic size={18} />
      )}
    </button>
  );
}
