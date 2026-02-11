"""
Socket.IO server for Agent - handles real-time chat with BE Server
"""
import socketio
import asyncio
from client import TeluguVermiFarmsClient

# Create Socket.IO server (async mode)
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=['http://localhost:3000', 'http://127.0.0.1:3000', '*']
)

# Initialize the assistant client
assistant = TeluguVermiFarmsClient()

@sio.event
async def connect(sid, environ):
    print(f'✅ BE Server connected: {sid}')

@sio.event
async def disconnect(sid):
    print(f'❌ BE Server disconnected: {sid}')

@sio.on('chat:send')
async def handle_chat(sid, data):
    """
    Handle chat message from BE Server
    data: { message: str, conversationId: str, userId: int, userToken: str }
    """
    message = data.get('message', '')
    conversation_id = data.get('conversationId', '')
    user_id = data.get('userId')
    user_token = data.get('userToken', '')  # Get token from BE server
    
    print(f'📨 Message from BE Server (user {user_id}): {message}')
    
    try:
        # Get conversation history
        history = assistant.get_history()
        
        # Send "thinking" status
        await sio.emit('chat:status', {
            'status': 'thinking',
            'conversationId': conversation_id
        }, room=sid)
        
        # Get response using unified chat interface (handles Gemini/OpenAI switching)
        response = await assistant.chat(history, message, user_token)
        
        if response:
            # Stream the response word by word
            words = (response or "").split(' ')
            for i, word in enumerate(words):
                await sio.emit('chat:stream', {
                    'chunk': word + ' ',
                    'index': i,
                    'conversationId': conversation_id
                }, room=sid)
                await asyncio.sleep(0.01)  # Reduced delay for faster streaming
            
            # Signal completion
            await sio.emit('chat:complete', {
                'conversationId': conversation_id,
                'fullResponse': response
            }, room=sid)
        else:
            await sio.emit('chat:error', {
                'message': 'No response from assistant',
                'conversationId': conversation_id
            }, room=sid)
            
    except Exception as e:
        print(f'❌ Chat error: {e}')
        # Send generic error to user, log actual error
        await sio.emit('chat:error', {
            'message': 'An internal error occurred. Please try again later.',
            'conversationId': conversation_id
        }, room=sid)

@sio.on('ping')
async def handle_ping(sid):
    print(f'🏓 Ping from {sid}')
    await sio.emit('pong', {'timestamp': asyncio.get_event_loop().time()}, room=sid)

# Create ASGI app
app = socketio.ASGIApp(sio)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
