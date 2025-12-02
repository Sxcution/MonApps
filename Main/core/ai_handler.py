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
                        }
                    ]
                }
            ]
            
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                tools=self.tools
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

    def process_message(self, user_text: str) -> str:
        """
        Send message to Gemini, handle function calls automatically, and return response.
        """
        if not self.api_key or not self.chat_session:
            return "⚠️ Please configure your Gemini API Key in Settings first."

        try:
            print(f"📤 AIHandler: Sending to Gemini: '{user_text}'")
            
            # Send message
            response = self.chat_session.send_message(user_text)
            
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
            if part.function_call:
                fc = part.function_call
                func_name = fc.name
                args = dict(fc.args)
                
                print(f"🤖 AIHandler: Function Call Detected: {func_name}({args})")
                
                # Execute function
                result = self._execute_function(func_name, args)
                
                # Send result back to Gemini
                # We need to send the function response back to the model to get the final natural language answer.
                # This is the standard flow.
                
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
            
            if part.text:
                final_text += part.text
                
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
            else:
                return f"Error: Function {name} not found."
        except Exception as e:
            return f"Error executing {name}: {str(e)}"
