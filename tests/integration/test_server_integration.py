"""Integration tests for MCP server with mock YouTrack."""

import pytest
import tempfile
import os
from mcp_youtrack.server import MCPServer
from mcp_youtrack.youtrack_client import YouTrackClient
from mcp_youtrack.utils.config import Config


@pytest.mark.asyncio
class TestServerIntegration:
    """Integration tests for MCP server."""
    
    async def test_server_initialization(self, mock_youtrack_base_url, mock_api_token):
        """Test server initialization with mock YouTrack."""
        youtrack_client = YouTrackClient(mock_youtrack_base_url, mock_api_token)
        server = MCPServer(youtrack_client)
        
        assert server.youtrack_client is not None
        assert server.youtrack_client.base_url == mock_youtrack_base_url
        
        await youtrack_client.close()
    
    async def test_get_issue_handler_integration(self, mock_youtrack_base_url, mock_api_token):
        """Test get_issue handler with mock server."""
        youtrack_client = YouTrackClient(mock_youtrack_base_url, mock_api_token)
        server = MCPServer(youtrack_client)
        
        try:
            # Simulate handler call
            result = await server.issues_handler.get_issue({"issue_id": "TEST-1"})
            
            assert result.id == "TEST-1"
            assert result.summary == "Test Issue"
            assert len(result.attachments) == 1
            
        finally:
            await youtrack_client.close()
    
    async def test_update_issue_handler_integration(self, mock_youtrack_base_url, mock_api_token):
        """Test update_issue handler with mock server."""
        youtrack_client = YouTrackClient(mock_youtrack_base_url, mock_api_token)
        server = MCPServer(youtrack_client)
        
        try:
            # Update issue via handler
            result = await server.issues_handler.update_issue({
                "issue_id": "TEST-1",
                "summary": "Integration Test Update",
                "description": "Updated via integration test"
            })
            
            assert result.summary == "Integration Test Update"
            assert result.description == "Updated via integration test"
            
        finally:
            await youtrack_client.close()
    
    async def test_update_comment_handler_integration(self, mock_youtrack_base_url, mock_api_token):
        """Test update_comment handler with mock server."""
        youtrack_client = YouTrackClient(mock_youtrack_base_url, mock_api_token)
        server = MCPServer(youtrack_client)
        
        try:
            # Update comment via handler
            result = await server.comments_handler.update_comment({
                "issue_id": "TEST-1",
                "comment_id": "comment-1",
                "text": "Updated comment via integration test"
            })
            
            assert result.text == "Updated comment via integration test"
            assert result.id == "comment-1"
            
        finally:
            await youtrack_client.close()
    
    async def test_server_serialization_integration(self, mock_youtrack_base_url, mock_api_token):
        """Test server serialization with real data."""
        youtrack_client = YouTrackClient(mock_youtrack_base_url, mock_api_token)
        server = MCPServer(youtrack_client)
        
        try:
            # Get issue and serialize
            issue = await server.issues_handler.get_issue({"issue_id": "TEST-1"})
            serialized = server._serialize_issue(issue)
            
            # Verify serialization includes all expected fields
            assert "id" in serialized
            assert "summary" in serialized
            assert "comments" in serialized
            assert "attachments" in serialized
            assert "work_items" in serialized
            
            # Verify nested objects are serialized properly
            assert len(serialized["comments"]) == 1
            assert isinstance(serialized["comments"][0], dict)
            assert "text" in serialized["comments"][0]
            
            assert len(serialized["attachments"]) == 1  
            assert isinstance(serialized["attachments"][0], dict)
            assert "name" in serialized["attachments"][0]
            
        finally:
            await youtrack_client.close()


