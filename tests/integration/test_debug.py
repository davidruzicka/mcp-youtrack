"""Debug test to see what YouTrackClient returns."""

import pytest
from mcp_youtrack.youtrack_client import YouTrackClient


@pytest.mark.asyncio
async def test_debug_youtrack_client(mock_youtrack_base_url, mock_api_token):
    """Debug test to see what YouTrackClient returns."""
    async with YouTrackClient(mock_youtrack_base_url, mock_api_token) as client:
        issue = await client.get_issue_full("TEST-1")
        
        print(f"Issue: {issue}")
        print(f"Comments count: {len(issue.comments)}")
        print(f"Comments: {issue.comments}")
        print(f"Attachments count: {len(issue.attachments)}")
        print(f"Attachments: {issue.attachments}")
        
        # Let's also test the raw response
        import httpx
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(f"{mock_youtrack_base_url}/issues/TEST-1")
            raw_data = response.json()
            print(f"Raw data comments: {raw_data.get('comments', [])}")
            print(f"Raw data attachments: {raw_data.get('attachments', [])}")
        
        assert issue is not None
