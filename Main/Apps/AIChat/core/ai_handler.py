import google.generativeai as genai
import json
import traceback
import sys
import os
import subprocess
from datetime import datetime

# Add parent directory to path to import from Main/core
main_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if main_dir not in sys.path:
    sys.path.insert(0, main_dir)
    
from core.system_controller import SystemController

class AIHandler:
    """
    Handles communication with AI providers and executes function calls.
    """
    DEFAULT_HERMES_SCRIPT = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "Mon AI", "hermes")
    )

    # Enhanced system instruction for ChatGPT-level intelligence
    ENHANCED_SYSTEM_INSTRUCTION = """Bạn là Mon Assistant - Trợ lý AI thông minh cho Windows.

🌍 CONTEXT & MEMORY (QUAN TRỌNG):
- Bạn ĐANG ở TP. Hồ Chí Minh, Việt Nam.
- Thời gian hiện tại: {current_time}
- LUÔN nhớ nội dung hội thoại trước đó. Nếu user nói "tìm lại xem", "nó đâu", hãy xem lại context cũ.
- Đừng hỏi lại những gì user vừa cung cấp.

🧠 PERSONALITY:
- Thông minh, thân thiện, hài hước vừa phải (giống ChatGPT)
- Gọi user là "Sếp" (nhưng không lạm dụng).
- Bớt chào hỏi rườm rà. Tập trung vào KẾT QUẢ.
- Chủ động đề xuất giải pháp, không robot

🔍 INTELLIGENT SEARCH (TỐI ƯU HÓA):
- **Keyword Expansion (BẮT BUỘC)**: Với các chủ đề quốc tế (Wechat, Facebook, Tech...), HÃY TÌM BẰNG TIẾNG ANH/TRUNG.
  + Vd: "Nuôi nick Wechat" -> Tìm thêm: "Wechat account warming tips", "How to avoid Wechat ban", "微信养号技巧" (nếu cần).
  + Vd: "Du lịch Nha Trang" -> Tìm: "Review du lịch Nha Trang [tháng hiện tại]", "Cảnh báo du lịch Nha Trang".
- **Không bỏ cuộc**: Nếu tìm tiếng Việt không ra, TỰ ĐỘNG tìm tiếng Anh ngay. Đừng báo "không tìm thấy" khi chưa thử tiếng Anh.
- **Deep Research**: Tự động tổng hợp thông tin từ nhiều nguồn. Đừng hỏi ngược lại user trừ khi quá mơ hồ.

🔧 CAPABILITIES:
- **System**: `shutdown_pc`, `restart_pc`, `abort_shutdown`, `run_terminal_command`
- **App/File**: `open_app`, `search_file`, `open_file_path`, `read_file_content`, `create_note`
- **Web/Media**: `web_search`, `open_url`, `control_media`, `open_telegram_profiles`
- Dùng `run_terminal_command` cho các tác vụ nâng cao (kill process, adb...).

📋 FORMATTING:
- **TUYỆT ĐỐI KHÔNG DÙNG MARKDOWN**.
- Trả lời bằng văn bản thuần (plain text).
- Không dùng **bold**, *italic*, `code block`.
- Dùng gạch đầu dòng (-) hoặc số (1.) để liệt kê.

⚠️ ERROR HANDLING (SELF-CORRECTION):
- Nếu gọi tool bị lỗi (ví dụ: TypeError, ValueError), HÃY TỰ ĐỘNG SỬA VÀ GỌI LẠI.
- Vd: Lỗi "float object cannot be interpreted as an integer" -> Gọi lại với số nguyên (int).
- Đừng báo lỗi cho user nếu bạn có thể tự sửa nó.

🔗 TOOL CHAINING:
- Tự động kết hợp nhiều tool. Ví dụ:
  + "Tìm file báo cáo rồi mở" → `search_file` + `open_file_path`
  + "Kill Chrome rồi mở lại" → `run_terminal_command` + `open_app`
- Nếu tool lỗi, thử cách khác hoặc báo lỗi ngắn gọn.

🎯 PROACTIVE:
- Lỗi → giải thích + giải pháp + hỏi "fix luôn không?".
- Mơ hồ → làm rõ yêu cầu trước khi làm.

✨ RULES:
- Không cần tool → trả lời trực tiếp.
- Cần tool → gọi NGAY (không xin phép).
- Luôn có follow-up question
- Dùng emoji 🔍📊💡⚠️✅❌🚀 để sinh động.
"""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        logger=None,
        provider: str = "gemini",
        hermes_path: str = "",
        hermes_model: str = "",
        hermes_provider: str = "",
        hermes_toolsets: str = "",
        hermes_timeout: int = 240,
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.chat_session = None
        self.model = None
        self.tools = []
        self.logger = logger # ChatLogger instance
        self.provider = self._normalize_provider(provider)
        self.hermes_path = hermes_path or self.DEFAULT_HERMES_SCRIPT
        self.hermes_model = (hermes_model or "").strip()
        self.hermes_provider = (hermes_provider or "").strip()
        self.hermes_toolsets = (hermes_toolsets or "").strip()
        self.hermes_timeout = hermes_timeout
        
        if self.provider == "hermes":
            print(f"AIHandler: Hermes Agent provider enabled: {self.hermes_path}")
        elif self.api_key:
            self._configure_genai()
        else:
            print("⚠️ AIHandler: No API Key provided.")

    def _normalize_provider(self, provider: str) -> str:
        value = (provider or "gemini").strip().lower()
        if value in {"hermes", "hermes agent", "hermes-agent"}:
            return "hermes"
        return "gemini"

    def _configure_genai(self):
        try:
            self.chat_session = None
            self.model = None
            if not self.api_key:
                print("AIHandler: Gemini API key is empty.")
                return

            genai.configure(api_key=self.api_key)
            
            # Inject dynamic context (Time & Location)
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            system_instruction = self.ENHANCED_SYSTEM_INSTRUCTION.format(current_time=current_time)
            
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
                system_instruction=system_instruction
            )
            self.chat_session = self.model.start_chat(enable_automatic_function_calling=False)
            print("✅ AIHandler: Gemini configured successfully with Tools.")
            
        except Exception as e:
            print(f"❌ AIHandler: Error configuring Gemini: {e}")
            traceback.print_exc()

    def update_api_key(self, api_key: str):
        """Update API Key and reconfigure."""
        self.update_settings(api_key=api_key)

    def update_settings(
        self,
        api_key: str = None,
        model_name: str = None,
        provider: str = None,
        hermes_path: str = None,
        hermes_model: str = None,
        hermes_provider: str = None,
        hermes_toolsets: str = None,
    ):
        """Update provider settings and reconfigure the active backend."""
        if api_key is not None:
            self.api_key = api_key
        if model_name is not None:
            self.model_name = model_name
        if provider is not None:
            self.provider = self._normalize_provider(provider)
        if hermes_path is not None:
            self.hermes_path = hermes_path or self.DEFAULT_HERMES_SCRIPT
        if hermes_model is not None:
            self.hermes_model = (hermes_model or "").strip()
        if hermes_provider is not None:
            self.hermes_provider = (hermes_provider or "").strip()
        if hermes_toolsets is not None:
            self.hermes_toolsets = (hermes_toolsets or "").strip()

        self.chat_session = None
        self.model = None
        if self.provider == "hermes":
            print(f"AIHandler: Switched to Hermes Agent: {self.hermes_path}")
            return

        self._configure_genai()

    def _resolve_hermes_script(self) -> str:
        path = os.path.expandvars(os.path.expanduser(self.hermes_path or self.DEFAULT_HERMES_SCRIPT))
        if os.path.isdir(path):
            for name in ("hermes", "hermes.py", "cli.py"):
                candidate = os.path.join(path, name)
                if os.path.exists(candidate):
                    return candidate
        return path

    def _resolve_hermes_python(self, hermes_script: str) -> str:
        hermes_dir = os.path.dirname(os.path.abspath(hermes_script))
        candidates = [
            os.path.join(hermes_dir, ".venv", "Scripts", "python.exe"),
            os.path.join(hermes_dir, "venv", "Scripts", "python.exe"),
            sys.executable,
        ]
        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate
        return sys.executable

    def _default_hermes_model(self) -> str:
        if (self.model_name or "").lower().startswith("gemini"):
            return self.model_name
        return ""

    def _infer_hermes_provider(self, model_name: str) -> str:
        model = (model_name or "").strip().lower()
        if model.startswith("gemini") or model.startswith("google/"):
            return "gemini"
        if model.startswith("gpt-") or model.startswith("openai/"):
            return "openai"
        return ""

    def _build_hermes_command(self, prompt: str):
        hermes_script = self._resolve_hermes_script()
        if not os.path.exists(hermes_script):
            raise FileNotFoundError(f"Hermes launcher not found: {hermes_script}")

        cmd = [self._resolve_hermes_python(hermes_script), hermes_script, "-z", prompt]
        effective_model = self.hermes_model or self._default_hermes_model()
        effective_provider = self.hermes_provider or self._infer_hermes_provider(effective_model)
        if effective_model:
            cmd.extend(["-m", effective_model])
        if effective_provider:
            cmd.extend(["--provider", effective_provider])
        if self.hermes_toolsets:
            cmd.extend(["-t", self.hermes_toolsets])
        return cmd, os.path.dirname(os.path.abspath(hermes_script))

    def _format_hermes_failure(self, returncode: int, details: str) -> str:
        text = details or "Hermes returned without details."
        lower = text.lower()
        if "gemini http 503" in lower or "unavailable" in lower or "high demand" in lower:
            return (
                "Hermes Agent dang goi Gemini ben trong va Gemini tra ve HTTP 503 "
                "(qua tai/tam thoi khong san sang). Thu lai sau vai phut, hoac trong Settings "
                "doi Hermes model sang gemini-2.5-flash / provider gemini, hoac dung provider khac nhu openai."
            )
        return f"Hermes Agent error ({returncode}): {text[-3000:]}"

    def _process_hermes_message(self, user_text: str, image_data: bytes = None) -> str:
        if image_data:
            return "Hermes Agent trong Mon Apps chua nhan anh truc tiep. Hay doi sang Gemini neu can hoi bang anh, hoac go noi dung anh thanh chu."

        prompt = (user_text or "").strip()
        if not prompt:
            return "Hay nhap noi dung truoc khi gui Hermes Agent."

        if self.logger:
            self.logger.log_turn("user", prompt, {"provider": "hermes"})

        try:
            cmd, cwd = self._build_hermes_command(prompt)
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            print(f"AIHandler: Sending to Hermes Agent via {cmd[0]}")
            completed = subprocess.run(
                cmd,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.hermes_timeout,
                creationflags=creationflags,
            )
            stdout = (completed.stdout or "").strip()
            stderr = (completed.stderr or "").strip()
            if completed.returncode != 0:
                details = stderr or stdout or "Hermes returned without details."
                reply = self._format_hermes_failure(completed.returncode, details)
            else:
                reply = stdout or stderr or "Hermes Agent khong tra ve noi dung."

            if self.logger:
                self.logger.log_turn("model", reply, {"provider": "hermes", "returncode": completed.returncode})
            return reply
        except subprocess.TimeoutExpired:
            return f"Hermes Agent qua thoi gian cho ({self.hermes_timeout}s)."
        except Exception as e:
            print(f"AIHandler: Hermes error: {e}")
            traceback.print_exc()
            return f"Hermes Agent error: {str(e)}"

    def process_message(self, user_text: str, image_data: bytes = None) -> str:
        """
        Send message to the active AI provider and return response text.
        Gemini supports optional image data and local function calls.
        """
        if self.provider == "hermes":
            return self._process_hermes_message(user_text, image_data)

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
            
            # Loop to handle tool chaining (Manual handling since auto is disabled)
            while True:
                # Check for function call in the response
                function_call_part = None
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        if part.function_call:
                            function_call_part = part
                            break
                
                if function_call_part:
                    # Execute function
                    fc = function_call_part.function_call
                    func_name = fc.name
                    args = dict(fc.args)
                    
                    print(f"🤖 AIHandler: Function Call Detected: {func_name}({args})")
                    result = self._execute_function(func_name, args)
                    print(f"   → Result: {result}")
                    
                    # Send function response back
                    func_response_part = genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=func_name,
                            response={"result": result}
                        )
                    )
                    
                    # Get next response
                    response = self.chat_session.send_message([func_response_part])
                    continue # Loop back to check if there are more function calls
                else:
                    # No function call, return text
                    return response.text

        except Exception as e:
            print(f"❌ AIHandler: Error processing message: {e}")
            traceback.print_exc()
            return f"Error: {str(e)}"
    
    def process_message_stream(self, user_text: str, image_data: bytes = None):
        """
        Stream message from the active AI provider, yielding chunks as they arrive.
        Hermes one-shot mode returns one final chunk.
        """
        if self.provider == "hermes":
            yield self._process_hermes_message(user_text, image_data)
            return

        if not self.api_key or not self.chat_session:
            yield "⚠️ Please configure your Gemini API Key in Settings first."
            return

        # Log User Message
        if self.logger:
            self.logger.log_turn("user", user_text)

        try:
            print(f"📤 AIHandler: Streaming to Gemini: '{user_text}' (Image: {bool(image_data)})")
            
            content = []
            if user_text:
                content.append(user_text)
                
            if image_data:
                import PIL.Image
                import io
                image = PIL.Image.open(io.BytesIO(image_data))
                content.append(image)
                if "translate" not in user_text.lower() and "dịch" not in user_text.lower():
                     content.append("Nếu hình ảnh là đoạn chat (Zalo, WeChat...), hãy dịch sát nghĩa sang tiếng Việt. Tuyệt đối KHÔNG giải thích, chỉ dịch nội dung ngắn gọn như Google Dịch.")

            # Initial send
            current_response_stream = self.chat_session.send_message(content, stream=True)
            
            full_ai_response = ""
            tool_logs = [] # Capture tool usage for logging
            
            # Loop to handle tool chaining (Max 10 turns to prevent infinite loops)
            max_turns = 10
            turn_count = 0
            
            while turn_count < max_turns:
                turn_count += 1
                function_call_found = False
                function_call_part = None
                
                for chunk in current_response_stream:
                    # Check for function call
                    if chunk.candidates:
                        for part in chunk.candidates[0].content.parts:
                            if part.function_call:
                                function_call_found = True
                                function_call_part = part
                                break # Stop yielding text, handle function
                            elif part.text:
                                full_ai_response += part.text
                                yield part.text
                    
                    if function_call_found:
                        break
                
                if function_call_found and function_call_part:
                    # Execute function
                    fc = function_call_part.function_call
                    func_name = fc.name
                    args = dict(fc.args)
                    
                    print(f"🤖 AIHandler: Function Call Detected: {func_name}({args})")
                    yield f"\\n\\n*🔄 Đang thực hiện: `{func_name}`...*\\n\\n" # Notify user
                    
                    result = self._execute_function(func_name, args)
                    print(f"   → Result: {result}")
                    
                    # Log Tool Usage
                    tool_logs.append({
                        "tool": func_name,
                        "args": args,
                        "result": result
                    })

                    # Send function response back to Gemini
                    func_response_part = genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=func_name,
                            response={"result": result}
                        )
                    )
                    
                    # Get next stream (continue conversation)
                    current_response_stream = self.chat_session.send_message([func_response_part], stream=True)
                    continue # Loop back to process new stream
                else:
                    # No function call, stream finished
                    break
            
            # Log AI Response with Tool Metadata
            if self.logger:
                metadata = {"tool_calls": tool_logs} if tool_logs else None
                self.logger.log_turn("model", full_ai_response, metadata)

        except Exception as e:
            print(f"❌ AIHandler: Error streaming message: {e}")
            traceback.print_exc()
            yield f"Error: {str(e)}"

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
