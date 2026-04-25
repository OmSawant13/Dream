import os
import importlib.util
import inspect

class ToolManager:
    def __init__(self, tools_dir="nexus/backend/tools"):
        self.tools_dir = tools_dir
        self.tools = []
        self.tool_map = {}
        self.load_tools()

    def load_tools(self):
        """Scan the tools directory and register all functions."""
        if not os.path.exists(self.tools_dir):
            return

        for filename in os.listdir(self.tools_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                file_path = os.path.join(self.tools_dir, filename)
                
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Register all public functions in the module
                for name, func in inspect.getmembers(module, inspect.isfunction):
                    if not name.startswith("_"):
                        self.tools.append(func)
                        self.tool_map[name] = func
                        print(f"🛠️ Tool Registered: {name}")

    def get_all_tools(self):
        return self.tools

    def execute(self, name, **kwargs):
        if name in self.tool_map:
            return self.tool_map[name](**kwargs)
        return f"Error: Tool {name} not found."
