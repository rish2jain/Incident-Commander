"""
Authentication and authorization middleware for API security.
"""

import asyncio
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set
from functools import wraps

import jwt
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.utils.config import config
from src.utils.logging import get_logger
from src.utils.exceptions import AuthenticationError, AuthorizationError

logger = get_logger("auth_middleware")

# Security bearer for JWT tokens
security = HTTPBearer()


class SecurityConfig:
    """Security configuration for authentication and authorization."""
    
    def __init__(self):
        """Initialize security configuration."""
        self.jwt_secret_key = config.security.jwt_secret_key
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_hours = 24
        self.api_rate_limit = config.security.api_rate_limit  # requests per minute
        self.cors_origins = config.security.cors_origins
        self.require_auth = config.security.require_auth
        self.demo_api_key = config.security.demo_api_key
        
        # RBAC scopes
        self.rbac_scopes = {
            'admin': ['read', 'write', 'delete', 'admin'],
            'operator': ['read', 'write'],
            'viewer': ['read'],
            'demo': ['read', 'demo']
        }
        
        # Route permissions
        self.route_permissions = {
            '/incidents/trigger': ['write', 'admin'],
            '/incidents/{id}/resolve': ['write', 'admin'],
            '/agents/status': ['read', 'write', 'admin'],
            '/system/health': ['read', 'write', 'admin'],
            '/demo/': ['demo', 'read', 'write', 'admin'],
            '/ultimate-demo/': ['demo', 'read', 'write', 'admin'],
            '/admin/': ['admin']
        }


class RateLimiter:
    """Rate limiter for API endpoints."""
    
    def __init__(self, requests_per_minute: int = 60):
        """Initialize rate limiter."""
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = {}
        self.lock = asyncio.Lock()
    
    async def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed based on rate limit.
        
        Args:
            identifier: Unique identifier for rate limiting (IP, user ID, etc.)
            
        Returns:
            True if request is allowed, False otherwise
        """
        async with self.lock:
            now = time.time()
            minute_ago = now - 60
            
            # Clean old requests
            if identifier in self.requests:
                self.requests[identifier] = [
                    req_time for req_time in self.requests[identifier] 
                    if req_time > minute_ago
                ]
            else:
                self.requests[identifier] = []
            
            # Check rate limit
            if len(self.requests[identifier]) >= self.requests_per_minute:
                return False
            
            # Add current request
            self.requests[identifier].append(now)
            return True
    
    async def get_remaining_requests(self, identifier: str) -> int:
        """Get remaining requests for identifier."""
        async with self.lock:
            now = time.time()
            minute_ago = now - 60
            
            if identifier in self.requests:
                recent_requests = [
                    req_time for req_time in self.requests[identifier] 
                    if req_time > minute_ago
                ]
                return max(0, self.requests_per_minute - len(recent_requests))
            
            return self.requests_per_minute


class JWTManager:
    """JWT token management."""
    
    def __init__(self, security_config: SecurityConfig):
        """Initialize JWT manager."""
        self.security_config = security_config
    
    def create_token(self, user_id: str, scopes: List[str], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT token for user.
        
        Args:
            user_id: User identifier
            scopes: List of permission scopes
            expires_delta: Token expiration time
            
        Returns:
            JWT token string
        """
        if expires_delta is None:
            expires_delta = timedelta(hours=self.security_config.jwt_expiration_hours)
        
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            'sub': user_id,
            'scopes': scopes,
            'exp': expire,
            'iat': datetime.utcnow(),
            'iss': 'incident-commander'
        }
        
        token = jwt.encode(
            payload, 
            self.security_config.jwt_secret_key, 
            algorithm=self.security_config.jwt_algorithm
        )
        
        logger.info(f"Created JWT token for user {user_id} with scopes {scopes}")
        return token
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.security_config.jwt_secret_key,
                algorithms=[self.security_config.jwt_algorithm]
            )
            
            # Verify token hasn't expired
            if datetime.utcnow() > datetime.fromtimestamp(payload['exp']):
                raise AuthenticationError("Token has expired")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {e}")
    
    def refresh_token(self, token: str) -> str:
        """
        Refresh JWT token.
        
        Args:
            token: Current JWT token
            
        Returns:
            New JWT token
        """
        payload = self.verify_token(token)
        
        # Create new token with same user and scopes
        return self.create_token(
            user_id=payload['sub'],
            scopes=payload['scopes']
        )


