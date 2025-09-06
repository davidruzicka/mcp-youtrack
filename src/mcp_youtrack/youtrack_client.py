"""YouTrack API client for MCP server."""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from urllib.parse import urljoin

import httpx
from httpx import HTTPStatusError

from .models import (
    IssueFull, Comment, Attachment, WorkItem, Project,
    CreateIssueRequest, UpdateIssueRequest, AddCommentRequest,
    AddWorkItemRequest
)


class YouTrackClient:

    """HTTP client for interacting with YouTrack REST API."""

    def __init__(
        self,
        base_url: str,
        api_token: str,
        timeout: float = 30.0
    ):
        """Initialize YouTrack client.
        
        Args:
            base_url: Base URL of YouTrack instance
            api_token: API token for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.timeout = timeout
        
        # Setup headers for authentication
        # Prepare headers - don't set Content-Type globally to allow multipart uploads
        self._headers = {
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json"
        }
        
        # Create HTTP client
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers,
            timeout=timeout
        )

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def _parse_datetime(self, dt_value) -> datetime:
        """Parse datetime from YouTrack API response."""
        if isinstance(dt_value, str):
            # Handle ISO string format
            return datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
        elif isinstance(dt_value, (int, float)):
            # Handle timestamp in milliseconds
            return datetime.fromtimestamp(dt_value / 1000.0)
        else:
            raise ValueError(f"Unsupported datetime format: {dt_value}")

    def _parse_assignee(self, assignee_data: Optional[Dict[str, Any]]) -> Optional[str]:
        """Parse assignee data from YouTrack API response."""
        if not assignee_data:
            return None
        return assignee_data.get("name") or assignee_data.get("login")

    def _parse_comments(self, comments_data: List[Dict[str, Any]]) -> List[Comment]:
        """Parse comments data from YouTrack API response."""
        comments = []
        for comment_data in comments_data:
            comment = Comment(
                id=comment_data["id"],
                text=comment_data["text"],
                author=comment_data["author"]["login"],
                created=self._parse_datetime(comment_data["created"]),
                updated=self._parse_datetime(comment_data["updated"]) if comment_data.get("updated") else None
            )
            comments.append(comment)
        return comments

    def _parse_attachments(self, attachments_data: List[Dict[str, Any]]) -> List[Attachment]:
        """Parse attachments data from YouTrack API response."""
        attachments = []
        for att_data in attachments_data:
            attachment = Attachment(
                id=att_data["id"],
                name=att_data["name"],
                size=att_data["size"],
                content_type=att_data.get("mimeType", "application/octet-stream"),
                extension=att_data.get("extension"),
                url=att_data["url"],
                created=self._parse_datetime(att_data["created"]),
                author=att_data["author"]["login"]
            )
            attachments.append(attachment)
        return attachments

    def _parse_work_items(self, work_items_data: List[Dict[str, Any]]) -> List[WorkItem]:
        """Parse work items data from YouTrack API response."""
        work_items = []
        for work_data in work_items_data:
            work_item = WorkItem(
                id=work_data["id"],
                duration=work_data["duration"],
                description=work_data["description"],
                date=self._parse_datetime(work_data["date"]),
                author=work_data["author"]["login"],
                type=work_data.get("type")
            )
            work_items.append(work_item)
        return work_items

    async def get_issue_full(self, issue_id: str) -> IssueFull:
        """Get complete issue data including comments, attachments, and work items.
        
        Args:
            issue_id: ID of the issue to retrieve
            
        Returns:
            Complete issue data
            
        Raises:
            HTTPStatusError: If the issue is not found or server error occurs
        """
        url = f"/issues/{issue_id}"
        params = {
            "fields": "id,summary,description,created,updated,"
                     "comments(id,text,author(id,login),created,updated,attachments),"
                     "attachments(id,name,size,extension,mimeType,created,author(id,login),url),"
                     "timeTracking,"
                     "customFields,project(id,name,shortName),reporter(id,login)"
        }
        
        response = await self._client.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        return IssueFull(
            id=data["id"],
            summary=data["summary"],
            description=data.get("description", ""),
            state="Unknown",  # Will be extracted from customFields if available
            priority="Normal",  # Will be extracted from customFields if available
            assignee=None,  # Will be extracted from customFields if available
            created=self._parse_datetime(data["created"]),
            updated=self._parse_datetime(data["updated"]),
            comments=self._parse_comments(data.get("comments", [])),
            attachments=self._parse_attachments(data.get("attachments", [])),
            work_items=self._parse_work_items(data.get("timeTracking", {}).get("workItems", [])),
            custom_fields=data.get("customFields", {}),
            project=data.get("project", {}).get("shortName") if data.get("project") else None,
            reporter=data.get("reporter", {}).get("login") if data.get("reporter") else None,
            tags=[]  # Will be extracted from customFields if available
        )

    async def download_attachment(self, issue_id: str, attachment_id: str) -> bytes:
        """Download attachment content.
        
        Args:
            issue_id: ID of the issue
            attachment_id: ID of the attachment
            
        Returns:
            Attachment content as bytes
            
        Raises:
            HTTPStatusError: If the attachment is not found or server error occurs
        """
        url = f"/issues/{issue_id}/attachments/{attachment_id}"
        response = await self._client.get(url)
        response.raise_for_status()
        return response.content

    async def upload_attachment(self, issue_id: str, filename: str, content: bytes = None) -> Attachment:
        """Upload an attachment to an issue. Accepts either file_path or (filename, content)."""
        import os
        import mimetypes
        url = f"/issues/{issue_id}/attachments"
        if content is None:
            # filename is actually a file_path
            file_path = filename
            with open(file_path, 'rb') as f:
                file_content = f.read()
            filename = os.path.basename(file_path)
        else:
            file_content = content
        content_type, _ = mimetypes.guess_type(filename)
        if content_type is None:
            content_type = 'application/octet-stream'
        files = {"file": (filename, file_content, content_type)}
        response = await self._client.post(url, files=files)
        response.raise_for_status()
        data = response.json()
        # Vracíme Attachment dataclass
        return Attachment(
            id=data["id"],
            name=data["name"],
            size=data["size"],
            content_type=data.get("mimeType") or data.get("contentType", "application/octet-stream"),
            url=data["url"],
            created=self._parse_datetime(data["created"]),
            author=(data["author"].get("login") or data["author"].get("name") if data.get("author") else None),
            extension=data.get("extension")
        )

    async def get_comments(self, issue_id: str) -> List[Comment]:
        """Get all comments for an issue.
        
        Args:
            issue_id: ID of the issue
            
        Returns:
            List of comments
        """
        url = f"/api/issues/{issue_id}/comments"
        response = await self._client.get(url)
        response.raise_for_status()
        
        data = response.json()
        return self._parse_comments(data)

    async def add_comment(self, issue_id: str, comment_data: Union[str, Dict[str, Any]]) -> Comment:
        """Add a new comment to an issue.
        
        Args:
            issue_id: ID of the issue
            comment_data: Comment text (str) or comment data dict with 'text' field
            
        Returns:
            Created comment as Comment
        """
        url = f"/issues/{issue_id}/comments"
        
        # If comment_data is a string, wrap it in a dict
        if isinstance(comment_data, str):
            comment_data = {"text": comment_data}
        
        response = await self._client.post(url, json=comment_data)
        response.raise_for_status()
        data = response.json()
        return Comment(
            id=data["id"],
            text=data["text"],
            author=(data["author"].get("login") or data["author"].get("name") if data.get("author") else None),
            created=self._parse_datetime(data["created"]),
            updated=self._parse_datetime(data["updated"]) if data.get("updated") else None
        )

    async def get_work_items(self, issue_id: str) -> List[WorkItem]:
        """Get all work items for an issue.
        
        Args:
            issue_id: ID of the issue
            
        Returns:
            List of work items as WorkItem
        """
        url = f"/issues/{issue_id}/timeTracking/workItems"
        response = await self._client.get(url)
        response.raise_for_status()
        data = response.json()
        return self._parse_work_items(data)

    async def add_work_item(self, issue_id: str, work_item_data: Dict[str, Any]) -> WorkItem:
        """Add a new work item to an issue.
        
        Args:
            issue_id: ID of the issue
            work_item_data: Work item data
            
        Returns:
            Created work item as WorkItem
        """
        url = f"/issues/{issue_id}/timeTracking/workItems"
        
        response = await self._client.post(url, json=work_item_data)
        response.raise_for_status()
        data = response.json()
        return WorkItem(
            id=data["id"],
            duration=data["duration"],
            description=data["description"],
            date=self._parse_datetime(data["date"]),
            author=(data["author"].get("login") or data["author"].get("name") if data.get("author") else None),
            type=data.get("type")
        )

    async def list_projects(self) -> List[Project]:
        """Get list of all projects.
        
        Returns:
            List of projects
        """
        url = "/admin/projects"
        params = {
            "fields": "id,name,shortName,archived"
        }
        response = await self._client.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        projects = []
        
        for project_data in data:
            project = Project(
                id=project_data["id"],
                name=project_data["name"],
                description=None,  # Not available in basic fields
                key=project_data["shortName"],
                created=datetime.now(),  # Not available in basic fields
                updated=None,  # Not available in basic fields
                archived=project_data.get("archived", False)
            )
            projects.append(project)
        
        return projects

    async def update_issue(self, issue_id: str, update_data: Dict[str, Any]) -> None:
        """Update an existing issue in YouTrack."""
        url = f"/issues/{issue_id}"
        payload = {}
        # Map MCP fields to YouTrack fields
        if "summary" in update_data:
            payload["summary"] = update_data["summary"]
        if "description" in update_data:
            payload["description"] = update_data["description"]
        if "state" in update_data:
            payload.setdefault("customFields", []).append({"name": "State", "value": {"name": update_data["state"]}})
        if "priority" in update_data:
            payload.setdefault("customFields", []).append({"name": "Priority", "value": {"name": update_data["priority"]}})
        if "assignee" in update_data:
            payload.setdefault("customFields", []).append({"name": "Assignee", "value": {"login": update_data["assignee"]}})
        if "tags" in update_data:
            payload["tags"] = [{"name": tag} for tag in update_data["tags"]]
        # Only send PATCH if there is something to update
        if not payload:
            return
        response = await self._client.post(url, json=payload)
        response.raise_for_status()

    async def update_comment(self, issue_id: str, comment_id: str, text: str) -> Comment:
        """Update a comment on an issue."""
        url = f"/issues/{issue_id}/comments/{comment_id}"
        payload = {"text": text}
        response = await self._client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return Comment(
            id=data["id"],
            text=data["text"],
            author=data["author"]["login"] if "author" in data and data["author"] else None,
            created=self._parse_datetime(data["created"]),
            updated=self._parse_datetime(data["updated"]) if data.get("updated") else None
        )
