"""Entra ID token validation and JWKS management."""

import time
import httpx
import jwt
from fastapi import HTTPException

from config import ENTRA_TENANT_ID, JWKS_CACHE_DURATION
from utils import logger

# Prefer PyJWT's built-in JWKS client for key selection. It handles fetching
# and picking the correct key for a given JWT (kid) reliably.
from jwt import PyJWKClient

# Cache for JWKS keys
_jwks_cache: dict = {}
_jwks_cache_time: float = 0

# Cache PyJWKClient instance
_jwk_client: PyJWKClient | None = None
_jwk_client_tenant: str = ""

async def get_jwks_keys() -> dict:
    """Fetch and cache Microsoft's JWKS keys asynchronously."""
    global _jwks_cache, _jwks_cache_time
    
    if _jwks_cache and (time.time() - _jwks_cache_time) < JWKS_CACHE_DURATION:
        return _jwks_cache
    
    jwks_url = f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}/discovery/v2.0/keys"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        _jwks_cache = response.json()
        _jwks_cache_time = time.time()
        logger.info("Fetched JWKS keys from Microsoft")
        return _jwks_cache


async def get_signing_key(token: str) -> str:
    """Get the signing key for a token from JWKS."""
    global _jwk_client, _jwk_client_tenant

    if not ENTRA_TENANT_ID:
        raise ValueError("ENTRA_TENANT_ID is not configured")

    jwks_url = f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}/discovery/v2.0/keys"

    if _jwk_client is None or _jwk_client_tenant != ENTRA_TENANT_ID:
        _jwk_client = PyJWKClient(jwks_url, cache_keys=True, timeout=10)
        _jwk_client_tenant = ENTRA_TENANT_ID

    signing_key = _jwk_client.get_signing_key_from_jwt(token).key
    return signing_key


async def validate_token(token: str) -> dict:
    """Validate an Entra ID token and return the claims."""
    from config import ENTRA_AUDIENCE, ENTRA_TENANT_ID
    
    try:
        signing_key = await get_signing_key(token)

        def _decode_with_key(key):
            return jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=ENTRA_AUDIENCE,
                issuer=f"https://sts.windows.net/{ENTRA_TENANT_ID}/",
                leeway=60,  # 60 seconds tolerance for clock skew
            )

        # Verify the token with clock skew tolerance
        try:
            claims = _decode_with_key(signing_key)
        except jwt.InvalidSignatureError:
            # Keys can rotate; rebuild the JWK client once and retry.
            global _jwk_client
            _jwk_client = None
            signing_key = await get_signing_key(token)
            claims = _decode_with_key(signing_key)
        
        # Validate nbf (not before) claim if present
        if "nbf" in claims:
            nbf = claims["nbf"]
            if time.time() < nbf:
                raise ValueError("Token not yet valid (nbf claim)")
        
        logger.info(f"✅ Token validated for user: {claims.get('preferred_username', claims.get('sub', 'unknown'))}")
        return claims
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired",
            headers={"WWW-Authenticate": 'Bearer realm="api", error="invalid_token", error_description="Token has expired"'}
        )
    except jwt.InvalidAudienceError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token audience",
            headers={"WWW-Authenticate": 'Bearer realm="api", error="invalid_token", error_description="Invalid audience"'}
        )
    except jwt.InvalidIssuerError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token issuer",
            headers={"WWW-Authenticate": 'Bearer realm="api", error="invalid_token", error_description="Invalid issuer"'}
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": 'Bearer realm="api", error="invalid_token"'}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": 'Bearer realm="api", error="invalid_token"'}
        )
