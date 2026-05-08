"""SUNDAY CLI — interactive terminal chat with full agent support.

Usage:
    python -m sunday.cli          # Interactive chat
    sunday-chat                   # Same (via pyproject.toml entry point)

Features:
    - Full agent routing (Secretary, Research, Coding, Memory, Verification)
    - Persistent memory via ChromaDB
    - Conversation history via SQLite
    - Colorized output with Rich
    - Special commands: /quit, /new, /agents, /memory <query>, /help
"""

import asyncio
import sys

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

# Custom theme for SUNDAY
_theme = Theme(
    {
        "sunday": "bold magenta",
        "user": "bold cyan",
        "status": "dim yellow",
        "error": "bold red",
        "info": "dim white",
        "agent": "bold green",
        "memory": "italic dim cyan",
    }
)

console = Console(theme=_theme)


def _print_banner() -> None:
    """Print the SUNDAY welcome banner."""
    banner = Text()
    banner.append("  ☀️  ", style="bold yellow")
    banner.append("SUNDAY", style="bold magenta")
    banner.append(" — Simply Unique Natural Daily Assistant for YOU\n", style="dim white")
    banner.append("      Type a message to chat. Use /help for commands.\n", style="dim white")
    banner.append("      Press Ctrl+C or type /quit to exit.\n", style="dim white")

    console.print(Panel(banner, border_style="magenta", padding=(0, 2)))
    console.print()


def _print_help() -> None:
    """Print available commands."""
    console.print("\n[sunday]Available commands:[/sunday]")
    console.print("  [bold]/help[/bold]             — Show this help message")
    console.print("  [bold]/quit[/bold]             — Exit SUNDAY")
    console.print("  [bold]/new[/bold]              — Start a new conversation")
    console.print("  [bold]/agents[/bold]           — List available agents")
    console.print("  [bold]/memory <query>[/bold]   — Search long-term memory")
    console.print("  [bold]/history[/bold]          — Show current conversation history")
    console.print()


