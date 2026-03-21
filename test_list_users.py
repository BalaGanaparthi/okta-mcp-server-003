#!/usr/bin/env python3
"""Test script to list users in Okta."""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path so we can import the module
sys.path.insert(0, str(Path(__file__).parent / "src"))

from okta_mcp_server.okta_client import OktaClient


async def main():
    """List users from Okta."""
    try:
        # Initialize Okta client (loads from environment variables)
        client = OktaClient()

        print(f"Connected to Okta domain: {client.domain}")
        print("-" * 60)

        # List users
        print("Fetching users from Okta...")
        print("-" * 60)

        users = await client.list_users(limit=20)

        print(f"\n✓ Found {len(users)} users\n")

        # Display users in a formatted table
        print(f"{'ID':<20} {'Email':<30} {'Status':<15} {'Created':<20}")
        print("-" * 85)

        for user in users:
            user_id = user.get("id", "N/A")[:20]
            email = user.get("profile", {}).get("email", "N/A")[:30]
            status = user.get("status", "N/A")[:15]
            created = user.get("created", "N/A")[:20]
            print(f"{user_id:<20} {email:<30} {status:<15} {created:<20}")

        print("-" * 85)
        print(f"\nTotal users: {len(users)}")

        return users

    except Exception as e:
        print(f"✗ Error listing users: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
