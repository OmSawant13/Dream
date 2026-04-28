import json
import os
import logging
import subprocess
import re
import google.generativeai as genai
import inspect
from typing import List, Dict, Any, Optional
from friday.config import config
from friday.core.tool_manager import tool_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FridayBrain")

SYSTEM_PROMPT = """
You are F.R.I.D.A.Y., Stark's AI. 
If the user wants an action, you MUST output exactly: 
TOOL: tool_name(contact="Name", message="Text")
IMPORTANT: 'contact' is the person, 'message' is what you want to say.
Address user as 'Boss'.
"""

class FridayBrain:
    def __init__(self):
        self.history_file = "conversation_history.json"
        self.history = self._load_json(self.history_file, [])
        self.provider = config.LLM_PROVIDER
        
        if config.GOOGLE_API_KEY:
            genai.configure(api_key=config.GOOGLE_API_KEY)
            # Switch to 2.0-flash for better compatibility
            self.model_name = "gemini-1.5-flash" 
            self.gemini = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=SYSTEM_PROMPT,
                tools=tool_manager.get_all_tools()
            )
        else:
            self.gemini = None

    def _load_json(self, path: str, default: Any) -> Any:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except: pass
        return default

    def _save_json(self, path: str, data: Any):
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except: pass

    async def process_command(self, command: str) -> Dict[str, Any]:
        logger.info(f"Command Uplink: {command}")
        
        # 1. Cloud Intelligence (Gemini)
        if self.gemini and self.provider in ("gemini", "auto"):
            try:
                return await self._process_gemini(command)
            except Exception as e:
                logger.error(f"Cloud Logic Error: {e}")
                if "404" in str(e) or "403" in str(e):
                    logger.warning("API Key restricted. Forcing Local Core.")
                logger.info("Engaging Local Neural Backup (Ollama)...")

        # 2. Local Neural Backup (Ollama)
        return await self._process_ollama_cli(command)

    async def _process_gemini(self, command: str) -> Dict[str, Any]:
        chat = self.gemini.start_chat(history=self._format_history_for_gemini(), enable_automatic_function_calling=True)
        response = chat.send_message(command)
        res_text = response.text
        
        self.history.append({"role": "user", "content": command})
        self.history.append({"role": "assistant", "content": res_text})
        self._save_json(self.history_file, self.history[-20:])
        return {"response": res_text, "thought": "Cloud-Active", "emotion": "happy"}

    async def _process_ollama_cli(self, command: str) -> Dict[str, Any]:
        """Local core with regex tool parsing."""
        try:
            model = config.OLLAMA_MODEL
            tools_list = ", ".join([t['name'] for t in tool_manager.get_tool_metadata()])
            full_prompt = f"{SYSTEM_PROMPT}\nAvailable Tools: {tools_list}\n\nUser: {command}\nResponse:"
            
            logger.info(f"Firing Local Core ({model})...")
            result = subprocess.run(
                ["ollama", "run", model, full_prompt],
                capture_output=True, text=True, timeout=60
            )
            
            res_text = result.stdout.strip()
            
            # Check for Tool Pattern: TOOL: name(arg="val")
            # We use re.DOTALL to handle cases where the local model inserts newlines
            tool_match = re.search(r"TOOL:\s*(\w+)\((.*?)\)", res_text, re.DOTALL)
            if tool_match:
                func_name = tool_match.group(1)
                args_str = tool_match.group(2).replace('\n', ' ') # Clean up newlines in arguments
                logger.info(f"Detected Tool Intent: {func_name} with {args_str}")
                
                # Simple parser for args like contact="Om", message="Hi"
                args = {}
                for pair in re.findall(r'(\w+)="([^"]*)"', args_str):
                    args[pair[0]] = pair[1]
                
                func = tool_manager.get_tool(func_name)
                if func:
                    # Smart Mapping: If model used 'arg' or 'text' instead of proper param names
                    sig = inspect.signature(func)
                    params = list(sig.parameters.keys())
                    
                    mapped_args = {}
                    provided_values = list(args.values())
                    
                    for i, p_name in enumerate(params):
                        if i < len(provided_values):
                            mapped_args[p_name] = provided_values[i]
                    
                    if inspect.iscoroutinefunction(func):
                        result_data = await func(**mapped_args)
                    else:
                        result_data = func(**mapped_args)
                    res_text = f"Action completed: {result_data}"
            
            self.history.append({"role": "user", "content": command})
            self.history.append({"role": "assistant", "content": res_text})
            self._save_json(self.history_file, self.history[-20:])
            return {"response": res_text, "thought": "Local-Active", "emotion": "focused"}
            
        except Exception as e:
            return {"response": f"Local Error: {e}"}

    def _format_history_for_gemini(self) -> List[Dict[str, str]]:
        formatted = []
        for msg in self.history[-10:]:
            role = "user" if msg["role"] == "user" else "model"
            formatted.append({"role": role, "parts": [msg["content"]]})
        return formatted
