import React from "react";

interface LayoutProps {
  sidebar: React.ReactNode;
  main: React.ReactNode;
}

export function Layout({ sidebar, main }: LayoutProps) {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-sunday-bg">
      {/* Sidebar */}
      <div className="w-72 flex-shrink-0 border-r border-sunday-border flex flex-col bg-sunday-surface">
        {sidebar}
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">{main}</div>
    </div>
  );
}
