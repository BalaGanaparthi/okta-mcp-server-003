"""Okta API client for user management operations."""

import os
from typing import Any

import httpx
from pydantic import BaseModel


class OktaUserProfile(BaseModel):
    """Okta user profile data."""

    firstName: str
    lastName: str
    email: str
    login: str | None = None


class OktaClient:
    """HTTP client for Okta REST API."""

    def __init__(
        self,
        domain: str | None = None,
        api_token: str | None = None,
    ):
        """Initialize Okta client.

        Args:
            domain: Okta domain (e.g., dev-12345.okta.com)
            api_token: Okta API token
        """
        self.domain = domain or os.environ.get("OKTA_DOMAIN")
        self.api_token = api_token or os.environ.get("OKTA_API_TOKEN")

        if not self.domain:
            raise ValueError("OKTA_DOMAIN environment variable is required")
        if not self.api_token:
            raise ValueError("OKTA_API_TOKEN environment variable is required")

        self.base_url = f"https://{self.domain}/api/v1"
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"SSWS {self.api_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30.0,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response and raise appropriate errors."""
        if response.status_code >= 400:
            try:
                error_data = response.json()
                error_message = error_data.get("errorSummary", response.text)
            except Exception:
                error_message = response.text
            raise Exception(
                f"Okta API error ({response.status_code}): {error_message}"
            )
        if response.status_code == 204:
            return {"status": "success"}
        return response.json()

    async def create_user(
        self,
        email: str,
        first_name: str,
        last_name: str,
        login: str | None = None,
        activate: bool = True,
    ) -> dict[str, Any]:
        """Create a new Okta user.

        Args:
            email: User's email address
            first_name: User's first name
            last_name: User's last name
            login: User's login (defaults to email if not provided)
            activate: Whether to activate the user immediately

        Returns:
            Created user data
        """
        payload = {
            "profile": {
                "firstName": first_name,
                "lastName": last_name,
                "email": email,
                "login": login or email,
            }
        }

        response = await self._client.post(
            "/users",
            json=payload,
            params={"activate": str(activate).lower()},
        )
        return await self._handle_response(response)

    async def list_users(
        self,
        limit: int = 20,
        search: str | None = None,
        filter_query: str | None = None,
    ) -> list[dict[str, Any]]:
        """List Okta users with optional filtering.

        Args:
            limit: Maximum number of users to return
            search: Search query (searches across multiple fields)
            filter_query: Filter expression (Okta filter syntax)

        Returns:
            List of user data
        """
        params: dict[str, Any] = {"limit": limit}
        if search:
            params["search"] = search
        if filter_query:
            params["filter"] = filter_query

        response = await self._client.get("/users", params=params)
        return await self._handle_response(response)

    async def get_user(self, user_id: str) -> dict[str, Any]:
        """Get a user by ID or login.

        Args:
            user_id: User ID or login email

        Returns:
            User data
        """
        response = await self._client.get(f"/users/{user_id}")
        return await self._handle_response(response)

    async def update_user(
        self,
        user_id: str,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
    ) -> dict[str, Any]:
        """Update a user's profile.

        Args:
            user_id: User ID or login email
            first_name: New first name (optional)
            last_name: New last name (optional)
            email: New email (optional)

        Returns:
            Updated user data
        """
        profile: dict[str, str] = {}
        if first_name is not None:
            profile["firstName"] = first_name
        if last_name is not None:
            profile["lastName"] = last_name
        if email is not None:
            profile["email"] = email

        if not profile:
            raise ValueError("At least one field must be provided for update")

        response = await self._client.post(
            f"/users/{user_id}",
            json={"profile": profile},
        )
        return await self._handle_response(response)

    async def deactivate_user(self, user_id: str) -> dict[str, Any]:
        """Deactivate a user.

        Args:
            user_id: User ID or login email

        Returns:
            Status response
        """
        response = await self._client.post(f"/users/{user_id}/lifecycle/deactivate")
        return await self._handle_response(response)

    async def delete_user(self, user_id: str) -> dict[str, Any]:
        """Delete a user (must be deactivated first).

        Args:
            user_id: User ID or login email

        Returns:
            Status response
        """
        # First deactivate the user (required by Okta)
        try:
            await self.deactivate_user(user_id)
        except Exception as e:
            # User might already be deactivated
            if "already deactivated" not in str(e).lower():
                pass  # Continue with deletion attempt

        # Then delete
        response = await self._client.delete(f"/users/{user_id}")
        return await self._handle_response(response)
