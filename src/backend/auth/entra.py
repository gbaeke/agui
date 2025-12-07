"""Entra ID token validation and JWKS management."""

import time
import httpx
import jwt
from fastapi import HTTPException

from config import ENTRA_TENANT_ID, JWKS_CACHE_DURATION, TOKEN_REPLAY_CACHE_MAX_SIZE
from utils import logger

# Cache for JWKS keys
_jwks_cache: dict = {}
_jwks_cache_time: float = 0

# Token replay prevention cache (stores token IDs with expiration)
# In production, use Redis or similar distributed cache
_token_replay_cache: dict[str, float] = {}


async def get_jwks_keys() -> dict:
    """Fetch and cache Microsoft's JWKS keys asynchronously."""
    global _jwks_cache, _jwks_cache_time
    
    if _jwks_cache and (time.time() - _jwks_cache_time) < JWKS_CACHE_DURATION:
        return _jwks_cache
    
    jwks_url = f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}/discovery/v2.0/keys"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(jwks_url)
        _jwks_cache = response.json()
        _jwks_cache_time = time.time()
        logger.info("Fetched JWKS keys from Microsoft")
        return _jwks_cache


async def get_signing_key(token: str) -> str:
    """Get the signing key for a token from JWKS."""
    # Decode header without verification to get kid
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    
    if not kid:
        raise ValueError("Token missing 'kid' header")
    
    jwks = await get_jwks_keys()
    
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            # Convert JWK to PEM
            from jwt.algorithms import RSAAlgorithm
            return RSAAlgorithm.from_jwk(key)
    
    raise ValueError(f"Unable to find signing key for kid: {kid}")


def _check_token_replay(jti: str, exp: float) -> None:
    """Check and prevent token replay attacks."""
    global _token_replay_cache
    
    current_time = time.time()
    
    # Clean up expired tokens from cache to prevent unbounded growth
    if len(_token_replay_cache) > TOKEN_REPLAY_CACHE_MAX_SIZE:
        _token_replay_cache = {
            k: v for k, v in _token_replay_cache.items() 
            if v > current_time
        }
    
    # Check if token was already used
    if jti in _token_replay_cache:
        raise ValueError("Token has already been used (replay detected)")
    
    # Add token to cache with its expiration time
    _token_replay_cache[jti] = exp


async def validate_token(token: str) -> dict:
    """Validate an Entra ID token and return the claims."""
    from config import ENTRA_AUDIENCE, ENTRA_TENANT_ID
    
    try:
        signing_key = await get_signing_key(token)
        
        # Verify the token with clock skew tolerance
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=ENTRA_AUDIENCE,
            issuer=f"https://sts.windows.net/{ENTRA_TENANT_ID}/",
            leeway=60,  # 60 seconds tolerance for clock skew
        )
        
        # Validate nbf (not before) claim if present
        if "nbf" in claims:
            nbf = claims["nbf"]
            if time.time() < nbf:
                raise ValueError("Token not yet valid (nbf claim)")
        
        # Token replay protection using jti (JWT ID)
        jti = claims.get("jti")
        if jti:
            exp = claims.get("exp", time.time() + 3600)
            _check_token_replay(jti, exp)
        
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
