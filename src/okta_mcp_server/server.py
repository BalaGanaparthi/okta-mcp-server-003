"""MCP server for Okta user management."""

import os
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from okta_mcp_server.okta_client import OktaClient

# Load environment variables
load_dotenv()


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce API key authentication via x-api-key header."""

    def __init__(self, app, api_key: str, exclude_paths: list[str] | None = None):
        super().__init__(app)
        self.api_key = api_key
        self.exclude_paths = exclude_paths or []

    async def dispatch(self, request: Request, call_next):

        await printRequest(request)

        # Skip auth for excluded paths (e.g., /health)
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Check x-api-key/authorization header
        provided_key = request.headers.get("x-api-key")
        if not provided_key:
            # ServiceNow sends apikey in authorization header
            provided_key = request.headers.get("authorization")
            if not provided_key:
                return JSONResponse(
                    {"error": "Unauthorized", "message": "Missing x-api-key header"},
                    status_code=401,
                )
        if provided_key != self.api_key:
            return JSONResponse(
                {"error": "Forbidden", "message": "Invalid API key"},
                status_code=403,
            )

        return await call_next(request)

# Global Okta client instance
okta_client: OktaClient | None = None

async def printRequest(request):
    print(f'{request.method} {str(request.url)}\n---')
    print('Headers:')
    for key, value in request.headers.items():
        print(f"  {key}: {value}")
    try:
        body = await request.body()
        print(f'Body: {body.decode() if body else "(empty)"}\n---')
    except Exception as e:
        print(f'Body: (could not read: {e})\n---')
    print('Query Parameters:')
    for key, value in request.query_params.items():
        print(f"  {key}: {value}")

@asynccontextmanager
async def lifespan(server: FastMCP):
    """Manage Okta client lifecycle."""
    global okta_client
    okta_client = OktaClient()
    try:
        yield
    finally:
        if okta_client:
            await okta_client.close()


# Create MCP server with transport security configured for Railway
# Disable DNS rebinding protection since Railway proxy handles security
transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=False,
)
mcp = FastMCP("Okta MCP Server", lifespan=lifespan, transport_security=transport_security)


# Health check endpoint
@mcp.custom_route("/health", methods=["GET"])
async def health(request):
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "ok", "service": "okta-mcp-server"})


@mcp.tool()
async def create_user(
    email: str,
    first_name: str,
    last_name: str,
    login: str | None = None,
) -> dict[str, Any]:
    """Create a new Okta user.

    Args:
        email: User's email address
        first_name: User's first name
        last_name: User's last name
        login: User's login (defaults to email if not provided)

    Returns:
        Created user data including ID and status
    """
    if not okta_client:
        raise RuntimeError("Okta client not initialized")

    result = await okta_client.create_user(
        email=email,
        first_name=first_name,
        last_name=last_name,
        login=login,
    )
    return {
        "id": result.get("id"),
        "status": result.get("status"),
        "profile": result.get("profile"),
        "created": result.get("created"),
    }


@mcp.tool()
async def list_users(
    limit: int = 20,
    search: str | None = None,
) -> list[dict[str, Any]]:
    """List Okta users with optional filtering.

    Args:
        limit: Maximum number of users to return (default: 20)
        search: Search query to filter users (searches name, email, login)

    Returns:
        List of users with their basic information
    """
    if not okta_client:
        raise RuntimeError("Okta client not initialized")

    users = await okta_client.list_users(limit=limit, search=search)

    # Return simplified user data
    return [
        {
            "id": user.get("id"),
            "status": user.get("status"),
            "profile": {
                "firstName": user.get("profile", {}).get("firstName"),
                "lastName": user.get("profile", {}).get("lastName"),
                "email": user.get("profile", {}).get("email"),
                "login": user.get("profile", {}).get("login"),
            },
            "created": user.get("created"),
            "lastLogin": user.get("lastLogin"),
        }
        for user in users
    ]


@mcp.tool()
async def get_user(user_id: str) -> dict[str, Any]:
    """Get an Okta user by ID or login.

    Args:
        user_id: User ID or login email

    Returns:
        User data including profile and status
    """
    if not okta_client:
        raise RuntimeError("Okta client not initialized")

    user = await okta_client.get_user(user_id)
    return {
        "id": user.get("id"),
        "status": user.get("status"),
        "profile": user.get("profile"),
        "created": user.get("created"),
        "lastLogin": user.get("lastLogin"),
        "lastUpdated": user.get("lastUpdated"),
    }


@mcp.tool()
async def update_user(
    user_id: str,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
) -> dict[str, Any]:
    """Update an Okta user's profile.

    Args:
        user_id: User ID or login email
        first_name: New first name (optional)
        last_name: New last name (optional)
        email: New email address (optional)

    Returns:
        Updated user data
    """
    if not okta_client:
        raise RuntimeError("Okta client not initialized")

    user = await okta_client.update_user(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
    )
    return {
        "id": user.get("id"),
        "status": user.get("status"),
        "profile": user.get("profile"),
        "lastUpdated": user.get("lastUpdated"),
    }


@mcp.tool()
async def delete_user(user_id: str) -> dict[str, Any]:
    """Deactivate and delete an Okta user.

    This will first deactivate the user (if active) and then permanently
    delete them from Okta. This action cannot be undone.

    Args:
        user_id: User ID or login email

    Returns:
        Deletion status
    """
    if not okta_client:
        raise RuntimeError("Okta client not initialized")

    await okta_client.delete_user(user_id)
    return {
        "status": "deleted",
        "user_id": user_id,
        "message": "User has been deactivated and deleted",
    }


def main():
    """Run the MCP server."""
    import uvicorn

    port = int(os.environ.get("PORT", 8000))

    # Get API key from environment (required)
    api_key = os.environ.get("MCP_API_KEY")
    if not api_key:
        raise ValueError("MCP_API_KEY environment variable is required")

    # Get the ASGI app for streamable HTTP transport
    app = mcp.streamable_http_app()

    # Wrap with API key authentication middleware
    # Exclude /health endpoint for monitoring/health checks
    app = APIKeyAuthMiddleware(app, api_key, exclude_paths=["/health"])

    # Run with uvicorn for custom host/port
    # proxy_headers and forwarded_allow_ips for Railway reverse proxy
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
