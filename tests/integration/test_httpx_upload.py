"""Test multipart upload directly with httpx."""

import tempfile
import os
import httpx
import pytest


@pytest.mark.asyncio
async def test_direct_httpx_multipart_upload(mock_youtrack_base_url):
    """Test uploading file directly with httpx multipart."""
    # Create temporary text file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Direct httpx test content\nMultiple lines\n")
        temp_file_path = f.name
    
    try:
        async with httpx.AsyncClient() as client:
            # Prepare multipart form data the same way as YouTrackClient
            with open(temp_file_path, 'rb') as f:
                file_content = f.read()
            
            filename = os.path.basename(temp_file_path)
            files = {"file": (filename, file_content, "text/plain")}
            
            print(f"Uploading file: {filename}")
            print(f"Content length: {len(file_content)}")
            
            response = await client.post(
                f"{mock_youtrack_base_url}/issues/TEST-1/attachments",
                files=files
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response content: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Upload successful: {data}")
                assert "id" in data
                assert data["name"] == filename
            else:
                print(f"Upload failed with status {response.status_code}: {response.text}")
                
    finally:
        os.unlink(temp_file_path)
