import { useEffect } from "react";
import { Layout } from "@/components/common/Layout";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { useChatStore } from "@/stores/chatStore";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";

function App() {
  const connect = useChatStore((s) => s.connect);

  useEffect(() => {
    connect();
  }, [connect]);

  // Register global keyboard shortcuts
  useKeyboardShortcuts();

  return <Layout sidebar={<Sidebar />} main={<ChatWindow />} />;
}

export default App;
