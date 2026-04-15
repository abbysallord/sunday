from fastapi import APIRouter
from pydantic import BaseModel

from sunday.config.settings import PROJECT_ROOT, settings
from sunday.utils.logging import log

router = APIRouter(tags=["Settings"])


class SettingsUpdate(BaseModel):
    llm_primary_provider: str | None = None
    llm_primary_model: str | None = None
    llm_fallback_provider: str | None = None
    llm_fallback_model: str | None = None
    llm_offline_model: str | None = None
    voice_tts_voice: str | None = None
    voice_stt_model: str | None = None


@router.get("/")
async def get_settings():
    return {
        "llm": settings.llm.model_dump(),
        "voice": settings.voice.model_dump(),
    }


@router.patch("/")
async def update_settings(updates: SettingsUpdate):
    updates_dict = updates.model_dump(exclude_unset=True)
    if not updates_dict:
        return {"status": "ok"}

    env_path = PROJECT_ROOT / ".env"

    # Update memory
    if "llm_primary_provider" in updates_dict:
        settings.llm.primary_provider = updates_dict["llm_primary_provider"]
    if "llm_primary_model" in updates_dict:
        settings.llm.primary_model = updates_dict["llm_primary_model"]
    if "llm_fallback_provider" in updates_dict:
        settings.llm.fallback_provider = updates_dict["llm_fallback_provider"]
    if "llm_fallback_model" in updates_dict:
        settings.llm.fallback_model = updates_dict["llm_fallback_model"]
    if "llm_offline_model" in updates_dict:
        settings.llm.offline_model = updates_dict["llm_offline_model"]
    if "voice_tts_voice" in updates_dict:
        settings.voice.tts_voice = updates_dict["voice_tts_voice"]
    if "voice_stt_model" in updates_dict:
        settings.voice.stt_model = updates_dict["voice_stt_model"]

    # Read the current .env lines
    content = env_path.read_text(encoding="utf-8") if env_path.exists() else ""

    # Map frontend keys to ENV keys
    env_updates = {}
    for k, v in updates_dict.items():
        if k.startswith("llm_"):
            env_var = f"SUNDAY_LLM_{k[4:].upper()}"
        elif k.startswith("voice_"):
            env_var = f"SUNDAY_{k.upper()}"
        else:
            continue
        env_updates[env_var] = str(v)

    # Modify content line by line or append
    new_lines = []
    lines = content.splitlines()
    handled_keys = set()

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue

        if "=" in line:
            key, val_curr = line.split("=", 1)
            key = key.strip()
            if key in env_updates:
                new_lines.append(f"{key}={env_updates[key]}")
                handled_keys.add(key)
                continue

        new_lines.append(line)

    # Append unhandled keys
    for k, v in env_updates.items():
        if k not in handled_keys:
            new_lines.append(f"{k}={v}")

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    log.info("settings.updated", updates=list(updates_dict.keys()))
    return {"status": "ok"}
