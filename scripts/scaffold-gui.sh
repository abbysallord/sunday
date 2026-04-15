#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
PROJECT_ROOT="$(pwd)"
GUI_DIR="$PROJECT_ROOT/gui"

echo "🎨 Scaffolding SUNDAY GUI..."
echo "=============================="

# ---- Clean and init ----
rm -rf "$GUI_DIR"
mkdir -p "$GUI_DIR"
cd "$GUI_DIR"

# ---- package.json ----
cat > package.json << 'EOF'
{
  "name": "sunday-gui",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint 'src/**/*.{ts,tsx}' --max-warnings 0",
    "preview": "vite preview",
    "tauri": "tauri"
  },
  "dependencies": {
    "@tauri-apps/api": "^2.5.0",
    "@tauri-apps/plugin-shell": "^2.2.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-markdown": "^9.0.1",
    "zustand": "^5.0.0",
    "lucide-react": "^0.468.0"
  },
  "devDependencies": {
    "@tauri-apps/cli": "^2.5.0",
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.20",
    "eslint": "^9.15.0",
    "eslint-plugin-react-hooks": "^5.0.0",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.15",
    "typescript": "~5.6.3",
    "vite": "^6.0.0"
  }
}
EOF

# ---- TypeScript configs ----
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"]
}
EOF

cat > tsconfig.node.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["vite.config.ts"]
}
EOF

# ---- Vite config ----
cat > vite.config.ts << 'EOF'
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

const host = process.env.TAURI_DEV_HOST;

export default defineConfig(async () => ({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    host: host || false,
    hmr: host
      ? {
          protocol: "ws",
          host,
          port: 1421,
        }
      : undefined,
    watch: {
      ignored: ["**/src-tauri/**"],
    },
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/ws": {
        target: "ws://127.0.0.1:8000",
        ws: true,
      },
      "/health": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
}));
EOF

# ---- Tailwind ----
cat > tailwind.config.ts << 'EOF'
import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        sunday: {
          bg: "#0a0a0f",
          surface: "#12121a",
          "surface-hover": "#1a1a25",
          border: "#1e1e2e",
          "border-active": "#2d2d44",
          text: "#e4e4ef",
          "text-muted": "#6b6b80",
          accent: "#7c5bf5",
          "accent-hover": "#6a4be0",
          "accent-glow": "rgba(124, 91, 245, 0.15)",
          user: "#1e3a5f",
          assistant: "#1a1a25",
          success: "#34d399",
          error: "#f87171",
          warning: "#fbbf24",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s ease-in-out infinite",
        "fade-in": "fadeIn 0.2s ease-out",
        "slide-up": "slideUp 0.2s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
EOF

cat > postcss.config.js << 'EOF'
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
EOF

# ---- ESLint ----
cat > eslint.config.js << 'EOF'
import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "src-tauri"] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ["**/*.{ts,tsx}"],
    plugins: {
      "react-hooks": reactHooks,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "@typescript-eslint/no-unused-vars": "warn",
    },
  }
);
EOF

# ---- index.html ----
cat > index.html << 'EOF'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/sunday.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>SUNDAY</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
EOF

# ---- SVG icon ----
cat > public/sunday.svg << 'SVGEOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#7c5bf5"/>
      <stop offset="100%" style="stop-color:#5b8bf5"/>
    </linearGradient>
  </defs>
  <circle cx="50" cy="50" r="45" fill="url(#g)"/>
  <text x="50" y="62" font-family="Inter,sans-serif" font-size="32" font-weight="700" fill="white" text-anchor="middle">S</text>
</svg>
SVGEOF
mkdir -p public

# move svg
mv sunday.svg public/ 2>/dev/null || true

# ---- Source directories ----
mkdir -p src/{components/{chat,voice,sidebar,common},hooks,stores,services,types,styles}

