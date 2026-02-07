#!/bin/bash

# Start the MCP server in the background
echo "Starting MCP Server..."
python mcp-server.py &

# Wait a moment for MCP server to initialize
sleep 5

# Start the main application
echo "Starting Agent Server..."
uvicorn server:socket_app --host 0.0.0.0 --port $PORT
