"""Coding tools for file system access and shell command execution."""

import asyncio
import subprocess
from pathlib import Path
from typing import List, Dict

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


async def read_file(path: str, start_line: int | None = None, end_line: int | None = None) -> str:
    """Read the text contents of a file, optionally paginated."""
    log.info("coding.read_file", target_path=path, start=start_line, end=end_line)

    def _read(p: str) -> str:
        try:
            target = Path(p).expanduser().resolve()
            if not target.exists():
                return f"Error: File not found at {target}."
            if not target.is_file():
                return f"Error: {target} is not a file."

            lines = target.read_text(encoding="utf-8").splitlines()
            
            start = max(1, start_line) if start_line is not None else 1
            end = min(len(lines), end_line) if end_line is not None else len(lines)
            
            if start > end:
                return "Error: start_line cannot be greater than end_line."
                
            output_lines = []
            for i in range(start - 1, end):
                output_lines.append(f"{i + 1}: {lines[i]}")

            content = "\n".join(output_lines)
            
            if len(content) > 15000:
                return content[:15000] + "\n\n... [Content truncated at 15000 chars]"

            return content
        except Exception as e:
            return f"Failed to read file: {str(e)}"

    return await asyncio.to_thread(_read, path)


async def write_file(path: str, content: str) -> str:
    """Write content to a file, replacing its entire contents."""
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


async def grep_search(path: str, query: str) -> str:
    """Search for a string in a file or directory."""
    log.info("coding.grep_search", target_path=path, query=query)
    
    def _grep(p: str, q: str) -> str:
        try:
            target = Path(p).expanduser().resolve()
            if not target.exists():
                return f"Error: Path not found at {target}."
                
            cmd = ["grep", "-rnI", q, str(target)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 1:
                return f"No matches found for '{q}' in {target}"
            elif result.returncode != 0:
                return f"Grep error: {result.stderr}"
                
            output = result.stdout
            if len(output) > 10000:
                return output[:9997] + "..."
            return output
        except Exception as e:
            return f"Error searching: {str(e)}"

    return await asyncio.to_thread(_grep, path, query)


async def multi_replace_file_content(path: str, replacements: List[Dict[str, str]]) -> str:
    """Surgically edit parts of a file by replacing specific target lines."""
    log.info("coding.multi_replace_file_content", target_path=path)
    
    def _replace(p: str, reps: List[Dict[str, str]]) -> str:
        try:
            target = Path(p).expanduser().resolve()
            if not target.exists():
                return f"Error: File not found at {target}."
                
            content = target.read_text(encoding="utf-8")
            
            for rep in reps:
                old_text = rep.get("target_content", "")
                new_text = rep.get("replacement_content", "")
                
                if old_text not in content:
                    return f"Error: Could not find exact match for target content:\n{old_text}"
                if content.count(old_text) > 1:
                    return f"Error: Found multiple matches for target content. Please provide a more specific, unique block of lines."
                    
                content = content.replace(old_text, new_text)
                
            target.write_text(content, encoding="utf-8")
            return f"Success: Applied {len(reps)} replacements to {target}"
            
        except Exception as e:
            return f"Error replacing content: {str(e)}"
            
    return await asyncio.to_thread(_replace, path, replacements)


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
        description="Read the text contents of a file. Use start_line and end_line to paginate large files.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to the file to read.",
                },
                "start_line": {
                    "type": "integer",
                    "description": "Optional. Start line to read (1-indexed).",
                },
                "end_line": {
                    "type": "integer",
                    "description": "Optional. End line to read (inclusive).",
                }
            },
            "required": ["path"],
        },
        func=read_file,
    )

    registry.register(
        name="write_file",
        description="Write content to a file. WARNING: This replaces the ENTIRE file. Use multi_replace_file_content for edits instead.",
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
        name="grep_search",
        description="Search for an exact string or pattern within files or directories. Extremely fast.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to the directory or file to search.",
                },
                "query": {
                    "type": "string",
                    "description": "The string to search for.",
                },
            },
            "required": ["path", "query"],
        },
        func=grep_search,
    )
    
    registry.register(
        name="multi_replace_file_content",
        description="Surgically edit parts of an existing file. Provide exact lines to replace. Highly token-efficient.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to the file.",
                },
                "replacements": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "target_content": {
                                "type": "string",
                                "description": "The exact block of lines to be replaced. Must include exact whitespace/indentation.",
                            },
                            "replacement_content": {
                                "type": "string",
                                "description": "The new content to drop in place of the target_content.",
                            }
                        },
                        "required": ["target_content", "replacement_content"]
                    }
                },
            },
            "required": ["path", "replacements"],
        },
        func=multi_replace_file_content,
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
