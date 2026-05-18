import { useCallback, useRef, useEffect } from "react";
import { useChatStore } from "@/stores/chatStore";
import { ws } from "@/services/websocket";
import { Mic, Radio, Loader2 } from "lucide-react";

export function ContinuousVoiceButton() {
  const { 
    voiceState, 
    setVoiceState, 
    isContinuousVoiceActive, 
    setContinuousVoiceActive,
    activeConversationId, 
    stopAudio 
  } = useChatStore();

  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const sourceRef = useRef<MediaAudioSourceNode | null>(null);

  // Stop recording and close AudioContext safely
  const stopContinuousVoice = useCallback(() => {
    logDebug("Stopping continuous voice stream...");
    
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current.onaudioprocess = null;
      processorRef.current = null;
    }
    
    if (sourceRef.current) {
      sourceRef.current.disconnect();
      sourceRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close().catch((err) => 
        console.error("Failed to close AudioContext:", err)
      );
      audioContextRef.current = null;
    }

    if (isContinuousVoiceActive) {
      ws.send("continuous_voice_stop", {});
      setContinuousVoiceActive(false);
    }
    
    setVoiceState("idle");
  }, [isContinuousVoiceActive, setContinuousVoiceActive, setVoiceState]);

  // Clean up recording on unmount
  useEffect(() => {
    return () => {
      stopContinuousVoice();
    };
  }, [stopContinuousVoice]);

  const startContinuousVoice = useCallback(async () => {
    try {
      logDebug("Requesting microphone permissions...");
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      // Browser Web Audio API handles automatic high-quality downsampling to 16kHz!
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: 16000,
        latencyHint: "interactive",
      });

      const source = audioContext.createMediaStreamSource(stream);
      
      // Buffer size of 1024 samples is exactly 64ms at 16kHz
      const processor = audioContext.createScriptProcessor(1024, 1, 1);

      processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0); // raw mono float32 array
        
        // Fast, call-stack safe array buffer binary to base64 conversion
        const uint8 = new Uint8Array(inputData.buffer);
        let binary = "";
        const len = uint8.byteLength;
        for (let i = 0; i < len; i++) {
          binary += String.fromCharCode(uint8[i]);
        }
        const base64 = btoa(binary);

        ws.send("continuous_voice_audio", { 
          audio: base64,
          conversation_id: useChatStore.getState().activeConversationId 
        });
      };

      source.connect(processor);
      processor.connect(audioContext.destination);

      audioContextRef.current = audioContext;
      processorRef.current = processor;
      streamRef.current = stream;
      sourceRef.current = source;

      // Start connection on server
      stopAudio(); // Mute assistant immediately on continuous toggle
      ws.send("continuous_voice_start", { conversation_id: activeConversationId });
      setContinuousVoiceActive(true);
      setVoiceState("listening");
      logDebug("Continuous voice stream started.");

    } catch (err) {
      console.error("Failed to start continuous voice:", err);
      stopContinuousVoice();
    }
  }, [activeConversationId, setContinuousVoiceActive, setVoiceState, stopAudio, stopContinuousVoice]);

  const handleToggle = () => {
    if (isContinuousVoiceActive) {
      stopContinuousVoice();
    } else {
      startContinuousVoice();
    }
  };

  const isActive = isContinuousVoiceActive;
  const isTranscribing = voiceState === "transcribing";
  const isProcessing = voiceState === "processing";
  const isSpeaking = voiceState === "speaking";

  let statusText = "Start Continuous Voice Mode";
  if (isActive) {
    if (isTranscribing) statusText = "Transcribing...";
    else if (isProcessing) statusText = "Processing...";
    else if (isSpeaking) statusText = "Speaking...";
    else statusText = "Listening (Continuous Mode Active)";
  }

  // Debug logger utility
  function logDebug(message: string) {
    console.log(`[ContinuousVoice] ${message}`);
  }

  return (
    <div className="relative group">
      {/* Dynamic Glow Layer */}
      {isActive && (
        <div 
          className={`absolute inset-0 rounded-xl bg-sunday-accent/30 animate-pulse blur-md scale-110 duration-1000 transition-all ${
            isSpeaking ? "bg-sunday-accent/40 animate-ping" : ""
          }`}
        ></div>
      )}

      <button
        onClick={handleToggle}
        className={`p-3 rounded-xl transition-all duration-300 flex-shrink-0 flex items-center justify-center relative shadow-lg z-20 border ${
          isActive
            ? isSpeaking
              ? "bg-sunday-accent border-sunday-accent text-white scale-105 shadow-sunday-accent/50"
              : isProcessing || isTranscribing
                ? "bg-sunday-warning/20 border-sunday-warning/40 text-sunday-warning"
                : "bg-emerald-500/20 border-emerald-500/40 text-emerald-400 shadow-emerald-500/20 animate-pulse"
            : "bg-sunday-bg-secondary border-sunday-border text-sunday-text-muted hover:text-sunday-text hover:border-sunday-text-muted hover:scale-105"
        }`}
        title={statusText}
      >
        {isProcessing || isTranscribing ? (
          <Loader2 size={18} className="animate-spin" />
        ) : isActive ? (
          <Radio size={18} className={isSpeaking ? "animate-pulse scale-110 text-white" : "text-emerald-400"} />
        ) : (
          <Mic size={18} className="opacity-70 group-hover:opacity-100" />
        )}
      </button>
    </div>
  );
}
