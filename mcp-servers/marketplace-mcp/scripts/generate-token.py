#!/usr/bin/env python3
"""Generate JWT token for marketplace-mcp local access"""

import jwt
import datetime
import sys

# Default secret from HAS .env
JWT_SECRET = "change_me_market_jwt"
JWT_ALGORITHM = "HS256"

def generate_token(scopes: list[str], expires_hours: int = 24) -> str:
    payload = {
        "sub": "local-agent",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=expires_hours),
        "scope": " ".join(scopes),
        "scopes": scopes,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

if __name__ == "__main__":
    scopes = sys.argv[1:] if len(sys.argv) > 1 else ["market:read"]
    token = generate_token(scopes)
    print(token)
