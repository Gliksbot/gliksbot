"""
Simple hardcoded authentication module for Dexter v3
Replaces Active Directory/LDAP authentication with hardcoded credentials
"""
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Hardcoded user credentials
HARDCODED_USERS = {
    "Jeff": "S3rv3r123",
    "Jacob": "Tank"
}

# JWT configuration
JWT_SECRET = os.environ.get("DEXTER_JWT_SECRET", "your_very_secure_jwt_secret_here_minimum_32_characters")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24

security = HTTPBearer()

class AuthManager:
    """Simple authentication manager with hardcoded credentials"""
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with hardcoded credentials
        Returns user info if valid, None otherwise
        """
        if username in HARDCODED_USERS and HARDCODED_USERS[username] == password:
            return {
                "username": username,
                "full_name": username,
                "roles": ["admin"],  # All authenticated users have full access
                "authenticated": True
            }
        return None
    
    def create_jwt_token(self, user_info: Dict[str, Any]) -> str:
        """Create JWT token for authenticated user"""
        payload = {
            "sub": user_info["username"],
            "username": user_info["username"],
            "full_name": user_info["full_name"],
            "roles": user_info["roles"],
            "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

# Global auth manager instance
auth_manager = AuthManager()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user from JWT token
    Use this to protect routes that require authentication
    """
    return auth_manager.verify_jwt_token(credentials.credentials)

def verify_token_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """
    Optional authentication dependency
    Returns user info if authenticated, None if not
    """
    if credentials is None:
        return None
    try:
        return auth_manager.verify_jwt_token(credentials.credentials)
    except HTTPException:
        return None