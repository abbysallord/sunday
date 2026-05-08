# Ollama Setup Guide for SUNDAY

Ollama is SUNDAY's offline fallback LLM. When Groq and Gemini are unavailable or rate-limited, SUNDAY falls back to a locally-running Ollama model.

## Hardware Tiers

| RAM | Recommended Model | Pull Command |
|-----|-------------------|--------------|
| < 8 GB | `qwen2.5:0.5b` or `tinyllama` | `ollama pull qwen2.5:0.5b` |
| 8–16 GB | `qwen2.5:3b` *(default)* | `ollama pull qwen2.5:3b` |
| > 16 GB | `qwen2.5:7b` or `mistral:7b` | `ollama pull qwen2.5:7b` |

**Current hardware:** AMD Ryzen AI 7 350, 14 GB RAM → `qwen2.5:3b` is the right choice.

## Quick Start (Local)

```bash
# Start the Ollama server
ollama serve

# Pull the model (one-time)
ollama pull qwen2.5:3b

# Verify it works
ollama run qwen2.5:3b "hello"
```

## Switching Models

Set the env var before starting SUNDAY:

```bash
SUNDAY_LLM_OFFLINE_MODEL=qwen2.5:0.5b uvicorn sunday.main:app
```

Or add it to your `.env` file:

```
SUNDAY_LLM_OFFLINE_MODEL=qwen2.5:3b
```

## Pointing SUNDAY at a Remote Ollama Instance

If Ollama is running on another machine or a cloud VPS:

```bash
OLLAMA_BASE_URL=http://your-server-ip:11434 uvicorn sunday.main:app
```

Or in `.env`:
```
OLLAMA_BASE_URL=http://your-server-ip:11434
```

## Cloud Deployment Options (Cheapest First)

When local hardware is too slow, run Ollama on a cheap cloud server:

### Option 1 — Hetzner VPS (~$6/month, CPU-only)
- **CX22**: 2 vCPU, 4 GB RAM → `qwen2.5:0.5b` only
- **CX32**: 4 vCPU, 8 GB RAM → `qwen2.5:3b` works well
- CPU inference is slow (~5–15 tok/s) but fine for fallback use

```bash
# On the Hetzner VPS
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:3b
OLLAMA_HOST=0.0.0.0 ollama serve
```

### Option 2 — Vast.ai (GPU, pay-per-hour)
- Rent an RTX 3090 for ~$0.20/hr when you need fast inference
- `qwen2.5:7b` runs at ~60 tok/s on a 3090
- Good for burst usage, not always-on

### Option 3 — RunPod (GPU, serverless)
- Serverless GPU pods — pay only when a request comes in
- More complex setup but cheapest for low-traffic use

## Performance Tips for Local CPU Inference

1. **Close other apps** — Ollama needs all available RAM
2. **Use quantized models** — `qwen2.5:3b` is already Q4 quantized
3. **Set thread count** — Ollama auto-detects, but you can override:
   ```bash
   OLLAMA_NUM_THREADS=6 ollama serve
   ```
4. **AMD iGPU acceleration** — The Radeon 860M can accelerate inference via ROCm, but setup is complex. Skip for now; CPU is sufficient for the 3B model.
