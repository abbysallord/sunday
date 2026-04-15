import { useState, useEffect } from "react";
import { X, Save, Loader2 } from "lucide-react";
import { api, BackendSettings } from "@/services/api";

interface SettingsDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsDialog({ isOpen, onClose }: SettingsDialogProps) {
  const [settings, setSettings] = useState<BackendSettings | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [formData, setFormData] = useState<Record<string, string>>({});

  useEffect(() => {
    if (isOpen) {
      api.getSettings().then((res) => {
        setSettings(res);
        setFormData({
          llm_primary_provider: res.llm.primary_provider,
          llm_primary_model: res.llm.primary_model,
          llm_fallback_provider: res.llm.fallback_provider,
          llm_offline_model: res.llm.offline_model,
          voice_tts_voice: res.voice.tts_voice,
          voice_stt_model: res.voice.stt_model,
        });
      });
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = async () => {
    setIsSaving(true);
    await api.updateSettings(formData);
    setIsSaving(false);
    onClose();
  };

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in">
      <div className="bg-sunday-surface border border-sunday-border shadow-2xl rounded-2xl w-full max-w-lg overflow-hidden animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-sunday-border/50">
          <h2 className="text-lg font-semibold text-sunday-text">Settings</h2>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-sunday-surface-hover text-sunday-text-muted hover:text-sunday-text transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6 max-h-[60vh] overflow-y-auto">
          {!settings ? (
            <div className="flex justify-center p-8">
              <Loader2 className="animate-spin text-sunday-accent" />
            </div>
          ) : (
            <>
              {/* LLM Settings */}
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-sunday-text-muted uppercase tracking-wider">AI Models</h3>
                
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-sunday-text mb-1">Primary Provider</label>
                    <select
                      name="llm_primary_provider"
                      value={formData.llm_primary_provider}
                      onChange={handleChange}
                      className="w-full bg-sunday-surface-hover border border-sunday-border rounded-lg px-3 py-2 text-sm text-sunday-text focus:outline-none focus:border-sunday-accent"
                    >
                      <option value="groq">Groq</option>
                      <option value="google">Google AI Studio</option>
                      <option value="ollama">Ollama (Local)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm text-sunday-text mb-1">Primary Model</label>
                    <input
                      name="llm_primary_model"
                      value={formData.llm_primary_model}
                      onChange={handleChange}
                      className="w-full bg-sunday-surface-hover border border-sunday-border rounded-lg px-3 py-2 text-sm text-sunday-text focus:outline-none focus:border-sunday-accent"
                    />
                  </div>
                </div>
              </div>

              <hr className="border-sunday-border/50" />

              {/* Voice Settings */}
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-sunday-text-muted uppercase tracking-wider">Voice</h3>
                
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-sunday-text mb-1">TTS Voice Model</label>
                    <input
                      name="voice_tts_voice"
                      value={formData.voice_tts_voice}
                      onChange={handleChange}
                      className="w-full bg-sunday-surface-hover border border-sunday-border rounded-lg px-3 py-2 text-sm text-sunday-text focus:outline-none focus:border-sunday-accent"
                    />
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 px-6 py-4 border-t border-sunday-border/50 bg-sunday-surface/50">
          <button onClick={onClose} className="px-4 py-2 rounded-lg text-sm font-medium text-sunday-text-muted hover:text-sunday-text hover:bg-sunday-surface-hover transition-colors">
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving || !settings}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-white bg-sunday-accent hover:bg-sunday-accent-hover disabled:opacity-50 transition-colors"
          >
            {isSaving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}
