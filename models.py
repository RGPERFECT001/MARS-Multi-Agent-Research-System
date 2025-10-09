"""Data models for the multi-agent research system."""

from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum


class AgentState(BaseModel):
    """State shared across all agents in the workflow."""
    
    # Input
    user_topic: str = Field(description="The research topic provided by the user")
    
    # Planner Agent Output
    research_plan: Optional[Dict] = Field(default=None, description="The research plan created by the planner")
    
    # Researcher Agent Output
    synthesized_data: Optional[Dict] = Field(default=None, description="The synthesized research data")
    research_attempts: int = Field(default=0, description="Number of research attempts made")
    
    # Pagination offsets for data sources
    arxiv_offset: int = Field(default=0, description="Offset for ArXiv pagination")
    github_offset: int = Field(default=0, description="Offset for GitHub pagination")
    stackoverflow_offset: int = Field(default=0, description="Offset for Stack Overflow pagination")
    reddit_offset: int = Field(default=0, description="Offset for Reddit pagination")
    
    # Writer Agent Output
    draft_report: Optional[str] = Field(default=None, description="The draft report created by the writer")
    writing_attempts: int = Field(default=0, description="Number of writing attempts made")
    
    # Critic Agent Output
    critique_feedback: Optional[str] = Field(default=None, description="Feedback from the critic agent")
    approval_status: Optional[str] = Field(default=None, description="Approval status from critic")
    
    # Final Output
    final_report: Optional[str] = Field(default=None, description="The final approved report")
    
    # Workflow Control
    current_iteration: int = Field(default=0, description="Current iteration number")
    max_iterations_reached: bool = Field(default=False, description="Whether max iterations have been reached")


class ResearchPlan(BaseModel):
    """Research plan structure."""
    
    main_questions: List[str] = Field(description="Main research questions to investigate")
    sub_topics: List[str] = Field(description="Sub-topics to explore")
    search_strategies: List[str] = Field(description="Search strategies to employ")
    expected_sources: List[str] = Field(description="Types of sources expected")
    research_depth: int = Field(default=3, description="Depth of research required")


class SynthesizedData(BaseModel):
    """Synthesized research data structure."""
    
    key_findings: List[str] = Field(description="Key findings from research")
    supporting_evidence: List[str] = Field(description="Supporting evidence for findings")
    conflicting_information: List[str] = Field(description="Any conflicting information found")
    source_summaries: List[Dict] = Field(description="Summaries of information sources")
    data_quality_score: float = Field(description="Quality score of the research data")


class CritiqueResult(BaseModel):
    """Result of critique analysis."""
    
    overall_assessment: Literal["approved", "revision_needed", "research_insufficient"] = Field(
        description="Overall assessment of the report"
    )
    specific_feedback: str = Field(description="Specific feedback on what needs improvement")
    strengths: List[str] = Field(description="Strengths identified in the report")
    weaknesses: List[str] = Field(description="Weaknesses identified in the report")
    recommendations: List[str] = Field(description="Recommendations for improvement")


class WorkflowStatus(str, Enum):
    """Status of the workflow."""
    PLANNING = "planning"
    RESEARCHING = "researching"
    WRITING = "writing"
    CRITIQUING = "critiquing"
    REVISING = "revising"
    COMPLETED = "completed"
    FAILED = "failed"