# ---- Global CSS ----
cat > src/styles/globals.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    @apply bg-sunday-bg text-sunday-text font-sans antialiased;
    overflow: hidden;
    user-select: none;
  }

  /* Custom scrollbar */
  ::-webkit-scrollbar {
    width: 6px;
  }

  ::-webkit-scrollbar-track {
    background: transparent;
  }

  ::-webkit-scrollbar-thumb {
    @apply bg-sunday-border rounded-full;
  }

  ::-webkit-scrollbar-thumb:hover {
    @apply bg-sunday-border-active;
  }

  /* Make text in chat selectable */
  .message-content {
    user-select: text;
  }

  /* Markdown styles inside messages */
  .message-content h1,
  .message-content h2,
  .message-content h3 {
    @apply font-semibold mt-3 mb-1;
  }

  .message-content h1 { @apply text-xl; }
  .message-content h2 { @apply text-lg; }
  .message-content h3 { @apply text-base; }

  .message-content p {
    @apply mb-2 leading-relaxed;
  }

  .message-content ul,
  .message-content ol {
    @apply ml-4 mb-2 space-y-1;
  }

  .message-content ul { @apply list-disc; }
  .message-content ol { @apply list-decimal; }

  .message-content code {
    @apply font-mono text-sm bg-sunday-surface-hover px-1.5 py-0.5 rounded;
  }

  .message-content pre {
    @apply bg-sunday-surface-hover rounded-lg p-4 my-2 overflow-x-auto;
  }

  .message-content pre code {
    @apply bg-transparent p-0;
  }

  .message-content a {
    @apply text-sunday-accent underline underline-offset-2;
  }

  .message-content blockquote {
    @apply border-l-2 border-sunday-accent pl-3 italic text-sunday-text-muted my-2;
  }
}
EOF

# ---- Tauri backend (Rust) ----
mkdir -p src-tauri/src

cat > src-tauri/Cargo.toml << 'EOF'
[package]
name = "sunday-gui"
version = "0.1.0"
description = "SUNDAY Desktop Application"
authors = ["SUNDAY Team"]
edition = "2021"

[lib]
name = "sunday_gui_lib"
crate-type = ["staticlib", "cdylib", "rlib"]

[build-dependencies]
tauri-build = { version = "2", features = [] }

[dependencies]
tauri = { version = "2", features = ["tray-icon"] }
tauri-plugin-shell = "2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
EOF

cat > src-tauri/build.rs << 'EOF'
fn main() {
    tauri_build::build()
}
EOF

cat > src-tauri/tauri.conf.json << 'EOF'
{
  "$schema": "https://raw.githubusercontent.com/tauri-apps/tauri/dev/crates/tauri-utils/schema.json",
  "productName": "SUNDAY",
  "version": "0.1.0",
  "identifier": "com.sunday.app",
  "build": {
    "beforeDevCommand": "npm run dev",
    "devUrl": "http://localhost:1420",
    "beforeBuildCommand": "npm run build",
    "frontendDist": "../dist"
  },
  "app": {
    "title": "SUNDAY",
    "windows": [
      {
        "title": "SUNDAY",
        "width": 1200,
        "height": 800,
        "minWidth": 800,
        "minHeight": 600,
        "resizable": true,
        "decorations": true,
        "transparent": false
      }
    ],
    "security": {
      "csp": null
    },
    "trayIcon": {
      "iconPath": "icons/icon.png",
      "iconAsTemplate": true
    }
  }
}
EOF

cat > src-tauri/src/lib.rs << 'EOF'
use tauri::Manager;

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! SUNDAY is ready.", name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![greet])
        .setup(|app| {
            #[cfg(debug_assertions)]
            {
                let window = app.get_webview_window("main").unwrap();
                window.open_devtools();
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running SUNDAY");
}
EOF

cat > src-tauri/src/main.rs << 'EOF'
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    sunday_gui_lib::run()
}
EOF

# Create icons directory with a placeholder
mkdir -p src-tauri/icons
# Generate a simple 32x32 PNG placeholder (1x1 purple pixel scaled)
# We'll use the SVG as source later; for now Tauri needs something here
cp public/sunday.svg src-tauri/icons/ 2>/dev/null || true

# Tauri needs a png icon — create a minimal one with a script
# For now, just touch it so the build doesn't fail on missing icon
python3 -c "
import struct, zlib
def create_png(w, h, color):
    def chunk(ctype, data):
        c = ctype + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    raw = b''
    for _ in range(h):
        raw += b'\x00' + bytes(color * w)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')
with open('src-tauri/icons/icon.png', 'wb') as f:
    f.write(create_png(32, 32, [124, 91, 245]))
with open('src-tauri/icons/32x32.png', 'wb') as f:
    f.write(create_png(32, 32, [124, 91, 245]))
with open('src-tauri/icons/128x128.png', 'wb') as f:
    f.write(create_png(128, 128, [124, 91, 245]))
with open('src-tauri/icons/128x128@2x.png', 'wb') as f:
    f.write(create_png(256, 256, [124, 91, 245]))
print('Icons generated')
" 2>/dev/null || echo "Warning: Could not generate icons, you may need to add them manually"

echo ""
echo "🎨 GUI scaffold complete!"
echo ""
echo "Next: Run 'cd gui && npm install' then create the React source files."
echo ""
