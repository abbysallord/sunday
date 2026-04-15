import { useEffect } from "react";
import { Layout } from "@/components/common/Layout";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { useChatStore } from "@/stores/chatStore";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import { SettingsDialog } from "@/components/settings/SettingsDialog";

function App() {
  const { connect, isSettingsOpen, setSettingsOpen } = useChatStore();

  useEffect(() => {
    connect();
  }, [connect]);

  // Register global keyboard shortcuts
  useKeyboardShortcuts();

  return (
    <>
      <Layout sidebar={<Sidebar />} main={<ChatWindow />} />
      <SettingsDialog isOpen={isSettingsOpen} onClose={() => setSettingsOpen(false)} />
    </>
  );
}

export default App;
