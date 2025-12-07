"""AG-UI Server - Hosts an AI agent accessible via HTTP with tools."""

import json
import logging
import os
import sys
import time
from collections.abc import Awaitable, Callable
from datetime import datetime
from functools import lru_cache

import httpx
import jwt
from dotenv import load_dotenv
from agent_framework import ChatAgent, FunctionInvocationContext, ai_function, function_middleware
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework_ag_ui import add_agent_framework_fastapi_endpoint
from azure.identity import DefaultAzureCredential
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Load environment variables
load_dotenv()

# Configure logging with explicit stdout handler for Docker
logger = logging.getLogger("agui.tools")
logger.setLevel(logging.INFO)

# Create stdout handler with formatting
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Entra ID configuration
ENTRA_TENANT_ID = os.environ.get("ENTRA_TENANT_ID", "")
ENTRA_AUDIENCE = os.environ.get("ENTRA_AUDIENCE", "")

# Cache for JWKS keys
_jwks_cache: dict = {}
_jwks_cache_time: float = 0
JWKS_CACHE_DURATION = 86400  # 24 hours

# Token replay prevention cache (stores token IDs with expiration)
# In production, use Redis or similar distributed cache
_token_replay_cache: dict[str, float] = {}
TOKEN_REPLAY_CACHE_MAX_SIZE = 10000  # Prevent unbounded growth


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


# Security scheme for OpenAPI documentation
security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Security(security_scheme)) -> dict | None:
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


# Function middleware to log tool calls
@function_middleware
async def tool_logging_middleware(
    context: FunctionInvocationContext,
    next: Callable[[FunctionInvocationContext], Awaitable[None]],
) -> None:
    """Middleware that logs tool calls with timing information."""
    function_name = context.function.name
    args = context.arguments
    
    logger.info(f"Tool call started: {function_name}")
    logger.info(f"  Arguments: {args}")
    
    start_time = time.time()
    
    await next(context)
    
    duration = time.time() - start_time
    
    logger.info(f"Tool call completed: {function_name} (took {duration:.3f}s)")
    if context.result is not None:
        # Truncate long results for logging
        result_str = str(context.result)
        if len(result_str) > 200:
            result_str = result_str[:200] + "..."
        logger.info(f"  Result: {result_str}")


# Read configuration
endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")

if not endpoint:
    raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")
if not deployment_name:
    raise ValueError("AZURE_OPENAI_DEPLOYMENT_NAME environment variable is required")


# Define tools for the agent
@ai_function(description="Get the current weather for a location")
def get_weather(location: str) -> str:
    """Get real weather information for a location using Open-Meteo API."""
    try:
        # Step 1: Geocode the location to get coordinates
        geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
        geocode_params = {"name": location, "count": 1, "language": "en", "format": "json"}
        
        with httpx.Client(timeout=10.0) as client:
            geo_response = client.get(geocode_url, params=geocode_params)
            geo_data = geo_response.json()
            
            if "results" not in geo_data or len(geo_data["results"]) == 0:
                return json.dumps({"error": f"Location '{location}' not found"})
            
            result = geo_data["results"][0]
            lat = result["latitude"]
            lon = result["longitude"]
            resolved_name = result.get("name", location)
            country = result.get("country", "")
            
            # Step 2: Get current weather
            weather_url = "https://api.open-meteo.com/v1/forecast"
            weather_params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                "timezone": "auto",
            }
            
            weather_response = client.get(weather_url, params=weather_params)
            weather_data = weather_response.json()
            
            current = weather_data.get("current", {})
            
            # Map weather codes to conditions
            weather_code = current.get("weather_code", 0)
            condition = _weather_code_to_condition(weather_code)
            
            return json.dumps({
                "location": f"{resolved_name}, {country}".strip(", "),
                "temperature": current.get("temperature_2m"),
                "humidity": current.get("relative_humidity_2m"),
                "wind_speed": current.get("wind_speed_10m"),
                "condition": condition,
            })
            
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return json.dumps({"error": str(e)})


def _weather_code_to_condition(code: int) -> str:
    """Map WMO weather codes to simple condition strings."""
    if code == 0:
        return "sunny"
    elif code in (1, 2):
        return "partly cloudy"
    elif code == 3:
        return "cloudy"
    elif code in (45, 48):
        return "foggy"
    elif code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return "rainy"
    elif code in (71, 73, 75, 77, 85, 86):
        return "snowy"
    elif code in (95, 96, 99):
        return "stormy"
    else:
        return "cloudy"


