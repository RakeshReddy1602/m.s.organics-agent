import jwt
import os
import datetime
import sys

# Default to the value in the file if not set, but warn the user
# validation logic from auth_middleware.py
JWT_SECRET = os.getenv('JWT_SECRET')

if not JWT_SECRET:
    print("Error: JWT_SECRET environment variable is not set.")
    print("Please run this script with the JWT_SECRET set, e.g.:")
    print("JWT_SECRET=your_real_secret python agent/generate_jwt.py")
    sys.exit(1)

def generate_token():
    # Payload matching JWTPayload class in auth_middleware.py
    # class JWTPayload:
    #     def __init__(self, userId: int, email: str, name: str, userCode: str):
    
    payload = {
        "userId": 1,  # Admin/System user ID
        "email": "agent@system.local",
        "name": "System Agent",
        "userCode": "SYS001",
        "iat": datetime.datetime.utcnow(),
        # Expire in 10 years for a "production" service token, or configure as needed
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=3650)
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token

if __name__ == "__main__":
    try:
        token = generate_token()
        print("\nGenerated Production JWT:")
        print("-" * 20)
        print(token)
        print("-" * 20)
        print("\nAdd this token to your client or wherever it's needed as:")
        print(f"Authorization: Bearer {token}")
    except Exception as e:
        print(f"Error generating token: {e}")
