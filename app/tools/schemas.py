from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class SearchDocsInput(BaseModel):
    query: str = Field(description="Search keywords, concepts, or question about internal runbooks, architecture, or policies")
    top_k: int = Field(default=3, ge=1, le=5, description="Maximum number of document excerpts to return")


class GetServiceInput(BaseModel):
    service_name_or_id: str = Field(description="Service name or ID (e.g. 'checkout-api', 'svc-payment-gw', 'fraud-detector')")


class ListOpenPRsInput(BaseModel):
    service_id: Optional[str] = Field(default=None, description="Optional service ID to filter open PRs (e.g. 'svc-checkout-api')")


class GetPRInput(BaseModel):
    pr_number: int = Field(description="Pull request number (e.g. 101, 102, 103)")


class CreateTicketDraftInput(BaseModel):
    title: str = Field(min_length=5, max_length=200, description="Concise title summarizing the incident or defect")
    description: str = Field(min_length=10, description="Detailed problem statement, impact, and diagnostic context")
    priority: Literal["P0", "P1", "P2", "P3", "P4"] = Field(description="Incident severity level")
    team: str = Field(description="Responsible owner team (e.g. 'payments', 'security', 'catalog', 'infrastructure', 'experience')")
    labels: List[str] = Field(default_factory=list, description="Descriptive labels or tags")
    service_id: Optional[str] = Field(default=None, description="Optional associated service ID (e.g. 'svc-checkout-api')")


class SummarizePRInput(BaseModel):
    pr_number: int = Field(description="Target PR number to summarize")
    summary: str = Field(min_length=15, description="High-level architectural summary of the changes and motivation")
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(description="Deployment risk tier assessment")
    risk_notes: str = Field(min_length=10, description="Potential failure modes, edge cases, and rollback instructions")


class ListTicketsInput(BaseModel):
    service_id: Optional[str] = Field(default=None, description="Optional service ID to filter (e.g. 'svc-checkout-api')")
    severity: Optional[str] = Field(default=None, description="Optional severity filter ('P0', 'P1', 'P2', 'P3', 'P4')")
    include_drafts: bool = Field(default=True, description="Whether to include local draft tickets")
