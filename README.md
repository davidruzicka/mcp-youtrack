# MCP YouTrack Server

A Model Context Protocol (MCP) server implementation for JetBrains YouTrack integration, enabling coding agents to interact with YouTrack instances for issue management, comments, attachments, and work tracking.

## Features

- **Complete Issue Management**: Retrieve full issue data including comments, attachments, and work items
- **Attachment Handling**: Download and upload attachments to issues
- **Comment Management**: Add and retrieve comments on issues
- **Work Item Tracking**: Manage time tracking and work items
- **Project Management**: List and manage YouTrack projects
- **Multiple Transport Options**: Support for stdio and HTTP streaming transports

## Architecture

The server is built with a modular architecture:

```
mcp-youtrack/
├── src/mcp_youtrack/
│   ├── server.py              # Main MCP server implementation
│   ├── youtrack_client.py     # YouTrack REST API client
│   ├── models.py              # Data models for YouTrack entities
│   ├── handlers/              # MCP tool handlers
│   │   ├── issues.py          # Issue management tools
│   │   ├── comments.py        # Comment management tools
│   │   ├── work.py            # Work item management tools
│   │   └── projects.py        # Project management tools
│   └── utils/                 # Utility functions and configuration
├── tests/                     # Comprehensive test suite
└── examples/                  # Usage examples
```

## Installation

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- YouTrack instance with API access

### Setup

1. Clone the repository:
```bash
git clone https://github.com/davidruzicka/mcp-youtrack.git
cd mcp-youtrack
```

2. Install dependencies:
```bash
poetry install
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your YouTrack configuration
```

## Configuration

### Environment Variables

- `YOUTRACK_URL`: Base URL of your YouTrack instance
- `YOUTRACK_API_TOKEN`: API token for authentication
- `MCP_TRANSPORT`: Transport type (`stdio` or `http`)
- `MCP_HOST`: Host for HTTP transport (default: `localhost`)
- `MCP_PORT`: Port for HTTP transport (default: `8000`)

### Example Configuration

```bash
YOUTRACK_URL=https://youtrack.company.com
YOUTRACK_API_TOKEN=your_api_token_here
MCP_TRANSPORT=stdio
```

## Usage

### Running the Server

#### STDIO Transport (for local development)

```bash
poetry run python -m mcp_youtrack.server
```

#### HTTP Transport

```bash
poetry run python -m mcp_youtrack.server --transport http --host 0.0.0.0 --port 8000
```

### Available MCP Tools

#### `youtrack.get_issue`

Retrieve complete issue data including comments, attachments, and work items.

**Parameters:**
- `issue_id` (required): ID of the issue to retrieve
- `include_comments` (optional): Whether to include comments (default: true)
- `include_attachments` (optional): Whether to include attachments (default: true)
- `include_work_items` (optional): Whether to include work items (default: true)

**Example:**
```json
{
  "issue_id": "PROJ-123",
  "include_comments": true,
  "include_attachments": true,
  "include_work_items": true
}
```

**Response:**
```json
{
  "id": "PROJ-123",
  "summary": "Bug in login form",
  "description": "Users cannot log in with valid credentials",
  "state": "Open",
  "priority": "High",
  "assignee": "developer1",
  "comments": [...],
  "attachments": [...],
  "work_items": [...]
}
```

#### `youtrack.list_issues`

List issues with optional filtering.

**Parameters:**
- `project` (optional): Project key to filter by
- `state` (optional): State to filter by
- `assignee` (optional): Assignee to filter by
- `limit` (optional): Maximum number of issues (default: 50)
- `offset` (optional): Number of issues to skip (default: 0)

#### `youtrack.download_attachment`

Download attachment content.

**Parameters:**
- `issue_id` (required): ID of the issue
- `attachment_id` (required): ID of the attachment

#### `youtrack.upload_attachment`

Upload a new attachment to an issue.

**Parameters:**
- `issue_id` (required): ID of the issue
- `filename` (required): Name of the file
- `content` (required): File content as base64 encoded string

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_youtrack_client.py

# Run with coverage
poetry run pytest --cov=mcp_youtrack
```

### Code Quality

```bash
# Format code
poetry run black src/ tests/

# Sort imports
poetry run isort src/ tests/

# Type checking
poetry run mypy src/
```

### Test-Driven Development

This project follows TDD principles:

1. **Write failing tests first** - Tests define the expected behavior
2. **Implement minimal code** - Write just enough code to make tests pass
3. **Refactor** - Clean up the code while keeping tests green
4. **Repeat** - Continue the cycle for new features

## API Reference

### YouTrack Client

The `YouTrackClient` class provides low-level access to YouTrack REST API:

```python
from mcp_youtrack.youtrack_client import YouTrackClient

client = YouTrackClient(
    base_url="https://youtrack.company.com",
    api_token="your_token",
    timeout=30.0
)

# Get complete issue
issue = await client.get_issue_full("PROJ-123")

# Download attachment
content = await client.download_attachment("PROJ-123", "att_1")

# Upload attachment
attachment = await client.upload_attachment("PROJ-123", "screenshot.png", content)
```

### Data Models

All YouTrack entities are represented as Python dataclasses:

- `IssueFull`: Complete issue data
- `Comment`: Issue comment
- `Attachment`: File attachment
- `WorkItem`: Time tracking entry
- `Project`: YouTrack project

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

CMD ["python", "-m", "mcp_youtrack.server"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  mcp-youtrack:
    build: .
    environment:
      - YOUTRACK_URL=${YOUTRACK_URL}
      - YOUTRACK_API_TOKEN=${YOUTRACK_API_TOKEN}
      - MCP_TRANSPORT=http
      - MCP_HOST=0.0.0.0
      - MCP_PORT=8000
    ports:
      - "8000:8000"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Implement the feature
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Roadmap


## Roadmap

### Implementováno
- [x] HTTP streaming transport endpoint (`/mcp/stream`) a základní testování
- [x] Kompletní testovací izolace a refaktor integračních testů
- [x] Attachment upload/download včetně binárních a velkých souborů
- [x] Komplexní CRUD integrační testy
- [x] Pokrytí testů pomocí pytest-cov

### Další kroky (priorita)
- [ ] Automatizovaná bezpečnostní kontrola pomocí Trivy (security scan)
  - Lokálně: `trivy fs .`
  - V CI: přidat Trivy scan do workflow (např. GitHub Actions)
- [ ] Authentication via HTTP headers for remote access
- [ ] Issue creation and update tools
- [ ] Story breakdown automation
- [ ] Git commit integration
- [ ] Bulk operations support
- [ ] Advanced search and filtering
- [ ] Webhook support for real-time updates
- [ ] Performance optimization and caching
- [ ] Comprehensive error handling and logging
