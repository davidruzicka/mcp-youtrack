# Setup Instructions for MCP YouTrack Server

## Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- YouTrack instance URL
- YouTrack API token

## Step 1: Get YouTrack API Token

1. Go to your YouTrack instance URL
2. Log in to your account
3. Go to **Settings** → **Personal** → **Access Tokens**
4. Click **Create Token**
5. Give it a name (e.g., "MCP Server")
6. Copy the generated token (you won't see it again!)

## Step 2: Configure Environment

Create a `.env` file in the project root:

```bash
# YouTrack Configuration
YOUTRACK_URL=<your_youtrack_url>
YOUTRACK_API_TOKEN=<your_actual_api_token_here>

# MCP Transport Configuration
MCP_TRANSPORT=stdio

# Optional: Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

**Important**: Replace `<your_youtrack_url>` with your YouTrack instance URL  `<your_actual_api_token_here>` with the token you copied from YouTrack.

## Step 3: Test Connection

Run the test script to verify your configuration:

```bash
# Make the script executable
chmod +x test_youtrack_api.py

# Run the test
python test_youtrack_api.py
```

You should see output like:
```
🔍 Testing YouTrack API Connection
==================================================
📁 Found .env file
✅ YOUTRACK_API_TOKEN is configured
Configuration loaded: Config(youtrack_url=<your_youtrack_url>, ...)
Connecting to YouTrack at: <your_youtrack_url>
Testing connection...
✅ Successfully connected to YouTrack!
Found 3 projects:
  - PROJ: My Project
  - TEST: Test Project
🎉 All tests passed! YouTrack API is working correctly.
```

## Step 4: Run Tests

```bash
# Run all tests
poetry run pytest

# Run only unit tests (no API calls)
poetry run pytest -m "not integration"

# Run integration tests (requires API token)
poetry run pytest -m integration

# Run specific test file
poetry run pytest tests/test_youtrack_client.py
```

## Step 5: Start MCP Server

### STDIO Transport (for local development)
```bash
poetry run python -m mcp_youtrack
```

### HTTP Transport (for remote access)
```bash
# Set transport to HTTP in .env
MCP_TRANSPORT=http
MCP_HOST=localhost
MCP_PORT=8000

# Start server
poetry run python -m mcp_youtrack
```

The server will be available at `http://localhost:8000`

## Troubleshooting

### "YOUTRACK_API_TOKEN environment variable is required"
- Make sure you created the `.env` file
- Check that the token is not empty
- Verify the file is in the project root directory

### "Connection failed"
- Verify your API token is correct
- Check network connectivity to <your_youtrack_url>
- Ensure your YouTrack account has API access

### "Invalid MCP_TRANSPORT"
- Make sure `MCP_TRANSPORT` is either `stdio` or `http`

### Import errors
- Make sure you're running from the project root
- Verify Poetry dependencies are installed: `poetry install`

## API Endpoints (HTTP Transport)

When running in HTTP mode, the server provides these endpoints:

- `GET /` - Server information
- `GET /health` - Health check
- `POST /mcp/tools` - List available MCP tools
- `POST /mcp/call` - Call an MCP tool
- `GET /mcp/stream` - Server-Sent Events stream

## MCP Tools Available

- `youtrack.get_issue` - Get complete issue data
- `youtrack.list_issues` - List issues with filtering
- `youtrack.download_attachment` - Download attachment
- `youtrack.upload_attachment` - Upload attachment

## Next Steps

1. **Test with real data**: Try getting issues from your projects
2. **Implement missing tools**: Add issue creation, updates, etc.
3. **Add authentication**: Implement HTTP header-based auth for remote access
4. **Deploy**: Set up CI/CD and deployment pipeline

## Security Notes

- Never commit your `.env` file to version control
- Keep your API token secure
- Consider using environment variables in production
- The `.env` file is already in `.gitignore`
