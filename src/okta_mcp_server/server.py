"""MCP server for Okta user management."""

import os
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from okta_mcp_server.okta_client import OktaClient

# Load environment variables
load_dotenv()

# Global Okta client instance
okta_client: OktaClient | None = None


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


# Create MCP server
mcp = FastMCP("Okta MCP Server", lifespan=lifespan)


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

    # Get the ASGI app for streamable HTTP transport
    app = mcp.streamable_http_app()

    # Run with uvicorn for custom host/port
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
