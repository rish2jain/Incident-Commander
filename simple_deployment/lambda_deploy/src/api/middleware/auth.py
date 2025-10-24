"""
Authentication middleware for API endpoints.

Provides API key authentication for showcase and sensitive endpoints.
"""

from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.utils.config import config
from src.utils.logging import get_logger

logger = get_logger("auth_middleware")

security = HTTPBearer(auto_error=False)


async def verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> bool:
    """
    Verify API key for showcase endpoints.
    
    In development mode, allows access without authentication.
    In production, requires valid API key.
    """
    # Allow access in development mode
    if config.environment == "development":
        return True
    
    # Require authentication in production
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate API key (in production, this would check against a secure store)
    valid_api_keys = [
        getattr(config, 'showcase_api_key', None),
        getattr(config, 'demo_api_key', None),
        getattr(config, 'admin_api_key', None)
    ]
    
    if credentials.credentials not in [key for key in valid_api_keys if key]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return True


async def verify_demo_access(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> bool:
    """
    Verify access for demo endpoints.
    
    More permissive authentication for demo scenarios.
    """
    # Always allow in development
    if config.environment == "development":
        return True
    
    # In staging/production, allow demo access with basic validation
    if not credentials and config.environment != "development":
        # For demo purposes, we can be more lenient
        logger.warning("Demo access without authentication - allowed for demonstration")
        return True
    
    return await verify_api_key(credentials)


async def verify_admin_access(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> bool:
    """
    Verify admin access for sensitive operations.
    
    Requires admin-level authentication.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check admin API key
    admin_key = getattr(config, 'admin_api_key', None)
    if not admin_key or credentials.credentials != admin_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return True