from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from typing import Optional

# JWT configuration - must match server configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')

security = HTTPBearer()

class JWTPayload:
    def __init__(self, userId: int, email: str, name: str, userCode: str):
        self.userId = userId
        self.email = email
        self.name = name
        self.userCode = userCode

def verify_access_token(token: str) -> JWTPayload:
    """
    Verify JWT access token and return user payload
    """
    try:
        # Decode and verify JWT token
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        
        # Extract user information
        user_data = JWTPayload(
            userId=payload.get('userId'),
            email=payload.get('email'),
            name=payload.get('name'),
            userCode=payload.get('userCode')
        )
        
        return user_data
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired. Please refresh your token."
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid access token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = security) -> JWTPayload:
    """
    Dependency to get current authenticated user from JWT token
    Usage: user = Depends(get_current_user)
    """
    token = credentials.credentials
    return verify_access_token(token)

async def get_current_user_optional(request: Request) -> Optional[JWTPayload]:
    """
    Optional authentication - returns None if no token or invalid token
    Usage: user = Depends(get_current_user_optional)
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.replace('Bearer ', '')
        return verify_access_token(token)
    except:
        return None
