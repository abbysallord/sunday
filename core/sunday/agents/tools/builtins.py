"""Builtin minimal system tools to demonstrate baseline integrations."""

import datetime
import math
import os
import platform

from sunday.agents.tools.python_repl import execute_python_code
from sunday.agents.tools.registry import ToolRegistry


def get_current_time(timezone: str = "local") -> str:
    """Provides realtime standard system clock output."""
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


def get_system_platform() -> str:
    """Extract standard OS information mapping."""
    return f"OS: {platform.system()} {platform.release()} ({os.name})"


def calculate_math(expression: str) -> str:
    """Safely calculate simple numeric equations using ast.literal_eval-safe parsing."""
    import ast
    import operator

    _OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }
    _MATH_FUNCS = {
        name: getattr(math, name)
        for name in dir(math)
        if not name.startswith("_") and callable(getattr(math, name))
    }

    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.operand))
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in _MATH_FUNCS:
                args = [_eval(a) for a in node.args]
                return _MATH_FUNCS[node.func.id](*args)
        raise ValueError(f"Unsupported expression: {ast.dump(node)}")

    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval(tree.body)
        return str(result)
    except Exception as e:
        return f"Calculation failed: {str(e)}"


def register_builtins(registry: ToolRegistry) -> None:
    """Register all builtin native plugins."""
    registry.register(
        name="get_current_time",
        description="Fetch the current system time and date.",
        parameters={
            "type": "object",
            "properties": {
                "timezone": {"type": "string", "description": "Optional timezone identifier."}
            },
        },
        func=get_current_time,
    )

    registry.register(
        name="get_system_platform",
        description="Return diagnostic os release string specifying platform constraints.",
        parameters={"type": "object", "properties": {}},
        func=get_system_platform,
    )

    registry.register(
        name="calculate_math",
        description="Evaluate mathematical expressions. Valid elements: numeric operations (+, -, *, /) and math module functions (sin, cos, sqrt).",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate",
                }
            },
            "required": ["expression"],
        },
        func=calculate_math,
    )

    registry.register(
        name="execute_python_code",
        description="Write and execute raw python script code internally. Use this to explicitly auto-fix algorithms, verify file structures, or debug your own native traces if other tools fail.",
        parameters={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The block of raw Python code to execute. Variables do not persist across multiple executions.",
                }
            },
            "required": ["code"],
        },
        func=execute_python_code,
    )
