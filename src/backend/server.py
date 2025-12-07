"""AG-UI Server - Main entry point."""

import uvicorn
from api import app
from config import (
    SERVER_HOST,
    SERVER_PORT,
    ENTRA_TENANT_ID,
    ENTRA_AUDIENCE,
)


def main():
    """Run the server."""
    print(f"🚀 Starting AG-UI server at http://{SERVER_HOST}:{SERVER_PORT}")
    
    if ENTRA_TENANT_ID and ENTRA_AUDIENCE:
        print("🔐 Entra ID authentication enabled")
        print(f"   Tenant: {ENTRA_TENANT_ID}")
        print(f"   Audience: {ENTRA_AUDIENCE}")
    else:
        print("⚠️  Entra ID authentication NOT configured (ENTRA_TENANT_ID or ENTRA_AUDIENCE missing)")
    
    print("\nPress Ctrl+C to stop")
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)


if __name__ == "__main__":
    main()
