import inspect
from typing import Dict, List, Callable, Any
from friday.tools import register_all_tools

class ToolManager:
    """
    Manages the collection and execution of Friday's toolset.
    """
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.tool_metadata: List[Dict[str, Any]] = []
        self._load_tools()

    def _load_tools(self):
        """
        Loads tools from friday.tools by mocking the MCP registration process.
        """
        class MockMCP:
            def __init__(self, manager):
                self.manager = manager
            
            def tool(self):
                def decorator(func):
                    # Store the function
                    self.manager.tools[func.__name__] = func
                    
                    # Generate metadata (OpenAI/Gemini style)
                    sig = inspect.signature(func)
                    props = {}
                    required = []
                    
                    type_map = {
                        str: "string",
                        int: "integer",
                        float: "number",
                        bool: "boolean",
                        dict: "object",
                        list: "array"
                    }
                    
                    for name, param in sig.parameters.items():
                        p_type = param.annotation if param.annotation != inspect.Parameter.empty else str
                        props[name] = {
                            "type": type_map.get(p_type, "string"),
                            "description": name # Ideally we'd parse docstrings for parameter descriptions
                        }
                        if param.default is inspect.Parameter.empty:
                            required.append(name)
                    
                    self.manager.tool_metadata.append({
                        "name": func.__name__,
                        "description": (func.__doc__ or "").strip().split("\n")[0],
                        "parameters": {
                            "type": "object",
                            "properties": props,
                            "required": required
                        }
                    })
                    return func
                return decorator

        mock_mcp = MockMCP(self)
        register_all_tools(mock_mcp)

    def get_tool(self, name: str) -> Callable:
        return self.tools.get(name)

    def get_all_tools(self) -> List[Callable]:
        return list(self.tools.values())

    def get_tool_metadata(self) -> List[Dict[str, Any]]:
        """Returns metadata for Gemini/OpenAI function calling."""
        return self.tool_metadata

    def get_ollama_tools(self) -> List[Dict[str, Any]]:
        """Returns tools in Ollama-compatible format."""
        # Ollama expects tools wrapped in a specific structure
        return [{"type": "function", "function": m} for m in self.tool_metadata]

tool_manager = ToolManager()
