"""Python REPL Environment for Auto-Fixer self-healing diagnostic loops."""

import contextlib
import io
import sys
import traceback


def execute_python_code(code: str) -> str:
    """Execute raw Python code, capturing stdout and tracebacks natively.
    
    WARNING: Highly unsafe outside of local development constraints. Built specifically
    for allowing the LLM to write its own test loops and self-diagnose traceback logic.
    """
    stdout_capture = io.StringIO()
    
    try:
        # Heavily restrict mapping but allow logic execution
        with contextlib.redirect_stdout(stdout_capture):
            # We enforce an isolated namespace to prevent contaminating agent state
            exec(code, {"__builtins__": __builtins__}, {})
            
        result = stdout_capture.getvalue()
        return result if result.strip() else "Executed successfully with no stdout output. (hint: use print() to see results)"
    except Exception:
        error_msg = traceback.format_exc()
        return f"Traceback Runtime Exception:\n{error_msg}\n\nPlease analyze this traceback and rewrite the code to fix the logic flaw natively."
