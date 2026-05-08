"""Coding tools for file system access and shell command execution."""

import asyncio
import subprocess
from pathlib import Path

from sunday.agents.tools.registry import ToolRegistry
from sunday.utils.logging import log


async def list_directory(path: str) -> str:
    """List files and directories at the given path."""
    log.info("coding.list_directory", target_path=path)

    def _list(p: str) -> str:
        try:
            target = Path(p).expanduser().resolve()
            if not target.exists():
                return f"Error: No directory found at {target}."
            if not target.is_dir():
                return f"Error: {target} is a file, not a directory."

            items = []
            for x in target.iterdir():
                icon = "📁" if x.is_dir() else "📄"
                items.append(f"{icon} {x.name}")

            if not items:
                return "Directory is empty."

            return "\n".join(sorted(items))
        except Exception as e:
            return f"Failed to list directory: {str(e)}"

    return await asyncio.to_thread(_list, path)


async def read_file(path: str) -> str:
    """Read the text contents of a file."""
    log.info("coding.read_file", target_path=path)

    def _read(p: str) -> str:
        try:
            target = Path(p).expanduser().resolve()
            if not target.exists():
                return f"Error: File not found at {target}."
            if not target.is_file():
                return f"Error: {target} is not a file."

            content = target.read_text(encoding="utf-8")

            if len(content) > 15000:
                return content[:15000] + "\n\n... [Content truncated at 15000 chars]"

            return content
        except Exception as e:
            return f"Failed to read file: {str(e)}"

    return await asyncio.to_thread(_read, path)


async def write_file(path: str, content: str) -> str:
    """Write content to a file, creating parent directories if needed."""
    log.info("coding.write_file", target_path=path)

    def _write(p: str, c: str) -> str:
        try:
            target = Path(p).expanduser().resolve()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(c, encoding="utf-8")
            return f"Success: File written to {target}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    return await asyncio.to_thread(_write, path, content)


async def run_shell(command: str) -> str:
    """Execute a shell command and return stdout/stderr."""
    log.info("coding.run_shell", cmd=command)

    def _run(cmd: str) -> str:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            output = result.stdout or ""
            error = result.stderr or ""

            combined = []
            if output:
                combined.append(f"[STDOUT]:\n{output}")
            if error:
                combined.append(f"[STDERR]:\n{error}")

            if not combined:
                combined.append(
                    f"Command executed successfully (exit code {result.returncode}) with no output."
                )

            final_str = "\n".join(combined)

            if len(final_str) > 10000:
                return final_str[:9997] + "..."

            return final_str
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 30 seconds."
        except Exception as e:
            return f"Error executing command: {str(e)}"

    return await asyncio.to_thread(_run, command)


def register_coding_tools(registry: ToolRegistry) -> None:
    """Register file system and shell tools for the Coding Agent."""
    registry.register(
        name="list_directory",
        description="List all files and folders in a directory.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to the directory. Use '~' for home directory.",
                }
            },
            "required": ["path"],
        },
        func=list_directory,
    )

    registry.register(
        name="read_file",
        description="Read the text contents of a file.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to the file to read.",
                }
            },
            "required": ["path"],
        },
        func=read_file,
    )

    registry.register(
        name="write_file",
        description="Write content to a file. Creates the file and parent directories if they don't exist.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path for the file to write.",
                },
                "content": {
                    "type": "string",
                    "description": "The full text content to write to the file.",
                },
            },
            "required": ["path", "content"],
        },
        func=write_file,
    )

    registry.register(
        name="run_shell",
        description=(
            "Execute a bash shell command and return the output. "
            "Use for running scripts, installing packages, checking system state, etc. "
            "Examples: 'ls -la', 'python script.py', 'pip install package'."
        ),
        parameters={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute.",
                }
            },
            "required": ["command"],
        },
        func=run_shell,
    )