async def _run_cli() -> None:
    """Main CLI event loop."""
    # Late imports to avoid import-time side effects when just importing the module
    from sunday.agents.manager import AgentManager
    from sunday.core.llm.router import llm_router
    from sunday.database.engine import db
    from sunday.database.vector import vector_db
    from sunday.models.messages import Conversation, Message, MessageSource, Role
    from sunday.utils.logging import log

    # Initialize
    agent_manager = AgentManager(llm_router=llm_router)
    await db.connect()

    # Print banner
    _print_banner()

    # Show loaded agents
    agents_list = list(agent_manager.agents.keys())
    console.print(f"[info]Agents loaded: {', '.join(agents_list)}[/info]")
    console.print()

    # State
    conversation = Conversation()
    await db.create_conversation(conversation)
    conversation_id = conversation.id
    max_context = 20

    while True:
        try:
            # Prompt
            try:
                user_input = console.input("[user]You → [/user]").strip()
            except EOFError:
                break

            if not user_input:
                continue

            # Handle special commands
            if user_input.startswith("/"):
                cmd_parts = user_input.split(maxsplit=1)
                cmd = cmd_parts[0].lower()

                if cmd in ("/quit", "/exit", "/q"):
                    console.print("\n[sunday]Goodbye! ☀️[/sunday]\n")
                    break

                elif cmd == "/help":
                    _print_help()
                    continue

                elif cmd == "/new":
                    conversation = Conversation()
                    await db.create_conversation(conversation)
                    conversation_id = conversation.id
                    console.print("[info]Started new conversation.[/info]\n")
                    continue

                elif cmd == "/agents":
                    console.print("\n[sunday]Available Agents:[/sunday]")
                    for _agent_id, agent in agent_manager.agents.items():
                        info = agent.info
                        console.print(f"  [agent]{info.name}[/agent] ({info.id})")
                        console.print(f"    {info.description}")
                        if info.capabilities:
                            kws = []
                            for cap in info.capabilities:
                                kws.extend(cap.keywords[:5])
                            console.print(f"    [dim]Keywords: {', '.join(kws[:10])}[/dim]")
                    console.print()
                    continue

                elif cmd == "/memory":
                    query = cmd_parts[1] if len(cmd_parts) > 1 else ""
                    if not query:
                        console.print("[error]Usage: /memory <search query>[/error]\n")
                        continue
                    memories = vector_db.query_memories(query, limit=5)
                    if memories:
                        console.print(f"\n[sunday]Memory results for '{query}':[/sunday]")
                        for i, mem in enumerate(memories, 1):
                            console.print(f"  [memory]{i}. {mem}[/memory]")
                    else:
                        console.print(f"[info]No memories found for '{query}'[/info]")
                    console.print()
                    continue

                elif cmd == "/history":
                    if not conversation.messages:
                        console.print("[info]No messages in this conversation yet.[/info]\n")
                        continue
                    console.print("\n[sunday]Conversation History:[/sunday]")
                    for msg in conversation.messages[-10:]:
                        role_style = "user" if msg.role == Role.USER else "sunday"
                        label = "You" if msg.role == Role.USER else "SUNDAY"
                        console.print(f"  [{role_style}]{label}:[/{role_style}] {msg.content[:200]}")
                    console.print()
                    continue

                else:
                    console.print(f"[error]Unknown command: {cmd}. Type /help for options.[/error]\n")
                    continue

            # Save user message
            user_msg = Message(role=Role.USER, content=user_input, source=MessageSource.TEXT)
            conversation.add_message(user_msg)
            await db.save_message(conversation_id, user_msg)

            # Store memory in background
            try:
                vector_db.add_memory(
                    user_msg.id,
                    f"User: {user_input}",
                    {"conversation_id": conversation_id, "role": "user"},
                )
            except Exception as e:
                log.warning("cli.memory_store_failed", error=str(e))

            # Route to agent
            active_agent = agent_manager.determine_agent(user_input)
            agent_name = active_agent.info.name
            console.print(f"[status]  ↳ {agent_name}[/status]")

            # Stream response
            context = conversation.get_context_messages(max_context)[:-1]
            full_response = []

            console.print()
            try:
                # Collect all tokens and render as markdown at the end
                with Live(Text("Thinking...", style="dim"), console=console, refresh_per_second=8) as live:
                    async for token in active_agent.stream(message=user_msg, context=context):
                        full_response.append(token)
                        current_text = "".join(full_response)
                        try:
                            live.update(Markdown(current_text))
                        except Exception:
                            live.update(Text(current_text))

                response_text = "".join(full_response)

            except Exception as e:
                error_str = str(e)
                if "all llm providers failed" in error_str.lower():
                    console.print(f"[error]Error: {error_str}[/error]\n")
                else:
                    console.print(f"[error]Error: {error_str}[/error]\n")
                continue

            if not response_text.strip():
                response_text = "(No response generated)"

            # Save assistant message
            assistant_msg = Message(role=Role.ASSISTANT, content=response_text)
            conversation.add_message(assistant_msg)
            await db.save_message(conversation_id, assistant_msg)

            # Store assistant memory
            try:
                vector_db.add_memory(
                    assistant_msg.id,
                    f"SUNDAY: {response_text}",
                    {"conversation_id": conversation_id, "role": "assistant"},
                )
            except Exception as e:
                log.warning("cli.memory_store_failed", error=str(e))

            console.print()

        except KeyboardInterrupt:
            console.print("\n\n[sunday]Goodbye! ☀️[/sunday]\n")
            break
        except Exception as e:
            console.print(f"[error]Unexpected error: {e}[/error]\n")
            continue


def main():
    """Entry point for the CLI."""
    try:
        asyncio.run(_run_cli())
    except KeyboardInterrupt:
        console.print("\n[sunday]Goodbye! ☀️[/sunday]")
        sys.exit(0)


if __name__ == "__main__":
    main()
