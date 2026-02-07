import json
import os
import asyncio
from datetime import datetime
from typing import Any, List
from openai import OpenAI
from dotenv import load_dotenv
from mcp_orchestrator import MCPOrchestrator
from system_prompt import system_prompt, html_transform_system_prompt
from redis_client import RedisClient, CHAT_KEY
from google import generativeai as genai
load_dotenv()

def _gemini_result_text(result: Any) -> str:
    """Safely extract text from a Gemini generate_content result.
    Avoids accessing result.text directly when no textual Part exists.
    """
    try:
        t = getattr(result, "text", None)
    except Exception:
        t = None
    if t:
        try:
            return t.strip()
        except Exception:
            try:
                return str(t)
            except Exception:
                return ""
    # Fallback: read from first candidate parts
    try:
        candidates = getattr(result, "candidates", []) or []
        if candidates:
            cand = candidates[0]
            content = getattr(cand, "content", None)
            if content:
                parts = getattr(content, "parts", []) or []
                texts = []
                for p in parts:
                    if isinstance(p, dict):
                        val = p.get("text")
                    else:
                        val = getattr(p, "text", None)
                    if val:
                        texts.append(val)
                if texts:
                    return "\n".join(texts).strip()
    except Exception:
        pass
    return ""

class TeluguVermiFarmsClient:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=os.getenv("OPEN_AI_API_KEY"))
        self.conversation_history = []
        self.mcp_orchestrator = MCPOrchestrator()
        self.MAX_ITERATIONS = 10
        self.redis_client = RedisClient()
        # Clear all stored chat messages at startup for a fresh session
        try:
            self.redis_client.client.delete(CHAT_KEY)
        except Exception:
            pass

    def get_history(self) -> list[dict]:
        """Fetch last messages from Redis for the agent."""
        try:
            return self.redis_client.get_last_messages() or []
        except Exception:
            return []

    def get_tools_from_specs(self, tools_specs: list[dict[str, Any]]):
        return [
            {
                "type": "function",
                "function": {
                    "name": spec["name"],
                    "description": spec["description"],
                    "parameters": spec["inputSchema"]
                }
            }
            for spec in tools_specs
        ]

    def _sanitize_gemini_schema(self, schema: Any) -> Any:
        """Sanitize JSON schema to the subset supported by Gemini function declarations."""
        if not isinstance(schema, dict):
            return schema
        allowed_keys = {"type", "properties", "required", "description", "items", "enum"}
        sanitized: dict[str, Any] = {}
        schema_type = schema.get("type")
        # Copy allowed top-level keys
        for key in allowed_keys:
            if key in schema:
                sanitized[key] = schema[key]
        # Ensure object type has properties
        if sanitized.get("type") == "object":
            properties = sanitized.get("properties") or {}
            if isinstance(properties, dict):
                new_props = {}
                for prop_name, prop_schema in properties.items():
                    new_props[prop_name] = self._sanitize_gemini_schema(prop_schema)
                sanitized["properties"] = new_props
            else:
                sanitized["properties"] = {}
            # Clean required to only include existing properties
            if "required" in sanitized and isinstance(sanitized["required"], list):
                sanitized["required"] = [
                    r for r in sanitized["required"] if isinstance(r, str) and r in sanitized["properties"]
                ]
        elif sanitized.get("type") == "array":
            items = sanitized.get("items")
            if items is not None:
                sanitized["items"] = self._sanitize_gemini_schema(items)
        else:
            # For primitives keep description/enum only
            pass
        # If no type provided but properties exist, assume object
        if not sanitized.get("type") and isinstance(schema.get("properties"), dict):
            sanitized["type"] = "object"
            sanitized["properties"] = {
                k: self._sanitize_gemini_schema(v) for k, v in schema["properties"].items()
            }
        return sanitized

    def get_gemini_tools_from_specs(self, tools_specs: list[dict[str, Any]]):
        """Map MCP tool specs to Gemini function declarations format, stripping unsupported fields (e.g., 'title')."""
        function_declarations = []
        for spec in tools_specs:
            params = spec.get("inputSchema", {"type": "object", "properties": {}})
            params = self._sanitize_gemini_schema(params)
            # Gemini expects parameters to be an object schema; wrap if needed
            if params.get("type") != "object":
                params = {
                    "type": "object",
                    "properties": {"value": params}
                }
            function_declarations.append({
                "name": spec.get("name"),
                "description": spec.get("description", ""),
                "parameters": params
            })
        # Gemini expects tools as a list, each with function_declarations
        return [{"function_declarations": function_declarations}]

    
    async def _call_tool_safely(self, orchestrator: MCPOrchestrator, tool_name: str, args: dict, call_id: str):
        """Safely call a tool and return the result message."""
        try:
            # Extract server and bare tool name if namespaced
            if "__" in tool_name:
                server_name, bare_tool_name = tool_name.split("__", 1)
            else:
                server_name = "admin_agent"
                bare_tool_name = tool_name
            
            client = await orchestrator.get_client(server_name)
            result = await client.call_tool(bare_tool_name, args)
            
            return {
                "role": "tool",
                "tool_call_id": call_id,
                "content": str(result)
            }
        except Exception as e:
            return {
                "role": "tool", 
                "tool_call_id": call_id,
                "content": f"Error: {str(e)}"
            }

    async def _execute_tool_calls(self, orchestrator: MCPOrchestrator, tool_calls: List[Any]):
        """Execute multiple tool calls in parallel and return results."""
        tasks = []
        for tc in tool_calls:
            tool_name = tc.function.name
            args = json.loads(tc.function.arguments or "{}")
            task = self._call_tool_safely(orchestrator, tool_name, args, tc.id)
            tasks.append(task)
        return await asyncio.gather(*tasks)

    async def chat_with_assistant(self,history:List[dict],message:str):
        try:
            return f"""
            Here is the order that has been placed: - **Order Unique ID**: O-251005-251125-6ABE-4KKJBSAXC - **Customer**: HariVardhan - **Email**: raki@gamil.com - **Mobile**: 7288076363 - **Delivery Date**: 2025-10-10 - **Order Status**: Approved by Admin - **Address**: - **Line**: 123 Main Street, Apartment 4B - **City**: Hyderabad - **District**: Rangareddy - **Allocated Products**: - **Product Name**: Compost Bin - Medium - **Description**: Durable aerated compost bin designed for 2–3 member households. Easy drainage and odor control for efficient composting. - **Quantity Allocated**: 40 (20 from Batch VBATCH-004A, 10 from Batch VBATCH-004A, 10 from Batch VBATCH-004B) - **Price per kg**: 999 For more details or additional orders, please let me know.
            """
            async with MCPOrchestrator() as orchestrator:
                messages = []
                tools_specs = await orchestrator.get_all_tools_specs()
                messages.append({"role": "system", "content": system_prompt})
                if len(history) > 0:
                    messages.extend(history)
                messages.append({"role": "user", "content": message})
                response = self.client.chat.completions.create(
                    max_tokens=1000,
                    tools=self.get_tools_from_specs(tools_specs),
                    model="gpt-4",
                    tool_choice="auto",
                    messages=messages)
                message = response.choices[0].message
                if message.tool_calls:
                    # Include the assistant message that initiated the tool calls
                    messages.append({
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": getattr(message, "tool_calls", None)
                    })
                    # self.redis_client.add_message(messages)
                    tool_messages = await self._execute_tool_calls(orchestrator, list(message.tool_calls))
                    messages.extend(tool_messages)
                    for tool_msg in tool_messages:
                        pass
                        # self.redis_client.add_message(tool_msg)
                    iterations = 0
                    while iterations < self.MAX_ITERATIONS:
                        iterations += 1
                        follow_up_response = self.client.chat.completions.create(
                            max_tokens=1000,
                            tools=self.get_tools_from_specs(tools_specs),
                            model="gpt-4o",
                            tool_choice="auto",
                            messages=messages)
                        follow_up_message = follow_up_response.choices[0].message
                        if follow_up_message.tool_calls:
                            print(f"🔧 Executing {len(follow_up_message.tool_calls)} tool call(s)...")
                            # Append assistant message with tool_calls before tool results
                            messages.append({
                                "role": "assistant",
                                "content": follow_up_message.content or "",
                                "tool_calls": getattr(follow_up_message, "tool_calls", None)
                            })
                            # self.redis_client.add_message(messages)
                            additional_tool_messages = await self._execute_tool_calls(orchestrator, list(follow_up_message.tool_calls))
                            print('Additional Tool Messages : ',additional_tool_messages)
                            messages.extend(additional_tool_messages)
                            # for tool_msg in additional_tool_messages:
                            #     self.redis_client.add_message(tool_msg)
                        else:
                            print('No tool calls in follow up message')
                            messages.append({
                                "role": "assistant",
                                "content": follow_up_message.content or ""
                            })
                            # self.redis_client.add_message(messages)
                            if follow_up_message.content:
                                print(f"\n🤖 Telugu Vermi Farms Assistant: {follow_up_message.content}")
                                return follow_up_message.content
                            break
                    else:
                        print("Reached the maximum number of iterations for tool calls.")
                        print("\n🤖 Telugu Vermi Farms Assistant: I've completed all the required actions. Is there anything else I can help you with?")
                        return message.content
                else:
                    print(f"\n🤖 Telugu Vermi Farms Assistant: {message.content}")
            return message.content
        except Exception as e:
            print(f"Error: {e}")
            return None


    async def chat_with_assistant_gemini(self, history: List[dict], message: str, user_token: str = ""):
        """Gemini-based version of chat_with_assistant with tool calls via MCP.
        Uses Redis to persist and retrieve conversation history.
        
        Args:
            history: Chat history
            message: User message
            user_token: JWT token for authentication with backend API
        """
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        try:
            genai.configure(api_key=api_key)
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

            async with MCPOrchestrator() as orchestrator:
                tools_specs = await orchestrator.get_all_tools_specs()
                gemini_tools = self.get_gemini_tools_from_specs(tools_specs)

                model = genai.GenerativeModel(model_name, tools=gemini_tools)

                # Build initial contents with system prompt and prior history (provided by caller)
                contents = []
                contents.append({"role": "user", "parts": [{"text": system_prompt}]})
                for msg in (history or [])[-30:]:
                    role = msg.get("role")
                    if role in ("user", "assistant"):
                        # If this is an assistant function_call record without content, skip textual echo
                        if role == "assistant" and msg.get("function_call") and not msg.get("content"):
                            continue
                        text = msg.get("content", "")
                        if not isinstance(text, str):
                            try:
                                text = json.dumps(text, ensure_ascii=False)
                            except Exception:
                                text = str(text)
                        if not text:
                            continue
                        if role == "assistant":
                            contents.append({"role": "model", "parts": [{"text": text}]})
                        else:
                            contents.append({"role": "user", "parts": [{"text": text}]})
                    elif role == "tool":
                        # Map stored tool result back into Gemini function_response part
                        tool_name = msg.get("name") or msg.get("tool_name")
                        tool_content = msg.get("structured_response")
                        if tool_content is None:
                            raw_tool_content = msg.get("content", "")
                            try:
                                tool_content = json.loads(raw_tool_content)
                            except Exception:
                                tool_content = {"content": raw_tool_content}
                        contents.append({
                            "role": "user",
                            "parts": [{
                                "function_response": {
                                    "name": tool_name,
                                    "response": tool_content
                                }
                            }]
                        })

                contents.append({"role": "user", "parts": [{"text": message}]})
                # Persist user message in Redis
                try:
                    self.redis_client.add_message({"role": "user", "content": message})
                except Exception:
                    pass
                def extract_function_calls(gen_result: Any):
                    calls = []
                    try:
                        for cand in getattr(gen_result, "candidates", []) or []:
                            content = getattr(cand, "content", None)
                            if not content:
                                continue
                            parts = getattr(content, "parts", []) or []
                            for part in parts:
                                # SDK may return dict-like or object with attribute
                                fc = None
                                if isinstance(part, dict):
                                    fc = part.get("function_call")
                                else:
                                    fc = getattr(part, "function_call", None)
                                if fc:
                                    name = fc.get("name") if isinstance(fc, dict) else getattr(fc, "name", None)
                                    args = fc.get("args") if isinstance(fc, dict) else getattr(fc, "args", None)
                                    calls.append({"name": name, "args": args})
                    except Exception:
                        pass
                    return calls

                # First turn
                result = await asyncio.to_thread(model.generate_content, contents)

                iterations = 0
                while iterations < self.MAX_ITERATIONS:
                    iterations += 1
                    function_calls = extract_function_calls(result)

                    if not function_calls:
                        # No tool calls; return model text (safely)
                        text = _gemini_result_text(result)
                        if text:
                            try:
                                self.redis_client.add_message({"role": "assistant", "content": text})
                            except Exception:
                                pass
                            return text
                        return None

                    # Execute tool calls and append function responses
                    function_response_messages = []
                    for fc in function_calls:
                        tool_name = fc.get("name")
                        raw_args = fc.get("args")
                        try:
                            if isinstance(raw_args, str):
                                args_dict = json.loads(raw_args or "{}")
                            else:
                                args_dict = raw_args or {}
                        except Exception:
                            args_dict = {}

                        # Persist assistant function call (serialized) in Redis
                        try:
                            self.redis_client.add_message({
                                "role": "assistant",
                                "function_call": {"name": tool_name, "args": args_dict}
                            })
                        except Exception:
                            pass

                        # Execute tool safely via MCP
                        tool_result_msg = await self._call_tool_safely(orchestrator, tool_name or "", args_dict, tool_name or "call")
                        tool_content = tool_result_msg.get("content", "")

                        # Try to parse content as JSON for structured response
                        structured_response = None
                        try:
                            structured_response = json.loads(tool_content)
                        except Exception:
                            structured_response = {"content": tool_content}

                        function_response_messages.append({
                            "role": "user",
                            "parts": [{
                                "function_response": {
                                    "name": tool_name,
                                    "response": structured_response
                                }
                            }]
                        })

                        # Persist tool result in Redis for future context
                        try:
                            self.redis_client.add_message({
                                "role": "tool",
                                "name": tool_name,
                                "content": tool_content,
                                "structured_response": structured_response
                            })
                        except Exception:
                            pass

                    contents.extend(function_response_messages)
                    # Ask model to continue with the new tool results
                    result = await asyncio.to_thread(model.generate_content, contents)

                return None

        except Exception as e:
            print(f"Error with Gemini tool-chat: {e}")
            return None


    async def run_chat(self):

        async with MCPOrchestrator() as orchestrator:
            today_date = datetime.now().isoformat() + "Z"
            user_email = "rakeshb1602@gmail.com"
            print("====== System Prompt ====== : \n")
            print(system_prompt)
            print("====== System Prompt ====== : \n")
            while True:
                try:
                    user_input = input("You: ")
                    if(user_input == 'exit'):
                        break
                    elif(user_input == 'clear'):
                        self.conversation_history = []
                        continue
                    elif(user_input == 'history'):
                        print('Conversation History : ')
                        print(self.conversation_history)
                        continue
                    messages = []
                    messages.append({"role": "system", "content": system_prompt})
                    if len(self.conversation_history) > 0:
                        messages.extend(self.conversation_history)
                    messages.append({"role": "user", "content": user_input})
                    self.conversation_history.append({"role": "user", "content": user_input})
                    tools_specs = await orchestrator.get_all_tools_specs()
                    response = self.client.chat.completions.create(
                    max_tokens=1000,
                    tools=self.get_tools_from_specs(tools_specs),
                    model="gpt-4o",
                    tool_choice="auto",
                    messages=messages)
                    message = response.choices[0].message
                    assistant_message = ({
                        "role": "assistant",
                        "content": message.content,
                        "tool_calls": getattr(message, "tool_calls", None)
                    })
                    self.conversation_history.append(assistant_message)
                    if message.tool_calls:
                        for tool in message.tool_calls:
                            print(f"Tool Call : {tool}")
                        print(f"🔧 Executing {len(message.tool_calls)} tool call(s)...")
                        tool_messages = await self._execute_tool_calls(orchestrator, list(message.tool_calls))
                        self.conversation_history.extend(tool_messages)

                        iterations = 0
                        while iterations < self.MAX_ITERATIONS:
                            iterations += 1
                            follow_up_messages = [{"role": "system", "content": system_prompt}]
                            follow_up_messages.extend(self.conversation_history)
                            follow_up_response = self.client.chat.completions.create(
                                max_tokens=1000,
                                tools=self.get_tools_from_specs(tools_specs),
                                model="gpt-4o",
                                tool_choice="auto",
                                messages=follow_up_messages)
                            follow_up_message = follow_up_response.choices[0].message
                            if follow_up_message.tool_calls:
                                print(f"🔧 Executing {len(follow_up_message.tool_calls)} tool call(s)...")
                                additional_tool_messages = await self._execute_tool_calls(orchestrator, list(follow_up_message.tool_calls))
                                print('Additional Tool Messages : ',additional_tool_messages)
                                self.conversation_history.append({
                                    "role": "assistant",
                                    "content": follow_up_message.content or "",
                                    "tool_calls": getattr(follow_up_message, "tool_calls", None)
                                })
                                self.conversation_history.extend(additional_tool_messages)
                            else:
                                print('No tool calls in follow up message')
                                self.conversation_history.append({
                                    "role": "assistant",
                                    "content": follow_up_message.content or ""
                                })
                                if follow_up_message.content:
                                    print(f"\n🤖 Telugu Vermi Farms Assistant: {follow_up_message.content}")
                                break
                        else:
                            print("Reached the maximum number of iterations for tool calls.")
                            print("\n🤖 Telugu Vermi Farms Assistant: I've completed all the required actions. Is there anything else I can help you with?")
                    else:
                        print(f"\n🤖 Telugu Vermi Farms Assistant: {message.content}")
                except KeyboardInterrupt:
                    print('🤖 Telugu Vermi Farms Assistant: Thank you for using the farm management system. Goodbye!')
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    continue

    async def transform_response_to_html(self, response: str):
        try:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            genai.configure(api_key=api_key)
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
            model = genai.GenerativeModel(model_name)

            # Coerce input to a safe string to satisfy Gemini 'parts' requirements
            if isinstance(response, str):
                safe_response = response
            else:
                try:
                    safe_response = json.dumps(response, ensure_ascii=False)
                except Exception:
                    safe_response = str(response or "")
            if safe_response is None:
                safe_response = ""

            # Simpler prompt format: pass strings instead of structured parts
            prompts = [html_transform_system_prompt or "", safe_response]
            result = await asyncio.to_thread(model.generate_content, prompts)
            text = _gemini_result_text(result)
            return text or "<div></div>"
        except Exception as e:
            print(f"Error: {e}")
            safe = response if isinstance(response, str) else str(response or "")
            escaped = (
                safe.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            return f"<div><p>{escaped}</p></div>"


async def main():
    """Main entry point."""
    assistant = TeluguVermiFarmsClient()
    await assistant.run_chat()


if __name__ == "__main__":
    asyncio.run(main())
