"""Authentication models and FastAPI dependencies."""

from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import ENTRA_TENANT_ID, ENTRA_AUDIENCE
from utils import logger
from .entra import validate_token

# Security scheme for OpenAPI documentation
security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(security_scheme)
) -> dict | None:
    """FastAPI dependency to validate Entra ID tokens.
    
    Returns:
        User claims if token is valid and Entra ID is configured, None if not configured.
        
    Raises:
        HTTPException: 401 if token is invalid or missing when Entra ID is configured.
    """
    # Skip validation if Entra ID is not configured
    if not ENTRA_TENANT_ID or not ENTRA_AUDIENCE:
        logger.warning("⚠️  Entra ID not configured - skipping token validation")
        return None
    
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": 'Bearer realm="api"'}
        )
    
    return await validate_token(credentials.credentials)
