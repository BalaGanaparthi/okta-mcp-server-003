# Okta MCP Server

An MCP (Model Context Protocol) server for Okta user management. This server provides tools for CRUD operations on Okta users and can be deployed to Railway or run locally with Docker.

## Features

- **create_user** - Create a new Okta user
- **list_users** - List users with optional search filtering
- **get_user** - Get user details by ID or login
- **update_user** - Update user profile information
- **delete_user** - Deactivate and delete a user
- **API Key Authentication** - All MCP endpoints protected with `x-api-key` header

## Prerequisites

- Docker and Docker Compose
- Okta developer account with API access
- Okta API token

### Getting an Okta API Token

1. Log in to your Okta Admin Console
2. Navigate to **Security > API > Tokens**
3. Click **Create Token**
4. Give it a name and copy the token value (you won't be able to see it again)

## Local Development

### 1. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
# OKTA_DOMAIN=dev-xxxxx.okta.com
# OKTA_API_TOKEN=00xxxxxxxxxxxxxxxxxx
# MCP_API_KEY=your-secret-api-key
```

### 2. Build and Run with Docker

```bash
# Build and start the server
docker-compose up --build

# The server will be available at http://localhost:8000
```

### 3. Test the Server

```bash
# Check server health (no auth required)
curl http://localhost:8000/health

# Test MCP endpoint (requires x-api-key header)
curl -X POST http://localhost:8000/mcp \
  -H "x-api-key: your-secret-api-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0.0"}}}'
```

### 4. Test with MCP Inspector

```bash
npx @anthropic/mcp-inspector http://localhost:8000/mcp
```

## Railway Deployment

### 1. Push to GitHub

Push this repository to your GitHub account.

### 2. Deploy to Railway

1. Go to [Railway](https://railway.app)
2. Click **New Project** > **Deploy from GitHub repo**
3. Select your repository
4. Railway will auto-detect the Dockerfile

### 3. Configure Environment Variables

In Railway dashboard, add these environment variables:

| Variable         | Description                                   |
| ---------------- | --------------------------------------------- |
| `OKTA_DOMAIN`    | Your Okta domain (e.g., `dev-12345.okta.com`) |
| `OKTA_API_TOKEN` | Your Okta API token                           |
| `MCP_API_KEY`    | Secret API key for client authentication      |

Railway automatically provides the `PORT` variable.

### 4. Get Your Server URL

After deployment, Railway provides a public URL:

```
https://okta-mcp-server-003-production.up.railway.app
```

## Using with Claude Desktop

Add to your Claude Desktop MCP configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "okta": {
      "url": "https://okta-mcp-server-003-production.up.railway.app/mcp",
      "headers": {
        "x-api-key": "your-mcp-api-key"
      }
    }
  }
}
```

For local development:

```json
{
  "mcpServers": {
    "okta": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "x-api-key": "your-mcp-api-key"
      }
    }
  }
}
```

## API Reference

### create_user

Create a new Okta user.

**Parameters:**

- `email` (required): User's email address
- `first_name` (required): User's first name
- `last_name` (required): User's last name
- `login` (optional): User's login (defaults to email)

### list_users

List users with optional filtering.

**Parameters:**

- `limit` (optional): Maximum users to return (default: 20)
- `search` (optional): Search query for filtering

### get_user

Get user by ID or login.

**Parameters:**

- `user_id` (required): User ID or login email

### update_user

Update user profile.

**Parameters:**

- `user_id` (required): User ID or login email
- `first_name` (optional): New first name
- `last_name` (optional): New last name
- `email` (optional): New email address

### delete_user

Deactivate and permanently delete a user.

**Parameters:**

- `user_id` (required): User ID or login email

## Project Structure

```
okta-mcp-server/
├── src/
│   └── okta_mcp_server/
│       ├── __init__.py
│       ├── server.py          # MCP server with tools
│       └── okta_client.py     # Okta API wrapper
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── .env.example
└── README.md
```

## License

MIT
