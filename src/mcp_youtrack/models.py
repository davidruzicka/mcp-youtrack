"""Data models for YouTrack entities."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class Comment:
    """Represents a comment on a YouTrack issue."""
    id: str
    text: str
    author: str
    created: datetime
    updated: Optional[datetime] = None


@dataclass
class Attachment:
    """Represents an attachment on a YouTrack issue."""
    id: str
    name: str
    size: int
    content_type: str
    url: str
    created: datetime
    author: str
    extension: Optional[str] = None


@dataclass
class WorkItem:
    """Represents a work item (time tracking) on a YouTrack issue."""
    id: str
    duration: int  # Duration in milliseconds
    description: str
    date: datetime
    author: str
    type: Optional[str] = None


@dataclass
class IssueFull:
    """Complete issue data including comments, attachments, and work items."""
    id: str
    summary: str
    description: str
    state: str
    priority: str
    assignee: Optional[str]
    created: datetime
    updated: datetime
    comments: List[Comment]
    attachments: List[Attachment]
    work_items: List[WorkItem]
    custom_fields: Dict[str, Any]
    project: Optional[str] = None
    reporter: Optional[str] = None
    tags: Optional[List[str]] = None


@dataclass
class Project:
    """Represents a YouTrack project."""
    id: str
    name: str
    description: Optional[str]
    key: str
    created: datetime
    updated: Optional[datetime] = None
    archived: bool = False


@dataclass
class IssueSummary:
    """Summary information about an issue for listing."""
    id: str
    summary: str
    state: str
    priority: str
    assignee: Optional[str]
    updated: datetime
    project: str


@dataclass
class CreateIssueRequest:
    """Request model for creating a new issue."""
    project: str
    summary: str
    description: str
    priority: str = "Normal"
    assignee: Optional[str] = None
    tags: Optional[List[str]] = None


@dataclass
class UpdateIssueRequest:
    """Request model for updating an existing issue."""
    summary: Optional[str] = None
    description: Optional[str] = None
    state: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    tags: Optional[List[str]] = None


@dataclass
class AddCommentRequest:
    """Request model for adding a comment to an issue."""
    text: str
    author: Optional[str] = None


@dataclass
class AddWorkItemRequest:
    """Request model for adding a work item to an issue."""
    duration: int  # Duration in milliseconds
    description: str
    date: Optional[datetime] = None
    type: Optional[str] = None


@dataclass
class BreakDownStoryRequest:
    """Request model for breaking down a user story into tasks."""
    story_id: str
    tasks: List[CreateIssueRequest]
    link_type: str = "Subtask"  # How to link the tasks to the story
