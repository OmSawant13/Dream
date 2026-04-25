import math

def calculate(expression: str) -> str:
    """Executes a mathematical expression. Use this for ANY math questions."""
    try:
        # Use a safe eval-like approach or simple eval for math
        # We'll allow basic math functions
        allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
        result = eval(expression, {"__builtins__": None}, allowed_names)
        return f"The result is {result}, boss. Simple math."
    except Exception as e:
        return f"Math Error: {e}. Maybe try a different formula?"