class APIKeyManager:
    """API key management for demo and service access."""
    
    def __init__(self, security_config: SecurityConfig):
        """Initialize API key manager."""
        self.security_config = security_config
        self.api_keys: Dict[str, Dict[str, Any]] = {
            # Demo API key
            self.security_config.demo_api_key: {
                'name': 'demo',
                'scopes': ['demo', 'read'],
                'created_at': datetime.utcnow(),
                'last_used': None
            }
        }
    
    def generate_api_key(self, name: str, scopes: List[str]) -> str:
        """
        Generate new API key.
        
        Args:
            name: API key name/description
            scopes: Permission scopes for the key
            
        Returns:
            Generated API key
        """
        # Generate secure API key
        key_data = f"{name}:{datetime.utcnow().isoformat()}:{time.time()}"
        api_key = hashlib.sha256(key_data.encode()).hexdigest()
        
        self.api_keys[api_key] = {
            'name': name,
            'scopes': scopes,
            'created_at': datetime.utcnow(),
            'last_used': None
        }
        
        logger.info(f"Generated API key for {name} with scopes {scopes}")
        return api_key
    
    def verify_api_key(self, api_key: str) -> Dict[str, Any]:
        """
        Verify API key and return associated data.
        
        Args:
            api_key: API key to verify
            
        Returns:
            API key data
            
        Raises:
            AuthenticationError: If API key is invalid
        """
        if api_key not in self.api_keys:
            raise AuthenticationError("Invalid API key")
        
        key_data = self.api_keys[api_key]
        key_data['last_used'] = datetime.utcnow()
        
        return key_data
    
    def revoke_api_key(self, api_key: str) -> bool:
        """
        Revoke API key.
        
        Args:
            api_key: API key to revoke
            
        Returns:
            True if key was revoked, False if not found
        """
        if api_key in self.api_keys:
            del self.api_keys[api_key]
            logger.info(f"Revoked API key: {api_key[:8]}...")
            return True
        return False


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for FastAPI."""
    
    def __init__(self, app, security_config: SecurityConfig):
        """Initialize authentication middleware."""
        super().__init__(app)
        self.security_config = security_config
        self.jwt_manager = JWTManager(security_config)
        self.api_key_manager = APIKeyManager(security_config)
        self.rate_limiter = RateLimiter(security_config.api_rate_limit)
        
        # Public endpoints that don't require authentication
        self.public_endpoints = {
            '/health',
            '/docs',
            '/openapi.json',
            '/redoc'
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request through authentication middleware."""
        # Skip authentication for public endpoints
        if any(request.url.path.startswith(endpoint) for endpoint in self.public_endpoints):
            return await call_next(request)
        
        # Skip authentication if not required (development mode)
        if not self.security_config.require_auth:
            return await call_next(request)
        
        try:
            # Rate limiting
            client_ip = request.client.host
            if not await self.rate_limiter.is_allowed(client_ip):
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"Maximum {self.security_config.api_rate_limit} requests per minute"
                    }
                )
            
            # Authentication
            user_info = await self._authenticate_request(request)
            
            # Authorization
            if not await self._authorize_request(request, user_info):
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "Insufficient permissions",
                        "message": "You don't have permission to access this resource"
                    }
                )
            
            # Add user info to request state
            request.state.user = user_info
            
            # Log security event
            await self._log_security_event(request, user_info, "access_granted")
            
            return await call_next(request)
            
        except AuthenticationError as e:
            await self._log_security_event(request, None, "authentication_failed", str(e))
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Authentication failed",
                    "message": str(e)
                }
            )
        except AuthorizationError as e:
            await self._log_security_event(request, None, "authorization_failed", str(e))
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Authorization failed",
                    "message": str(e)
                }
            )
        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            await self._log_security_event(request, None, "middleware_error", str(e))
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "Authentication system error"
                }
            )
    
    async def _authenticate_request(self, request: Request) -> Dict[str, Any]:
        """
        Authenticate request using JWT or API key.
        
        Args:
            request: FastAPI request object
            
        Returns:
            User information dictionary
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # Check for Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            if auth_header.startswith('Bearer '):
                # JWT token authentication
                token = auth_header[7:]  # Remove 'Bearer ' prefix
                payload = self.jwt_manager.verify_token(token)
                return {
                    'user_id': payload['sub'],
                    'scopes': payload['scopes'],
                    'auth_type': 'jwt'
                }
            elif auth_header.startswith('ApiKey '):
                # API key authentication
                api_key = auth_header[7:]  # Remove 'ApiKey ' prefix
                key_data = self.api_key_manager.verify_api_key(api_key)
                return {
                    'user_id': key_data['name'],
                    'scopes': key_data['scopes'],
                    'auth_type': 'api_key'
                }
        
        # Check for API key in query parameters (for demo purposes)
        api_key = request.query_params.get('api_key')
        if api_key:
            key_data = self.api_key_manager.verify_api_key(api_key)
            return {
                'user_id': key_data['name'],
                'scopes': key_data['scopes'],
                'auth_type': 'api_key'
            }
        
        raise AuthenticationError("No valid authentication credentials provided")
    
    async def _authorize_request(self, request: Request, user_info: Dict[str, Any]) -> bool:
        """
        Authorize request based on user scopes and route permissions.
        
        Args:
            request: FastAPI request object
            user_info: User information from authentication
            
        Returns:
            True if authorized, False otherwise
        """
        user_scopes = set(user_info.get('scopes', []))
        request_path = request.url.path
        
        # Find matching route permission
        required_scopes = None
        for route_pattern, scopes in self.security_config.route_permissions.items():
            if self._match_route_pattern(request_path, route_pattern):
                required_scopes = set(scopes)
                break
        
        # If no specific permissions required, allow access
        if required_scopes is None:
            return True
        
        # Check if user has any of the required scopes
        return bool(user_scopes.intersection(required_scopes))
    
    def _match_route_pattern(self, path: str, pattern: str) -> bool:
        """
        Match request path against route pattern.
        
        Args:
            path: Request path
            pattern: Route pattern (may contain wildcards)
            
        Returns:
            True if path matches pattern
        """
        # Simple pattern matching - can be enhanced with regex
        if pattern.endswith('/'):
            return path.startswith(pattern)
        elif '{' in pattern:
            # Handle path parameters like /incidents/{id}/resolve
            pattern_parts = pattern.split('/')
            path_parts = path.split('/')
            
            if len(pattern_parts) != len(path_parts):
                return False
            
            for pattern_part, path_part in zip(pattern_parts, path_parts):
                if pattern_part.startswith('{') and pattern_part.endswith('}'):
                    continue  # Skip path parameters
                elif pattern_part != path_part:
                    return False
            
            return True
        else:
            return path == pattern
    
    async def _log_security_event(self, request: Request, user_info: Optional[Dict[str, Any]], 
                                event_type: str, details: str = None):
        """
        Log security event for audit purposes.
        
        Args:
            request: FastAPI request object
            user_info: User information (if available)
            event_type: Type of security event
            details: Additional event details
        """
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'client_ip': request.client.host,
            'user_agent': request.headers.get('User-Agent'),
            'path': request.url.path,
            'method': request.method,
            'user_id': user_info.get('user_id') if user_info else None,
            'auth_type': user_info.get('auth_type') if user_info else None,
            'details': details
        }
        
        # Log to structured logger
        logger.info(f"Security event: {event_type}", extra={'security_event': event})


# Dependency functions for FastAPI
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User information dictionary
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # This would typically be injected by middleware
        # For now, we'll create a simple implementation
        security_config = SecurityConfig()
        jwt_manager = JWTManager(security_config)
        
        payload = jwt_manager.verify_token(credentials.credentials)
        return {
            'user_id': payload['sub'],
            'scopes': payload['scopes'],
            'auth_type': 'jwt'
        }
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))


def require_scopes(required_scopes: List[str]):
    """
    Decorator to require specific scopes for endpoint access.
    
    Args:
        required_scopes: List of required permission scopes
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would be implemented with proper dependency injection
            # For now, it's a placeholder
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Global security configuration instance
_security_config: Optional[SecurityConfig] = None

def get_security_config() -> SecurityConfig:
    """Get or create the global security configuration instance."""
    global _security_config
    if _security_config is None:
        _security_config = SecurityConfig()
    return _security_config