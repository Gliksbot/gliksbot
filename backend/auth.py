"""
Simple hardcoded authentication module for Dexter v3
Replaces Active Directory/LDAP authentication with hardcoded credentials
"""
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm

router = APIRouter()

# Hardcoded user credentials
HARDCODED_USERS = {
    "Jeff": "S3rv3r123",
    "Jacob": "Tank"
}

# Simple in-memory login attempt tracking (basic rate limiting scaffold)
_login_attempts: Dict[str, Dict[str, Any]] = {}
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 300

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
        Applies basic lockout on repeated failures.
        """
        now = datetime.utcnow().timestamp()
        rec = _login_attempts.setdefault(username, {"fails": 0, "lock_until": 0})
        if rec["lock_until"] > now:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Account temporarily locked. Try later.")
        
        if username in HARDCODED_USERS and HARDCODED_USERS[username] == password:
            rec["fails"] = 0
            rec["lock_until"] = 0
            return {
                "username": username,
                "full_name": username,
                "roles": ["admin"],  # All authenticated users have full access
                "authenticated": True
            }
        # failure
        rec["fails"] += 1
        if rec["fails"] >= MAX_ATTEMPTS:
            rec["lock_until"] = now + LOCKOUT_SECONDS
        return None
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT token for authenticated user"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # -------------------------------------------------------------------------
    # Backwards‑compatibility aliases
    #
    # Some parts of the application (e.g. login routes in backend/main.py) expect
    # ``AuthManager`` to expose ``create_jwt_token`` and ``verify_jwt_token``.
    # These methods were not originally defined, causing attribute errors and
    # resulting in HTTP 500 responses.  Provide alias methods that delegate to
    # the existing implementations.

    def create_jwt_token(self, user_info: Dict[str, Any]) -> str:
        """Alias for ``create_access_token``.  Accepts a user_info dict and
        encodes the ``username`` as the subject (``sub``) claim in the token."""
        # Use the user_info to construct the payload; mimic the behaviour of
        # create_access_token by using "sub" as the subject.
        data = {"sub": user_info.get("username")}
        return self.create_access_token(data)

    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """Alias for ``validate_token``.  Decodes and validates a JWT token."""
        return self.validate_token(token)

    def validate_token(self, token: str) -> Dict[str, Any]:
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
        except jwt.InvalidTokenError:
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
    return auth_manager.validate_token(credentials.credentials)

@router.post("/token", tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Provides a JWT token for valid credentials."""
    user = auth_manager.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_manager.create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me/", tags=["Users"])
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """Returns the current authenticated user's details."""
    return current_user

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