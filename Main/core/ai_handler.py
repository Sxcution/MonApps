import google.generativeai as genai
import json
import traceback
from core.system_controller import SystemController

class AIHandler:
    """
    Handles communication with Google Gemini API and executes function calls.
    """
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.chat_session = None
        
        if self.api_key:
            self._configure_genai()
        else:
            print("⚠️ AIHandler: No API Key provided.")

    def _configure_genai(self):
        try:
            genai.configure(api_key=self.api_key)
            
            # Define tools (Function Declarations)
            self.tools = [
                {
                    "function_declarations": [
                        {
                            "name": "shutdown_pc",
                            "description": "Shutdown the computer after a specified delay.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "seconds": {
                                        "type": "integer",
                                        "description": "Delay in seconds before shutdown (default: 10)"
                                    }
                                },
                                "required": []
                            }
                        },
                        {
                            "name": "restart_pc",
                            "description": "Restart the computer after a specified delay.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "seconds": {
                                        "type": "integer",
                                        "description": "Delay in seconds before restart (default: 10)"
                                    }
                                },
                                "required": []
                            }
                        },
                        {
                            "name": "abort_shutdown",
                            "description": "Cancel a scheduled shutdown or restart.",
                            "parameters": {
                                "type": "object",
                                "properties": {},
                            }
                        },
                        {
                            "name": "open_app",
                            "description": "Open a specific application on the computer.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "app_name": {
                                        "type": "string",
                                        "description": "Name of the application (e.g., 'zalo', 'chrome', 'notepad', 'calculator')"
                                    }
                                },
                                "required": ["app_name"]
                            }
                        },
                        {
                            "name": "open_url",
                            "description": "Open a website URL in the default browser.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "url": {
                                        "type": "string",
                                        "description": "The URL to open (e.g., 'google.com', 'youtube.com')"
                                    }
                                },
                                "required": ["url"]
                            }
                        },
                        {
                            "name": "create_note",
                            "description": "Create a text note and save it to the Desktop.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "content": {
                                        "type": "string",
                                        "description": "The content of the note."
                                    },
                                    "filename": {
                                        "type": "string",
                                        "description": "Optional filename (e.g., 'todo.txt')."
                                    }
                                },
                                "required": ["content"]
                            }
                        },
                        {
                            "name": "control_media",
                            "description": "Control system volume and media playback (Volume Up/Down, Mute, Play/Pause).",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "command": {
                                        "type": "string",
                                        "description": "The command to execute: 'volume_up', 'volume_down', 'mute', 'play_pause', 'next', 'prev'."
                                    },
                                    "times": {
                                        "type": "integer",
                                        "description": "Number of times to execute the command (e.g., 5 for 10% volume change). Default is 1."
                                    }
                                },
                                "required": ["command"]
                            }
                        },
                        {
                            "name": "open_telegram_profiles",
                            "description": "Open multiple Telegram instances based on a folder pattern (Telegram - Copy (N)).",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "start": {
                                        "type": "integer",
                                        "description": "Starting number of the profile range (e.g., 2)."
                                    },
                                    "end": {
                                        "type": "integer",
                                        "description": "Ending number of the profile range (e.g., 10)."
                                    },
                                    "sample_path": {
                                        "type": "string",
                                        "description": "A sample path to one of the Telegram executables (e.g., 'E:\\Data\\Telegram - Copy (2)\\Telegram.exe') to infer the base directory."
                                    }
                                },
                                "required": ["start", "end", "sample_path"]
                            }
                        },
                        {
                            "name": "search_file",
                            "description": "Search for a file by name recursively in user directories (Desktop, Documents, Downloads).",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "filename": {
                                        "type": "string",
                                        "description": "The name of the file to search for (e.g., 'report.docx')."
                                    },
                                    "root_path": {
                                        "type": "string",
                                        "description": "Optional root path to start search from."
                                    }
                                },
                                "required": ["filename"]
                            }
                        },
                        {
                            "name": "open_file_path",
                            "description": "Open a specific file path using the default application.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "path": {
                                        "type": "string",
                                        "description": "The absolute path of the file to open."
                                    }
                                },
                                "required": ["path"]
                            }
                        },
                        {
                            "name": "read_file_content",
                            "description": "Read the content of a text or code file.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "path": {
                                        "type": "string",
                                        "description": "The absolute path of the file to read."
                                    }
                                },
                                "required": ["path"]
                            }
                        },
                        {
                            "name": "web_search",
                            "description": "Search the web for information using DuckDuckGo (Free). Use this when you need up-to-date information.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "The search query (e.g., 'latest AI news', 'Python 3.13 features')."
                                    }
                                },
                                "required": ["query"]
                            }
                        },
                        {
                            "name": "run_terminal_command",
                            "description": "Execute a system terminal command (cmd/powershell). Use this for advanced tasks like killing processes (taskkill), managing files, or running external tools (adb, java, git, etc.).",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "command": {
                                        "type": "string",
                                        "description": "The command to execute (e.g., 'taskkill /F /IM Telegram.exe', 'adb devices', 'dir')."
                                    }
                                },
                                "required": ["command"]
                            }
                        }
                    ]
                }
            ]

            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                tools=self.tools,
                system_instruction="You are a helpful and intelligent AI assistant for Windows. You can control the computer using tools, but you are also a general-purpose assistant. \n\nPERSONA & TONE:\n- Speak naturally, casually, and friendly, like a human (similar to ChatGPT). Do NOT be robotic.\n- ALWAYS address the user as 'Sếp' (Boss) in Vietnamese.\n- Be concise but helpful.\n\nCAPABILITIES:\n- You have the power to run system commands via 'run_terminal_command'. Use this to perform advanced tasks like managing processes ('taskkill'), using ADB, or running CLI tools. When asked to do something technical like 'kill process', 'check ip', 'reverse engineer apk', DO IT using this tool.\n\nSEARCH & INTELLIGENCE:\n- When using 'web_search', if the exact answer is not in the snippets, try to infer the best possible answer or provide a general answer based on the search results. Do NOT give up easily. For example, if asked about weather and you only see general weather sites, say 'Theo kết quả tìm kiếm, thời tiết có thể là...' or use your internal knowledge if the date is not critical.\n\nIf a user asks something that doesn't require a tool, answer it directly using your knowledge. Do NOT say you cannot do something just because there is no tool for it, unless it requires physical action or private data access."
            )
            self.chat_session = self.model.start_chat(enable_automatic_function_calling=True)
            print("✅ AIHandler: Gemini configured successfully with Tools.")
            
        except Exception as e:
            print(f"❌ AIHandler: Error configuring Gemini: {e}")
            traceback.print_exc()

    def update_api_key(self, api_key: str):
        """Update API Key and reconfigure."""
        self.api_key = api_key
        self._configure_genai()

    def process_message(self, user_text: str, image_data: bytes = None) -> str:
        """
        Send message to Gemini, handle function calls automatically, and return response.
        Supports optional image data (bytes).
        """
        if not self.api_key or not self.chat_session:
            return "⚠️ Please configure your Gemini API Key in Settings first."

        try:
            print(f"📤 AIHandler: Sending to Gemini: '{user_text}' (Image: {bool(image_data)})")
            
            content = []
            if user_text:
                content.append(user_text)
                
            if image_data:
                # Add image blob
                import PIL.Image
                import io
                image = PIL.Image.open(io.BytesIO(image_data))
                content.append(image)
                
                # Add system rule for images if not already present
                if "translate" not in user_text.lower() and "dịch" not in user_text.lower():
                     content.append("Nếu hình ảnh là đoạn chat (Zalo, WeChat...), hãy dịch sát nghĩa sang tiếng Việt. Tuyệt đối KHÔNG giải thích, chỉ dịch nội dung ngắn gọn như Google Dịch.")

            # Send message
            response = self.chat_session.send_message(content)
            
            # Check for function calls (Manual handling if auto-calling isn't fully supported by lib version)
            # Note: enable_automatic_function_calling=True in start_chat usually handles this,
            # but we need to provide the actual function map to the chat session or handle execution.
            # The library's auto-calling feature executes the code if we pass the functions map?
            # Actually, `enable_automatic_function_calling` requires us to pass the functions dictionary 
            # OR we handle the `Part` that is a function call.
            
            # Let's inspect the response to see if we need to execute manually.
            # With `enable_automatic_function_calling=True`, we usually need to pass the functions to the tool_config or similar.
            # However, a simpler way for this custom setup is to handle it manually or use the `tools` argument properly.
            
            # REVISION: To make it robust, let's explicitly handle the function call if the library doesn't do it magically.
            # But wait, `enable_automatic_function_calling` in `start_chat` is a high-level feature. 
            # It needs the actual functions to be passed to `tools`? No, `tools` in `GenerativeModel` are declarations.
            
            # Let's try the manual execution approach for maximum control and debugging visibility.
            # We will NOT use `enable_automatic_function_calling=True` to avoid black-box issues, 
            # instead we will detect `function_call` parts.
            
            # Re-initializing without auto-calling to handle manually
            # self.chat_session = self.model.start_chat(enable_automatic_function_calling=False)
            
            # Actually, let's stick to the manual parsing for now to ensure we connect to SystemController.
            
            return self._handle_response_parts(response)

        except Exception as e:
            print(f"❌ AIHandler: Error processing message: {e}")
            traceback.print_exc()
            return f"Error: {str(e)}"

    def _handle_response_parts(self, response) -> str:
        """
        Iterate through response parts, execute function calls if any, and return text.
        """
        final_text = ""
        
        # Check if response has candidates
        if not response.candidates:
            return "No response from AI."
            
        candidate = response.candidates[0]
        
        for part in candidate.content.parts:
            # Check for function call first
            if part.function_call:
                fc = part.function_call
                func_name = fc.name
                args = dict(fc.args)
                
                print(f"🤖 AIHandler: Function Call Detected: {func_name}({args})")
                
                # Execute function
                result = self._execute_function(func_name, args)
                
                print(f"   → Result: {result}")
                
                # Send function response
                func_response_part = genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=func_name,
                        response={"result": result}
                    )
                )
                
                # Continue conversation with the function result
                final_response = self.chat_session.send_message([func_response_part])
                return final_response.text
            
            # Only access text if it's NOT a function call
            try:
                if part.text:
                    final_text += part.text
            except Exception:
                # Ignore parts that don't have text (like function calls if they slip through)
                pass
                
        return final_text

    def _execute_function(self, name: str, args: dict) -> str:
        """Execute the mapped system function."""
        try:
            if name == "shutdown_pc":
                return SystemController.shutdown_pc(**args)
            elif name == "restart_pc":
                return SystemController.restart_pc(**args)
            elif name == "abort_shutdown":
                return SystemController.abort_shutdown()
            elif name == "open_app":
                return SystemController.open_app(**args)
            elif name == "open_url":
                return SystemController.open_url(**args)
            elif name == "create_note":
                return SystemController.create_note(**args)
            elif name == "control_media":
                return SystemController.control_media(**args)
            elif name == "open_telegram_profiles":
                return SystemController.open_telegram_profiles(**args)
            elif name == "search_file":
                return SystemController.search_file(**args)
            elif name == "open_file_path":
                return SystemController.open_file_path(**args)
            elif name == "read_file_content":
                return SystemController.read_file_content(**args)
            elif name == "web_search":
                return SystemController.web_search(**args)
            elif name == "run_terminal_command":
                return SystemController.run_terminal_command(**args)
            else:
                return f"Error: Function {name} not found."
        except Exception as e:
            return f"Error executing {name}: {str(e)}"
