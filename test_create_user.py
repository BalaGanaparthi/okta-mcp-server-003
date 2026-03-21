#!/usr/bin/env python3
"""Test script to create a user in Okta."""

import asyncio
import sys
from pathlib import Path

# Add src to path so we can import the module
sys.path.insert(0, str(Path(__file__).parent / "src"))

from okta_mcp_server.okta_client import OktaClient


async def main():
    """Create a test user in Okta."""
    try:
        # Initialize Okta client (loads from environment variables)
        client = OktaClient()

        print(f"Connected to Okta domain: {client.domain}")
        print("-" * 50)

        # Create user
        print("Creating user with the following details:")
        print("  Email: testuser@example.com")
        print("  First Name: John")
        print("  Last Name: Doe")
        print("  Activate: True (auto-activate)")
        print("-" * 50)

        user_data = await client.create_user(
            email="testuser@example.com",
            first_name="John",
            last_name="Doe",
            activate=True
        )

        print("\n✓ User created successfully!")
        print("\nUser Details:")
        print(f"  User ID: {user_data.get('id')}")
        print(f"  Email: {user_data.get('profile', {}).get('email')}")
        print(f"  Name: {user_data.get('profile', {}).get('firstName')} {user_data.get('profile', {}).get('lastName')}")
        print(f"  Status: {user_data.get('status')}")
        print(f"  Created: {user_data.get('created')}")
        print(f"  Activated: {user_data.get('activated')}")

        return user_data

    except Exception as e:
        print(f"✗ Error creating user: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
