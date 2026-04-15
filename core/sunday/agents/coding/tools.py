"""Tool configurations strictly granting OS capabilities smoothly natively."""

import subprocess
from pathlib import Path

from sunday.agents.tools.registry import ToolRegistry
from sunday.utils.logging import log


def list_directory(path: str) -> str:
    """Return explicit structural lists indicating directories and file endpoints cleanly."""
    log.info("coding.list_directory", target_path=path)
    try:
        target = Path(path).expanduser().resolve()
        if not target.exists():
            return f"Error: No directory found at {target}."
        if not target.is_dir():
            return f"Error: The target {target} is a file, not a directory."

        items = []
        for x in target.iterdir():
            icon = "📁" if x.is_dir() else "📄"
            items.append(f"{icon} {x.name}")

        if not items:
            return "Directory is empty."

        return "\n".join(sorted(items))
    except Exception as e:
        return f"Failed to traverse directory: {str(e)}"


def read_file(path: str) -> str:
    """Yield explicit python or text contexts bounded strictly."""
    log.info("coding.read_file", target_path=path)
    try:
        target = Path(path).expanduser().resolve()
        if not target.exists() or not target.is_file():
            return f"Error: File at {target} does not exist natively."

        content = target.read_text(encoding="utf-8")

        # Token protections implicitly
        if len(content) > 15000:
            return content[:15000] + "\n\n... [Content strictly truncated for exceeding limits.]"

        return content
    except Exception as e:
        return f"Failed to read file: {str(e)}"


def write_file(path: str, content: str) -> str:
    """Overwrites or injects explicit blocks strictly physically natively."""
    log.info("coding.write_file", target_path=path)
    try:
        target = Path(path).expanduser().resolve()

        # Create explicit parent bounds if they do not magically exist natively
        target.parent.mkdir(parents=True, exist_ok=True)

        target.write_text(content, encoding="utf-8")
        return f"Success: File successfully written natively and saved to -> {target}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


def run_shell(command: str) -> str:
    """Execute raw bash logic locally tracking STDOUT natively."""
    log.info("coding.run_shell", cmd=command)
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        output = result.stdout or ""
        error = result.stderr or ""

        combined = []
        if output:
            combined.append(f"[STDOUT]:\n{output}")
        if error:
            combined.append(f"[STDERR]:\n{error}")

        if not combined:
            return "Command executed structurally with zero output parameters locally."

        final_str = "\n".join(combined)

        # Token bounds protection implicitly
        if len(final_str) > 10000:
            return final_str[:9997] + "..."

        return final_str
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 10 bounds natively."
    except Exception as e:
        return f"Bash structural execution explicitly failed: {str(e)}"


def register_coding_tools(registry: ToolRegistry) -> None:
    """Passively map structural references explicitly."""
    registry.register(
        name="list_directory",
        description="List all explicit files and folders securely mapped within an OS level directory boundary.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The absolute or relative directory structure. Use '.' for current working structure.",
                }
            },
            "required": ["path"],
        },
        func=list_directory,
    )

    registry.register(
        name="read_file",
        description="Read structural textual contents completely securely off a file.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The exact absolute mapping linking directly.",
                }
            },
            "required": ["path"],
        },
        func=read_file,
    )

    registry.register(
        name="write_file",
        description="Creates or totally overwrites structural definitions dynamically mapping natively.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The destination endpoint natively."},
                "content": {
                    "type": "string",
                    "description": "The massive explicit textual content block logically constructed.",
                },
            },
            "required": ["path", "content"],
        },
        func=write_file,
    )

    registry.register(
        name="run_shell",
        description="Evaluate literal Bash logic sequences mapping execution boundaries completely isolated structurally. e.g. 'pip install x', 'ls -la', 'python script.py'",
        parameters={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The precise terminal hook string command natively.",
                }
            },
            "required": ["command"],
        },
        func=run_shell,
    )