@pytest.mark.asyncio  
class TestAttachmentHandlerIntegration:
    """Integration tests for attachment handling through MCP server."""
    
    async def test_attachment_download_integration(self, mock_youtrack_base_url, mock_api_token):
        """Test attachment download through server integration."""
        youtrack_client = YouTrackClient(mock_youtrack_base_url, mock_api_token)
        server = MCPServer(youtrack_client)
        
        try:
            # Get issue with attachment
            issue = await server.issues_handler.get_issue({"issue_id": "TEST-1"})
            assert len(issue.attachments) == 1
            
            attachment = issue.attachments[0]
            assert attachment.name == "test-file.txt"
            assert attachment.size == 1024
            
            # Download attachment content
            content = await youtrack_client.download_attachment("TEST-1", attachment.id)
            assert isinstance(content, bytes)
            assert len(content) > 0
            
        finally:
            await youtrack_client.close()
    
    async def test_attachment_upload_integration(self, mock_youtrack_base_url, mock_api_token):
        """Test attachment upload through server integration."""
        youtrack_client = YouTrackClient(mock_youtrack_base_url, mock_api_token)
        server = MCPServer(youtrack_client)
        
        try:
            # Create test file
            test_content = b"Integration test attachment content"
            
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as temp_file:
                temp_file.write(test_content)
                temp_file_path = temp_file.name
            
            try:
                # Upload attachment
                attachment_response = await youtrack_client.upload_attachment("TEST-1", temp_file_path)
                
                assert hasattr(attachment_response, "id")
                assert attachment_response.size == len(test_content)
                
                # Verify upload by getting updated issue
                issue = await server.issues_handler.get_issue({"issue_id": "TEST-1"})
                assert len(issue.attachments) == 2  # Original + uploaded
                
                # Find uploaded attachment
                uploaded_attachment = None
                for att in issue.attachments:
                    if att.id == attachment_response.id:
                        uploaded_attachment = att
                        break
                
                assert uploaded_attachment is not None
                assert uploaded_attachment.size == len(test_content)
                
            finally:
                os.unlink(temp_file_path)
                
        finally:
            await youtrack_client.close()
    
    async def test_issue_with_multiple_attachments(self, mock_youtrack_base_url, mock_api_token):
        """Test handling issue with multiple attachments."""
        youtrack_client = YouTrackClient(mock_youtrack_base_url, mock_api_token)
        server = MCPServer(youtrack_client)
        
        try:
            # Upload multiple attachments to TEST-2
            temp_files = []
            
            for i in range(3):
                content = f"Test file {i} content".encode()
                
                temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix=f'-{i}.txt', delete=False)
                temp_file.write(content)
                temp_file.close()
                temp_files.append(temp_file.name)
                
                await youtrack_client.upload_attachment("TEST-2", temp_file.name)
            
            try:
                # Get issue and verify all attachments
                issue = await server.issues_handler.get_issue({"issue_id": "TEST-2"})
                assert len(issue.attachments) == 3
                
                # Verify serialization handles multiple attachments
                serialized = server._serialize_issue(issue)
                assert len(serialized["attachments"]) == 3
                
                for att_data in serialized["attachments"]:
                    assert "id" in att_data
                    assert "name" in att_data
                    assert "size" in att_data
                    assert "content_type" in att_data
                    
            finally:
                # Clean up temp files
                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                
        finally:
            await youtrack_client.close()
    
    async def test_attachment_error_handling(self, mock_youtrack_base_url, mock_api_token):
        """Test attachment error handling integration."""
        youtrack_client = YouTrackClient(mock_youtrack_base_url, mock_api_token)
        server = MCPServer(youtrack_client)
        
        try:
            # Test download non-existent attachment
            with pytest.raises(Exception):
                await youtrack_client.download_attachment("TEST-1", "non-existent-attachment")
            
            # Test upload to non-existent issue
            test_content = b"test"
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as temp_file:
                temp_file.write(test_content)
                temp_file_path = temp_file.name
            
            try:
                with pytest.raises(Exception):
                    await youtrack_client.upload_attachment("NONEXISTENT-1", temp_file_path)
            finally:
                os.unlink(temp_file_path)
                
        finally:
            await youtrack_client.close()