@ai_function(description="Get the current date and time in UTC (data is displayed in a UI widget - do not repeat the time in your response)")
def get_current_time() -> str:
    """Get the current date and time in UTC. The result is displayed in a visual clock widget in the UI."""
    from datetime import timezone
    now = datetime.now(timezone.utc)
    # Return ISO format for easy parsing in client
    return now.isoformat()


@ai_function(description="Calculate a mathematical expression")
def calculate(expression: str) -> str:
    """Safely evaluate a mathematical expression."""
    try:
        # Only allow safe mathematical operations
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return "Error: Only basic math operations are allowed"
        result = eval(expression)
        return f"Result: {expression} = {result}"
    except Exception as e:
        return f"Error calculating: {str(e)}"


# Create Azure OpenAI chat client
chat_client = AzureOpenAIChatClient(
    credential=DefaultAzureCredential(),
    endpoint=endpoint,
    deployment_name=deployment_name,
)

# Create a BedTimeStory agent that generates children's bedtime stories
bedtime_story_agent = ChatAgent(
    name="BedTimeStoryTeller",
    description="A creative storyteller that writes engaging bedtime stories for children",
    instructions="""You are a gentle and creative bedtime story teller. 
When given a topic or theme, create a short, soothing bedtime story suitable for children.
Your stories should:
- Be 3-5 paragraphs long
- Have a calming, peaceful tone
- Include a gentle moral or lesson
- End on a peaceful note that encourages sleep
- Be age-appropriate and imaginative""",
    chat_client=chat_client,
)

# Convert the bedtime story agent to a tool
bedtime_story_tool = bedtime_story_agent.as_tool(
    name="tell_bedtime_story",
    description="Generate a calming bedtime story for children based on a given theme or topic",
    arg_name="theme",
    arg_description="The theme or topic for the bedtime story (e.g., 'a brave little rabbit', 'magical forest', 'friendly dragon')",
)

# Create the AI agent with tools
agent = ChatAgent(
    name="AGUIAssistant",
    instructions="""You are a helpful assistant with access to tools.

CRITICAL RULE: Call each tool exactly ONCE per user request. Never call the same tool multiple times.

When the user asks for TIME:
- Call get_current_time ONCE
- Respond with exactly: "⏰" (just the emoji, nothing else)
- The UI shows a visual clock

When the user asks for WEATHER:
- Call get_weather ONCE  
- Add a brief friendly comment about the weather
- The UI shows a visual weather card

For CALCULATIONS:
- Call calculate ONCE
- Explain the result

For BEDTIME STORIES:
- Call tell_bedtime_story ONCE
- Let the story speak for itself

NEVER call a tool more than once per request.""",
    chat_client=chat_client,
    tools=[get_weather, get_current_time, calculate, bedtime_story_tool],
    middleware=[tool_logging_middleware],
)

# Create FastAPI app
app = FastAPI(title="AG-UI Demo Server")

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication middleware using decorator approach
@app.middleware("http")
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
        from starlette.responses import JSONResponse
        return JSONResponse(
            status_code=401,
            content={"detail": "Missing authentication credentials"},
            headers={"WWW-Authenticate": 'Bearer realm="api"'}
        )
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    try:
        await validate_token(token)
        return await call_next(request)
    except HTTPException as e:
        from starlette.responses import JSONResponse
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail},
            headers=e.headers
        )


# Register the AG-UI endpoint
add_agent_framework_fastapi_endpoint(app, agent, "/")


# Health check endpoint (no authentication required)
@app.get("/health")
def health_check():
    """Health check endpoint - no authentication required."""
    return {"status": "ok"}


def main():
    """Run the server."""
    
    
    print("🚀 Starting AG-UI server at http://127.0.0.1:8888")
    
    if ENTRA_TENANT_ID and ENTRA_AUDIENCE:
        print("🔐 Entra ID authentication enabled")
        print(f"   Tenant: {ENTRA_TENANT_ID}")
        print(f"   Audience: {ENTRA_AUDIENCE}")
    else:
        print("⚠️  Entra ID authentication NOT configured (ENTRA_TENANT_ID or ENTRA_AUDIENCE missing)")
    
    print("\nPress Ctrl+C to stop")
    uvicorn.run(app, host="127.0.0.1", port=8888)


if __name__ == "__main__":
    main()
