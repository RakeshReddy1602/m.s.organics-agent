
from fastmcp import Client as MCPClient
from contextlib import AsyncExitStack
from typing import Optional, Dict, List, Any
import json


class MCPOrchestrator:

    def __init__(self, admin_agent_url: Optional[str] = None) -> None:
        # Assign URL for MCP server, defaulting to the server in mcp-server.py if not provided
        import os
        self.admin_agent_url = admin_agent_url or os.getenv("MCP_SERVER_URL", "http://127.0.0.1:6280/mcp")
        self._clients: Dict[str, MCPClient] = {}
        self._stack: Optional[AsyncExitStack] = None
        print(f"MCP Orchestrator initialized with URL: {self.admin_agent_url}")
    
    async def __aenter__(self) -> "MCPOrchestrator":
        print(f"Connecting to MCP Server at {self.admin_agent_url}...")
        self._stack = AsyncExitStack()
        admin_agent_client = MCPClient(self.admin_agent_url)
        print("Initializing admin_agent client...")
        await self._stack.enter_async_context(admin_agent_client)
        self._clients["admin_agent"] = admin_agent_client
        print("admin_agent client initialized.")
        # Print the nested object for the admin_agent client (for debugging)
        # print("admin_agent client object:", self._clients["admin_agent"].__dict__)
        # Print all tools inside this client
        tools = await self._clients["admin_agent"].list_tools()
        print(f"Discovered {len(tools)} tools in admin_agent client.")
        # for tool in tools:
        #     print(f"  - {tool.name}: {getattr(tool, 'description', '')}")
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self._stack.aclose()

    async def get_client(self, name: str) -> MCPClient:
        return self._clients[name]

    def to_plain_json_schema(self, schema: Any) -> Dict[str, Any]:
        """Convert any schema object to plain JSON-serializable dict."""
        if isinstance(schema, dict):
            return schema
        try:
            return json.loads(json.dumps(schema, default=str))
        except (TypeError, ValueError):
            return {}

    async def get_all_tools_specs(self, namespaced: bool = True) -> List[Dict[str, Any]]:
        """
        Return a normalized, model-agnostic view of all tools with namespacing.
        
        Each item:
        {
          "server": "calendar",
          "name": "calendar__list-events" (if namespaced) or "list-events",
          "bare_name": "list-events",
          "description": "...",
          "inputSchema": {...}  # plain JSON Schema
        }
        """
        specs: List[Dict[str, Any]] = []
        for server, c in self._clients.items():
            tools = await c.list_tools()
            print('Length : ',len(tools))
            for t in tools:
                desc = getattr(t, "description", "") or getattr(t, "title", "")
                inputSchema = self.to_plain_json_schema(getattr(t, "inputSchema", {}) or {})
                bare_name = t.name
                full_name = f"{server}__{bare_name}" if namespaced else bare_name
                specs.append({
                    "server": server,
                    "name": full_name,
                    "bare_name": bare_name,
                    "description": desc,
                    "inputSchema": inputSchema,
                })
        return specs
            

    async def call_tool(self, server: str, name: str, params: Dict[str, Any]) -> Any:
        if server not in self._clients:
            raise ValueError(f"Server {server} not found")
        return await self._clients[server].call_tool(name, params or {})