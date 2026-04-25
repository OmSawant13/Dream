"""
Shell tools — execute Python snippets for calculation and data processing.
"""

import sys
from io import StringIO

def register(mcp):

    @mcp.tool()
    def execute_python_logic(code: str) -> str:
        """
        Executes a block of Python code and returns the result/stdout.
        Use this for complex calculations, data manipulation, or testing logic.
        """
        # Redirect stdout to capture print() calls
        old_stdout = sys.stdout
        redirected_output = sys.stdout = StringIO()
        
        try:
            # We'll use a shared global dictionary for persistence within the session
            # but for now, we'll just execute it standalone.
            exec(code, globals())
            sys.stdout = old_stdout
            result = redirected_output.getvalue()
            
            if not result:
                return "Execution complete. No output generated."
            return f"### EXECUTION RESULT:\n{result}"
            
        except Exception as e:
            sys.stdout = old_stdout
            return f"Logic failure: {str(e)}"
        finally:
            sys.stdout = old_stdout

    @mcp.tool()
    def run_calculation(expression: str) -> str:
        """
        Evaluate a simple mathematical expression.
        Example: '50 * 1.2 / (15 + 2)'.
        """
        try:
            # eval is safer for just expressions, but still powerful
            result = eval(expression, {"__builtins__": {}}, {})
            return f"Calculation complete: {expression} = {result}"
        except Exception as e:
            return f"Calculation error: {str(e)}"
