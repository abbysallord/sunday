import { useEffect, useRef, useState } from "react";
import { useChatStore } from "@/stores/chatStore";
import { MessageBubble } from "./MessageBubble";
import { StreamingBubble } from "./StreamingBubble";
import { InputBar } from "./InputBar";
import { VoiceButton } from "@/components/voice/VoiceButton";
import { ContinuousVoiceButton } from "@/components/voice/ContinuousVoiceButton";
import { VoiceIndicator } from "@/components/voice/VoiceIndicator";
import { Sun, X, AlertTriangle, Volume2, VolumeX, Loader2 } from "lucide-react";

export function ChatWindow() {
  const { messages, isGenerating, streamingContent, errorMessage, clearError, ttsEnabled, toggleTTS, activeJobs } =
    useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [showInputBar, setShowInputBar] = useState(false);

  // Auto-scroll to bottom safely without shifting entire app
  useEffect(() => {
    if (messagesEndRef.current) {
      const container = messagesEndRef.current.closest('.overflow-y-auto');
      if (container) {
        container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
      } else {
        messagesEndRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    }
  }, [messages, streamingContent]);

  return (
    <div className="flex flex-col h-full bg-sunday-bg">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto relative">
        {messages.length === 0 && !isGenerating ? (
          <WelcomeScreen />
        ) : (
          <div className="max-w-3xl mx-auto px-4 py-6 space-y-4 pb-32">
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

      {/* Active Jobs panel */}
      {Object.keys(activeJobs).length > 0 && (
        <div className="absolute top-4 right-4 z-20 flex flex-col gap-2">
          {Object.values(activeJobs).map((job) => (
            <div key={job.id} className="bg-sunday-surface/90 backdrop-blur border border-sunday-border shadow-lg rounded-xl p-3 flex items-center gap-3 animate-fade-in w-64">
              <Loader2 className="animate-spin text-sunday-accent" size={16} />
              <div className="flex-1 overflow-hidden">
                <p className="text-xs font-semibold text-sunday-text truncate">Deep Research Active</p>
                <p className="text-[10px] text-sunday-text-muted truncate">{job.message}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error toast */}
      {errorMessage && (
        <div className="max-w-3xl mx-auto px-4 w-full animate-slide-up absolute bottom-[140px] left-0 right-0 z-20">
          <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-sunday-error/10 border border-sunday-error/30 text-sm text-sunday-error shadow-xl shadow-sunday-error/5">
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

      {/* Voice-First Input area */}
      <div className="border-t border-sunday-border bg-sunday-surface/80 backdrop-blur-xl z-10 pb-6 relative rounded-t-[2.5rem] shadow-[0_-10px_40px_-15px_rgba(0,0,0,0.3)]">
        {/* Top controls row */}
        <div className="absolute top-0 right-8 -translate-y-1/2 flex gap-2">
           {/* TTS Toggle Button */}
           <button
             onClick={toggleTTS}
             className={`p-3 border rounded-full shadow-[0_0_20px_rgba(0,0,0,0.2)] transition-all duration-300 ${
               ttsEnabled
                 ? "bg-sunday-accent/20 border-sunday-accent/40 text-sunday-accent hover:bg-sunday-accent/30"
                 : "bg-sunday-surface-hover border-sunday-border text-sunday-text-muted hover:bg-sunday-border hover:text-sunday-text"
             }`}
             title={ttsEnabled ? "Disable read-aloud" : "Enable read-aloud"}
           >
             {ttsEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
           </button>

           {/* Toggle Keyboard Button */}
           <button 
             onClick={() => setShowInputBar(!showInputBar)} 
             className="p-3 bg-sunday-surface-hover border gap-2 flex items-center border-sunday-border rounded-full hover:bg-sunday-border hover:text-sunday-text text-sunday-text-muted shadow-[0_0_20px_rgba(0,0,0,0.2)] transition-all duration-300"
           >
             <kbd className="font-sans text-xs">keyboard</kbd>
           </button>
        </div>

        <div className="max-w-3xl mx-auto px-6 mt-8 relative">
           
           <div className={`flex flex-col items-center gap-4 transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)] ${showInputBar ? 'opacity-100 translate-y-0 relative' : 'opacity-0 translate-y-8 absolute pointer-events-none'}`}>
               <div className="w-full">
                 <InputBar />
               </div>
           </div>

           {/* Voice Button Area - Prominent */}
           <div className={`flex flex-col items-center gap-3 transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)] ${!showInputBar ? 'scale-125 translate-y-0 mt-4' : 'scale-100 translate-y-16 absolute opacity-0 pointer-events-none'}`}>
               <VoiceIndicator />
               <div className="flex items-center gap-4">
                   <ContinuousVoiceButton />
                   <VoiceButton variant="large" />
               </div>
           </div>
           
           <p className="text-[10px] text-sunday-text-muted text-center mt-6 select-none opacity-50 tracking-wide font-medium">
            PRESS <kbd className="px-1 py-0.5 rounded bg-sunday-surface-hover text-sunday-text-muted">/</kbd> TO TYPE
            {" · "}
            <kbd className="px-1 py-0.5 rounded bg-sunday-surface-hover text-sunday-text-muted">ESC</kbd> TO STOP
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
