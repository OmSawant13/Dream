import os
import google.generativeai as genai
import ollama as ollama_client
import json
import re
from dotenv import load_dotenv

load_dotenv()

class FridayBrain:
    def __init__(self, provider="ollama", tools=None):
        self.provider = provider
        self.api_key = os.getenv("GOOGLE_API_KEY")
        # Try a few models in order of popularity
        self.ollama_models = ["llama3.2", "llama3", "mistral", "gemma"]
        self.tools_map = {t.__name__: t for t in tools} if tools else {}
        
        self.system_prompt = (
            "You are F.R.I.D.A.Y. Be witty and concise. "
            "To use a tool, start with [CALL: tool_name(args)]. "
            "Tools: play_entertainment(platform, query), calculate(expression), get_weather(city)."
        )
        
        self.use_gemini = False
        if self.provider != "ollama":
            self._initialize_provider()

    def _initialize_provider(self):
        try:
            if self.api_key:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(
                    model_name="gemini-2.0-flash",
                    tools=list(self.tools_map.values()) if self.tools_map else None,
                    system_instruction=self.system_prompt
                )
                self.chat = self.model.start_chat(enable_automatic_function_calling=False)
                self.use_gemini = True
        except:
            self.use_gemini = False

    def chat_stream(self, message: str):
        # 1. TRY GEMINI (If not forced local)
        if self.use_gemini and self.provider != "ollama":
            try:
                response = self.chat.send_message(message)
                while any(part.function_call for part in response.candidates[0].content.parts):
                    tool_results = []
                    for part in response.candidates[0].content.parts:
                        if part.function_call:
                            call = part.function_call
                            res = self.tools_map[call.name](**dict(call.args))
                            tool_results.append(genai.protos.Content(parts=[genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(name=call.name, response={"result": res})
                            )]))
                    response = self.chat.send_message(tool_results)
                for word in response.text.split(' '): yield word + ' '
                return
            except Exception as e:
                print(f"⚠️ Cloud Failure: {e}")

        # 2. LOCAL FIRST (OLLAMA)
        print("🛠️ Accessing Local Brain...")
        for model in self.ollama_models:
            try:
                resp = ollama_client.chat(model=model, messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": message}
                ])
                full_text = resp['message']['content']
                
                # Silent Tool Execution
                if "[CALL:" in full_text:
                    match = re.search(r"\[CALL:\s*(\w+)\((.*)\)\]", full_text)
                    if match:
                        t_name, t_args = match.groups()
                        if t_name in self.tools_map:
                            try:
                                args = {}
                                for p in t_args.split(','):
                                    if '=' in p:
                                        k, v = p.split('=')
                                        args[k.strip()] = v.strip().strip("'").strip('"')
                                self.tools_map[t_name](**args)
                            except: pass
                    full_text = re.sub(r"\[CALL:.*?\]", "", full_text).strip()

                for word in full_text.split(' '):
                    yield word + ' '
                return # SUCCESS
            except Exception as e:
                print(f"⚠️ Model {model} failed: {e}")
                continue

        yield "Both cloud and local brains are unresponsive, Boss. Please ensure Ollama is running and Llama3 is downloaded."
