"""Authentication middleware for FastAPI."""

from fastapi import HTTPException
from starlette.responses import JSONResponse

from config import ENTRA_TENANT_ID, ENTRA_AUDIENCE
from .entra import validate_token


async def authentication_middleware(request, call_next):
    """Middleware to enforce authentication on all endpoints except health checks and OPTIONS."""
    # Skip auth for health checks and OPTIONS requests
    if request.url.path == "/health" or request.method == "OPTIONS":
        return await call_next(request)
    
    # Skip if Entra ID not configured
    if not ENTRA_TENANT_ID or not ENTRA_AUDIENCE:
        return await call_next(request)
    
    # Extract and validate token
    authorization = request.headers.get("authorization")
    if not authorization or not authorization.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"detail": "Missing authentication credentials"},
            headers={"WWW-Authenticate": 'Bearer realm="api"'}
        )
    
    token = authorization[7:]  # Remove "Bearer " prefix
    # Some proxies/libraries can append extra values (e.g., ", ...").
    # Only keep the first token-like value.
    token = token.strip().split(",", 1)[0].strip().split(" ", 1)[0].strip()
    
    try:
        await validate_token(token)
        return await call_next(request)
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail},
            headers=e.headers
        )
