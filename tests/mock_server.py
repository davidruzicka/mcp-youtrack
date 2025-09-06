"""Mock YouTrack server for integration testing."""

import json
import asyncio
import io
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request, File, UploadFile, Form
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn


class MockYouTrackServer:
    """Mock YouTrack server for testing."""
    
    def __init__(self):
        self.app = FastAPI(title="Mock YouTrack API")
        self._initialize_mock_data()
        self.setup_routes()

    def _initialize_mock_data(self):
        """Initialize or reset mock data to initial state."""
        self.data = self._init_mock_data()
        self.attachments_storage: Dict[str, bytes] = {}  # Store binary attachments
    
    def _init_mock_data(self) -> Dict[str, Any]:
        """Initialize mock data."""
        return {
            "issues": {
                "TEST-1": {
                    "id": "TEST-1",
                    "idReadable": "TEST-1",
                    "summary": "Test Issue",
                    "description": "Test issue description",
                    "created": int(datetime.now().timestamp() * 1000),
                    "updated": int(datetime.now().timestamp() * 1000),
                    "resolved": None,
                    "reporter": {
                        "id": "user1",
                        "login": "testuser",
                        "fullName": "Test User"
                    },
                    "assignee": None,
                    "customFields": [
                        {
                            "id": "state-field",
                            "name": "State",
                            "value": {"name": "Open", "id": "open"}
                        },
                        {
                            "id": "priority-field", 
                            "name": "Priority",
                            "value": {"name": "Normal", "id": "normal"}
                        }
                    ],
                    "tags": [],
                    "comments": [
                        {
                            "id": "comment-1",
                            "text": "Test comment",
                            "author": {
                                "id": "user1",
                                "login": "testuser",
                                "fullName": "Test User"
                            },
                            "created": int(datetime.now().timestamp() * 1000),
                            "updated": int(datetime.now().timestamp() * 1000)
                        }
                    ],
                    "attachments": [
                        {
                            "id": "attachment-1",
                            "name": "test-file.txt",
                            "size": 1024,
                            "mimeType": "text/plain",
                            "created": int(datetime.now().timestamp() * 1000),
                            "author": {
                                "id": "user1",
                                "login": "testuser",
                                "fullName": "Test User"
                            },
                            "url": "/issues/TEST-1/attachments/attachment-1"
                        }
                    ],
                    "workItems": []
                },
                "TEST-2": {
                    "id": "TEST-2",
                    "idReadable": "TEST-2", 
                    "summary": "Another Test Issue",
                    "description": "Another test issue",
                    "created": int(datetime.now().timestamp() * 1000),
                    "updated": int(datetime.now().timestamp() * 1000),
                    "resolved": None,
                    "reporter": {
                        "id": "user2",
                        "login": "user2", 
                        "fullName": "User Two"
                    },
                    "assignee": {
                        "id": "user1",
                        "login": "testuser",
                        "fullName": "Test User"
                    },
                    "customFields": [
                        {
                            "id": "state-field",
                            "name": "State", 
                            "value": {"name": "In Progress", "id": "in-progress"}
                        }
                    ],
                    "tags": [{"name": "bug"}],
                    "comments": [],
                    "attachments": [],
                    "workItems": []
                }
            },
            "projects": [
                {
                    "id": "test-project",
                    "name": "Test Project",
                    "shortName": "TEST",
                    "description": "Test project for mock server",
                    "archived": False
                }
            ],
            "comments": {
                "comment-1": {
                    "id": "comment-1",
                    "text": "Test comment",
                    "author": {
                        "id": "user1",
                        "login": "testuser",
                        "fullName": "Test User"
                    },
                    "created": int(datetime.now().timestamp() * 1000),
                    "updated": int(datetime.now().timestamp() * 1000)
                }
            }
        }
    
    def setup_routes(self):
        """Setup FastAPI routes."""

        @self.app.post("/reset")
        async def reset_data():
            """Reset mock data to initial state."""
            print("[MOCK SERVER] Reset endpoint called!")
            with open("/tmp/mockserver_reset.log", "a") as f:
                f.write("reset called\n")
            self.data = self._init_mock_data()
            self.attachments_storage = {}  # Explicitly reset attachments storage
            return {"status": "reset"}

        @self.app.get("/health")
        async def get_issue(issue_id: str, fields: str = None):
            """Get a single issue."""
            if issue_id not in self.data["issues"]:
                raise HTTPException(status_code=404, detail="Issue not found")
            
            issue = self.data["issues"][issue_id].copy()
            
            # Apply field filtering if specified
            if fields:
                filtered_issue = self._apply_fields_filter(issue, fields)
                return filtered_issue
            
            return issue
        
        @self.app.get("/issues/{issue_id}")
        async def get_issue(issue_id: str, fields: str = None):
            """Get a single issue by ID."""
            if issue_id not in self.data["issues"]:
                raise HTTPException(status_code=404, detail="Issue not found")
            
            issue = self.data["issues"][issue_id]
            
            # Apply field filtering if specified
            if fields:
                filtered_issue = self._apply_fields_filter(issue, fields)
                return filtered_issue
            
            return issue

        @self.app.post("/issues/{issue_id}")
        async def update_issue(issue_id: str, request: Request):
            """Update an issue."""
            if issue_id not in self.data["issues"]:
                raise HTTPException(status_code=404, detail="Issue not found")
            
            update_data = await request.json()
            issue = self.data["issues"][issue_id]
            
            # Update fields
            if "summary" in update_data:
                issue["summary"] = update_data["summary"]
            if "description" in update_data:
                issue["description"] = update_data["description"]
            if "customFields" in update_data:
                # Merge custom fields
                for new_field in update_data["customFields"]:
                    for existing_field in issue["customFields"]:
                        if existing_field["name"] == new_field["name"]:
                            existing_field["value"] = new_field["value"]
                            break
                    else:
                        issue["customFields"].append(new_field)
            if "tags" in update_data:
                issue["tags"] = update_data["tags"]
            
            issue["updated"] = int(datetime.now().timestamp() * 1000)
            return issue
        
        @self.app.get("/issues")
        async def list_issues(query: str = None, fields: str = None):
            """List issues."""
            issues = list(self.data["issues"].values())
            
            # Simple query filtering
            if query:
                filtered_issues = []
                for issue in issues:
                    if query.lower() in issue["summary"].lower():
                        filtered_issues.append(issue)
                issues = filtered_issues
            
            # Apply field filtering
            if fields:
                issues = [self._apply_fields_filter(issue, fields) for issue in issues]
            
            return issues
        
        @self.app.get("/issues/{issue_id}/comments")
        async def get_issue_comments(issue_id: str):
            """Get issue comments."""
            if issue_id not in self.data["issues"]:
                raise HTTPException(status_code=404, detail="Issue not found")
            
            return self.data["issues"][issue_id]["comments"]
        
        @self.app.post("/issues/{issue_id}/comments")
        async def add_comment(issue_id: str, request: Request):
            """Add a comment to issue."""
            if issue_id not in self.data["issues"]:
                raise HTTPException(status_code=404, detail="Issue not found")
            
            comment_data = await request.json()
            comment_id = f"comment-{len(self.data['comments']) + 1}"
            
            new_comment = {
                "id": comment_id,
                "text": comment_data.get("text", ""),
                "author": {
                    "id": "user1",
                    "login": "testuser", 
                    "fullName": "Test User"
                },
                "created": int(datetime.now().timestamp() * 1000),
                "updated": int(datetime.now().timestamp() * 1000)
            }
            
            self.data["comments"][comment_id] = new_comment
            self.data["issues"][issue_id]["comments"].append(new_comment)
            
            return new_comment
        
        @self.app.post("/issues/{issue_id}/comments/{comment_id}")
        async def update_comment(issue_id: str, comment_id: str, request: Request):
            """Update a comment."""
            if issue_id not in self.data["issues"]:
                raise HTTPException(status_code=404, detail="Issue not found")
            
            if comment_id not in self.data["comments"]:
                raise HTTPException(status_code=404, detail="Comment not found")
            
            update_data = await request.json()
            comment = self.data["comments"][comment_id]
            
            if "text" in update_data:
                comment["text"] = update_data["text"]
                comment["updated"] = int(datetime.now().timestamp() * 1000)
            
            # Update in issue comments as well
            for issue_comment in self.data["issues"][issue_id]["comments"]:
                if issue_comment["id"] == comment_id:
                    issue_comment.update(comment)
                    break
            
            return comment
        
        @self.app.get("/issues/{issue_id}/timeTracking/workItems")
        async def get_work_items(issue_id: str):
            """Get work items for issue."""
            if issue_id not in self.data["issues"]:
                raise HTTPException(status_code=404, detail="Issue not found")
            
            return self.data["issues"][issue_id]["workItems"]
        
        @self.app.post("/issues/{issue_id}/timeTracking/workItems")
        async def add_work_item(issue_id: str, request: Request):
            """Add work item to issue."""
            if issue_id not in self.data["issues"]:
                raise HTTPException(status_code=404, detail="Issue not found")
            
            work_item_data = await request.json()
            work_item_id = f"work-{len(self.data['issues'][issue_id]['workItems']) + 1}"
            
            new_work_item = {
                "id": work_item_id,
                "duration": work_item_data.get("duration", {"minutes": 60}),
                "date": work_item_data.get("date", int(datetime.now().timestamp() * 1000)),
                "description": work_item_data.get("description", ""),
                "author": {
                    "id": "user1",
                    "login": "testuser",
                    "fullName": "Test User" 
                },
                "type": work_item_data.get("type")
            }
            
            self.data["issues"][issue_id]["workItems"].append(new_work_item)
            return new_work_item
        
        @self.app.get("/admin/projects")
        async def list_projects():
            """List projects."""
            return self.data["projects"]
        
        # Attachment endpoints
        @self.app.get("/issues/{issue_id}/attachments")
        async def get_issue_attachments(issue_id: str):
            """Get issue attachments."""
            if issue_id not in self.data["issues"]:
                raise HTTPException(status_code=404, detail="Issue not found")
            
            return self.data["issues"][issue_id]["attachments"]
        
        @self.app.get("/issues/{issue_id}/attachments/{attachment_id}")
        async def download_attachment(issue_id: str, attachment_id: str):
            """Download attachment binary data."""
            if issue_id not in self.data["issues"]:
                raise HTTPException(status_code=404, detail="Issue not found")
            
            # Find attachment metadata
            attachment = None
            for att in self.data["issues"][issue_id]["attachments"]:
                if att["id"] == attachment_id:
                    attachment = att
                    break
            
            if not attachment:
                raise HTTPException(status_code=404, detail="Attachment not found")
            
            # Get binary data from storage or create mock data
            attachment_key = f"{issue_id}_{attachment_id}"
            if attachment_key in self.attachments_storage:
                content = self.attachments_storage[attachment_key]
            else:
                # Create mock content based on attachment type
                if attachment["mimeType"] == "text/plain":
                    content = b"This is mock text file content for testing."
                elif attachment["mimeType"].startswith("image/"):
                    # Mock image data (1x1 PNG)
                    content = base64.b64decode(
                        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
                    )
                elif attachment["mimeType"] == "application/pdf":
                    # Mock minimal PDF
                    content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n%%EOF"
                else:
                    content = b"Mock binary file content"
                
                self.attachments_storage[attachment_key] = content
            
            def iter_content():
                yield content
            
            return StreamingResponse(
                iter_content(),
                media_type=attachment["mimeType"],
                headers={
                    "Content-Disposition": f'attachment; filename="{attachment["name"]}"',
                    "Content-Length": str(len(content))
                }
            )
        
        @self.app.post("/issues/{issue_id}/attachments")
        async def upload_attachment(issue_id: str, request: Request):
            """Upload attachment to issue."""
            try:
                print(f"Upload request for issue: {issue_id}")
                print(f"Content-Type: {request.headers.get('content-type', 'unknown')}")
                if issue_id not in self.data["issues"]:
                    print(f"Issue {issue_id} not found")
                    # Raise outside try/except so FastAPI handles as 404, not 500
                    raise HTTPException(status_code=404, detail="Issue not found")
                content_type_header = request.headers.get('content-type', '')
                
                if 'application/json' in content_type_header:
                    # Handle JSON request (fallback)
                    print("Handling JSON request...")
                    body = await request.json()
                    file_content = body.get('content', '').encode('utf-8')
                    filename = body.get('name', 'uploaded-file.txt')
                    content_type = body.get('mimeType', 'text/plain')
                    
                elif 'multipart/form-data' in content_type_header:
                    # Handle multipart form data
                    print("Handling multipart request...")
                    form_data = await request.form()
                    print(f"Form keys: {list(form_data.keys())}")
                    
                    # Try to handle different multipart formats
                    if "file" not in form_data:
                        if form_data:
                            first_key = list(form_data.keys())[0]
                            print(f"Using first available key: {first_key}")
                            file_upload = form_data[first_key]
                        else:
                            raise HTTPException(status_code=400, detail="No file provided")
                    else:
                        file_upload = form_data["file"]
                    
                    print(f"File upload type: {type(file_upload)}")
                    
                    # Read file content
                    if hasattr(file_upload, 'read'):
                        file_content = await file_upload.read()
                    else:
                        file_content = file_upload
                    
                    # Get filename
                    filename = getattr(file_upload, 'filename', None) or "uploaded-file"
                    print(f"Filename: {filename}")
                    
                    # Get content type
                    content_type = getattr(file_upload, 'content_type', None) or "application/octet-stream"
                    
                else:
                    # Try to read raw body as last resort
                    print("Unknown content type, trying raw body...")
                    body = await request.body()
                    if body:
                        file_content = body
                        filename = "uploaded-file.bin"
                        content_type = "application/octet-stream"
                    else:
                        raise HTTPException(status_code=400, detail="No content provided")
                
                print(f"File content length: {len(file_content)}")
                print(f"Content type: {content_type}")
                
                # Create attachment metadata
                attachment_id = f"attachment-{len(self.data['issues'][issue_id]['attachments']) + 1}"
                
                new_attachment = {
                    "id": attachment_id,
                    "name": filename,
                    "size": len(file_content),
                    "mimeType": content_type,
                    "created": int(datetime.now().timestamp() * 1000),
                    "author": {
                        "id": "user1",
                        "login": "testuser",
                        "fullName": "Test User"
                    },
                    "url": f"/issues/{issue_id}/attachments/{attachment_id}"
                }
                
                # Store binary content
                attachment_key = f"{issue_id}_{attachment_id}"
                self.attachments_storage[attachment_key] = file_content
                
                # Add to issue
                self.data["issues"][issue_id]["attachments"].append(new_attachment)
                self.data["issues"][issue_id]["updated"] = int(datetime.now().timestamp() * 1000)
                
                print(f"Successfully created attachment: {attachment_id}")
                return new_attachment
                
            except HTTPException:
                # Let FastAPI handle HTTPException (like 404)
                raise
            except Exception as e:
                print(f"Upload error: {e}")
                import traceback
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=str(e))
            
            # Store binary content
            attachment_key = f"{issue_id}_{attachment_id}"
            self.attachments_storage[attachment_key] = file_content
            
            # Add to issue
            self.data["issues"][issue_id]["attachments"].append(new_attachment)
            self.data["issues"][issue_id]["updated"] = int(datetime.now().timestamp() * 1000)
            
            return new_attachment
        
        @self.app.delete("/issues/{issue_id}/attachments/{attachment_id}")
        async def delete_attachment(issue_id: str, attachment_id: str):
            """Delete attachment from issue."""
            if issue_id not in self.data["issues"]:
                raise HTTPException(status_code=404, detail="Issue not found")
            
            issue = self.data["issues"][issue_id]
            
            # Find and remove attachment
            attachment_found = False
            for i, att in enumerate(issue["attachments"]):
                if att["id"] == attachment_id:
                    del issue["attachments"][i]
                    attachment_found = True
                    break
            
            if not attachment_found:
                raise HTTPException(status_code=404, detail="Attachment not found")
            
            # Remove from storage
            attachment_key = f"{issue_id}_{attachment_id}"
            if attachment_key in self.attachments_storage:
                del self.attachments_storage[attachment_key]
            
            issue["updated"] = int(datetime.now().timestamp() * 1000)
            
            return {"message": "Attachment deleted successfully"}
        
        @self.app.exception_handler(404)
        async def not_found_handler(request: Request, exc: HTTPException):
            return JSONResponse(
                status_code=404,
                content={"error": "Not Found", "message": str(exc.detail)}
            )
        
        @self.app.exception_handler(500)
        async def server_error_handler(request: Request, exc: Exception):
            return JSONResponse(
                status_code=500, 
                content={"error": "Internal Server Error", "message": str(exc)}
            )
    
    def _apply_fields_filter(self, data: Dict[str, Any], fields: str) -> Dict[str, Any]:
        """Apply fields filtering to response data."""
        if not fields:
            return data
        
        # Simple fields filtering - in real implementation this would be more complex
        field_list = [f.strip() for f in fields.split(",")]
        filtered_data = {}
        
        # Always include id if present
        if "id" in data:
            filtered_data["id"] = data["id"]
        
        for field in field_list:
            # Handle simple fields
            if field in data:
                filtered_data[field] = data[field]
            elif "(" in field:
                # Handle complex fields like "comments(id,text,author(id,login))"
                field_name = field.split("(")[0]
                if field_name in data:
                    filtered_data[field_name] = data[field_name]
            elif "." in field:
                # Handle nested fields like "author.login"
                parts = field.split(".")
                if len(parts) == 2 and parts[0] in data and isinstance(data[parts[0]], dict):
                    if parts[0] not in filtered_data:
                        filtered_data[parts[0]] = {}
                    if parts[1] in data[parts[0]]:
                        filtered_data[parts[0]][parts[1]] = data[parts[0]][parts[1]]
        
        # Special handling for common fields that might be requested with complex notation
        if "comments" in fields and "comments" in data:
            filtered_data["comments"] = data["comments"]
        if "attachments" in fields and "attachments" in data:
            filtered_data["attachments"] = data["attachments"]
        
        return filtered_data
        
        return filtered_data
    
    async def start(self, host: str = "127.0.0.1", port: int = 8080):
        """Start the mock server."""
        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


async def run_mock_server():
    """Run the mock server."""
    mock_server = MockYouTrackServer()
    print("Starting Mock YouTrack Server on http://127.0.0.1:8080")
    print("Available endpoints:")
    print("  GET    /issues/{issue_id}")
    print("  POST   /issues/{issue_id}")  
    print("  GET    /issues")
    print("  GET    /issues/{issue_id}/attachments")
    print("  GET    /issues/{issue_id}/attachments/{attachment_id}")
    print("  POST   /issues/{issue_id}/attachments")
    print("  DELETE /issues/{issue_id}/attachments/{attachment_id}")
    print("  GET    /admin/projects")
    print("\nSample data available:")
    print("  Issues: TEST-1, TEST-2")
    print("  Attachment: attachment-1 (in TEST-1)")
    await mock_server.start()


if __name__ == "__main__":
    asyncio.run(run_mock_server())
