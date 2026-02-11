from client import TeluguVermiFarmsClient
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import socketio
from socket_server import sio
from auth_middleware import get_current_user, JWTPayload
import os

# Initialize FastAPI
app = FastAPI(
    title="Ila Compost Assistant API",
    version="1.0.0",
    description="Simple FastAPI web server for AI compost assistant",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

assistant = TeluguVermiFarmsClient()

# --- Routes ---
@app.get("/")
async def root():
    return {"message": "Ila compost assistant is running 🌱", "socket": "enabled"}

@app.post("/chat")
async def chat(request: Request, user: JWTPayload = Depends(get_current_user)):
    """
    POST /chat
    Body: {"message": "User text"}
    Streams AI response as plain text
    Requires: JWT authentication via Bearer token
    """
    try:
        data = await request.json()
        user_msg = data.get("message")
        print('User Message ====', user_msg)
        print('Authenticated User:', user.email)
        if not user_msg:
            return JSONResponse({"error": "Missing 'message' field"}, status_code=400)
        # Fetch history through assistant method so we can change storage later without touching server
        history = assistant.get_history()
        print('History ====', history)
        # Use unified chat method which handles provider selection
        response = await assistant.chat(history, user_msg)
            
        return JSONResponse({"response": response}, status_code=200)

        

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.on_event("shutdown")
async def shutdown_event():
    """Clear Redis conversation history on server shutdown."""
    print("Shutting down server... Clearing Redis history.")
    try:
        assistant.redis_client.clear_history()
    except Exception as e:
        print(f"Error during shutdown cleanup: {e}")

# Wrap FastAPI with Socket.IO ASGI app
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
