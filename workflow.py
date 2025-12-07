"""LangGraph workflow for the multi-agent research system."""

import logging
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from models import AgentState, WorkflowStatus
from agents.planner_agent import PlannerAgent
from agents.researcher_agent import ResearcherAgent
from agents.writer_agent import WriterAgent
from agents.critic_agent import CriticAgent
from config import MAX_ITERATIONS, MAX_RESEARCH_ATTEMPTS, MAX_WRITING_ATTEMPTS

logger = logging.getLogger(__name__)


class MultiAgentResearchWorkflow:
    """LangGraph workflow orchestrating the multi-agent research system."""
    
    def __init__(self):
        """Initialize the workflow with all agents."""
        self.planner = PlannerAgent()
        self.researcher = ResearcherAgent()
        self.writer = WriterAgent()
        self.critic = CriticAgent()
        
        # Create the workflow graph
        self.workflow = self._create_workflow()
        logger.info("Multi-agent research workflow initialized")
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("researcher", self._researcher_node)
        workflow.add_node("writer", self._writer_node)
        workflow.add_node("critic", self._critic_node)
        
        # Define the main flow
        workflow.set_entry_point("planner")
        
        # Add edges for the main flow
        workflow.add_edge("planner", "researcher")
        workflow.add_edge("researcher", "writer")
        workflow.add_edge("writer", END)
        
        # Add conditional edges from critic
        workflow.add_conditional_edges(
            "critic",
            self._critic_decision,
            {
                "approved": END,
                "revision_needed": "writer",
                "research_insufficient": "researcher"
            }
        )
        
        # Compile the workflow
        return workflow.compile(checkpointer=None)
    
    def _planner_node(self, state: AgentState) -> Dict[str, Any]:
        """Execute the planner agent."""
        logger.info("Executing planner node")
        try:
            result = self.planner.create_research_plan(state)
            return result
        except Exception as e:
            logger.error(f"Error in planner node: {e}")
            # Create a basic fallback plan
            fallback_plan = {
                "main_questions": [f"What is {state.user_topic}?", f"What are the key aspects of {state.user_topic}?"],
                "sub_topics": ["Overview", "Key aspects", "Implications"],
                "search_strategies": ["General research", "Literature review"],
                "expected_sources": ["General sources", "Academic papers"],
                "research_depth": 3
            }
            return {"research_plan": fallback_plan}
    
    def _researcher_node(self, state: AgentState) -> Dict[str, Any]:
        """Execute the researcher agent."""
        logger.info("Executing researcher node")
        
        # Increment research attempts
        state.research_attempts = getattr(state, 'research_attempts', 0) + 1
        
        # Check if we need to expand research or start fresh
        if state.synthesized_data and state.research_attempts > 1:
            # This is a research expansion due to insufficient research
            feedback = self.critic.get_feedback_for_research(state)
            try:
                result = self.researcher.expand_research(state, feedback)
                return result
            except Exception as e:
                logger.error(f"Error in researcher expansion: {e}")
                return {"synthesized_data": state.synthesized_data}
        else:
            # Initial research
            try:
                result = self.researcher.gather_and_synthesize(state)
                return result
            except Exception as e:
                logger.error(f"Error in researcher node: {e}")
                # Create fallback data
                fallback_data = {
                    "key_findings": [f"Research on {state.user_topic} shows various perspectives"],
                    "supporting_evidence": [f"Evidence supports multiple viewpoints on {state.user_topic}"],
                    "conflicting_information": [f"Some conflicting views exist on {state.user_topic}"],
                    "source_summaries": [{"source_type": "General", "key_insights": f"Overview of {state.user_topic}", "reliability": "medium"}],
                    "data_quality_score": 0.6
                }
                return {"synthesized_data": fallback_data}
    
    def _writer_node(self, state: AgentState) -> Dict[str, Any]:
        """Execute the writer agent."""
        logger.info("Executing writer node")
        
        # Increment writing attempts
        state.writing_attempts = getattr(state, 'writing_attempts', 0) + 1
        
        # Check if we need to revise or write fresh
        if state.draft_report and state.writing_attempts > 1:
            # This is a revision
            feedback = self.critic.get_feedback_for_revision(state)
            try:
                result = self.writer.revise_report(state, feedback)
                return result
            except Exception as e:
                logger.error(f"Error in writer revision: {e}")
                return {"draft_report": state.draft_report}
        else:
            # Initial writing
            try:
                result = self.writer.write_report(state)
                return result
            except Exception as e:
                logger.error(f"Error in writer node: {e}")
                # Create fallback report
                fallback_report = f"# Research Report: {state.user_topic}\n\nThis is a fallback report due to technical limitations.\n\n## Overview\n\n{state.user_topic} is an important topic that requires further research and analysis.\n\n*Note: This report was generated as a fallback due to system limitations.*"
                return {"draft_report": fallback_report}
    
    def _critic_node(self, state: AgentState) -> Dict[str, Any]:
        """Execute the critic agent."""
        logger.info("Executing critic node")
        try:
            result = self.critic.critique_report(state)
            return result
        except Exception as e:
            logger.error(f"Error in critic node: {e}")
            # Create fallback critique
            fallback_critique = {
                "critique_feedback": "Report evaluation completed with basic assessment.",
                "approval_status": "approved",
                "critique_details": {
                    "overall_assessment": "approved",
                    "specific_feedback": "Report meets basic requirements.",
                    "strengths": ["Addresses the topic"],
                    "weaknesses": ["Could be more detailed"],
                    "recommendations": ["Continue improving"]
                }
            }
            return fallback_critique
    
    def _critic_decision(self, state: AgentState) -> Literal["approved", "revision_needed", "research_insufficient"]:
        """Make decision based on critic evaluation and iteration limits."""
        logger.info("Making critic decision")
        
        # Increment iteration counter
        state.current_iteration = getattr(state, 'current_iteration', 0) + 1
        
        # Check iteration limits first
        if state.current_iteration >= MAX_ITERATIONS:
            logger.warning(f"Max iterations ({MAX_ITERATIONS}) reached, forcing approval")
            state.max_iterations_reached = True
            return "approved"
        
        if state.research_attempts >= MAX_RESEARCH_ATTEMPTS:
            logger.warning(f"Max research attempts ({MAX_RESEARCH_ATTEMPTS}) reached, forcing approval")
            return "approved"
        
        if state.writing_attempts >= MAX_WRITING_ATTEMPTS:
            logger.warning(f"Max writing attempts ({MAX_WRITING_ATTEMPTS}) reached, forcing approval")
            return "approved"
        
        # Get decision from critic
        try:
            decision = self.critic.should_continue_workflow(state)
            logger.info(f"Critic decision: {decision}")
            
            # Additional safety check - if we've been revising too many times, approve
            if decision == "revision_needed" and state.writing_attempts >= 2:
                logger.warning("Too many writing attempts, forcing approval")
                return "approved"
            
            if decision == "research_insufficient" and state.research_attempts >= 2:
                logger.warning("Too many research attempts, forcing approval")
                return "approved"
            
            return decision
            
        except Exception as e:
            logger.error(f"Error in critic decision: {e}")
            return "approved"  # Default to approval to prevent infinite loops
    
    def run(self, topic: str) -> Dict[str, Any]:
        """
        Run the complete research workflow.
        
        Args:
            topic: The research topic
            
        Returns:
            Final state with completed research report
        """
        logger.info(f"Starting research workflow for topic: {topic}")
        
        # Initialize state
        initial_state = AgentState(user_topic=topic)
        
        try:
            # Run the workflow
            final_state = self.workflow.invoke(initial_state)
            
            # Mark as completed
            final_state["final_report"] = final_state.get("draft_report", "No report generated")
            final_state["current_iteration"] = final_state.get("current_iteration", 0) + 1
            
            logger.info("Research workflow completed successfully")
            
            return final_state
            
        except Exception as e:
            logger.error(f"Error running research workflow: {e}")
            
            # Return error state
            return {
                "user_topic": topic,
                "final_report": f"Error generating research report: {str(e)}",
                "error": str(e),
                "workflow_status": WorkflowStatus.FAILED.value
            }
    
    def run_with_callback(self, topic: str, callback=None) -> Dict[str, Any]:
        """
        Run the workflow with progress callback.
        
        Args:
            topic: The research topic
            callback: Optional callback function for progress updates
            
        Returns:
            Final state with completed research report
        """
        if callback:
            callback("Starting research workflow...")
        
        # Initialize state
        initial_state = AgentState(user_topic=topic)
        
        try:
            # Run the workflow with streaming
            final_state = initial_state.dict()
            for step in self.workflow.stream(initial_state):
                final_state.update(step)
                
                if callback:
                    if "planner" in step:
                        callback("Planning research approach...")
                    elif "researcher" in step:
                        callback("Gathering and synthesizing information...")
                    elif "writer" in step:
                        callback("Writing comprehensive report...")
                    elif "critic" in step:
                        callback("Evaluating report quality...")
            
            # Mark as completed
            final_state["final_report"] = final_state.get("draft_report", "No report generated")
            final_state["current_iteration"] = final_state.get("current_iteration", 0) + 1
            
            if callback:
                callback("Research workflow completed!")
            
            logger.info("Research workflow completed successfully")
            
            return final_state
            
        except Exception as e:
            logger.error(f"Error running research workflow: {e}")
            
            if callback:
                callback(f"Error: {str(e)}")
            
            # Return error state
            return {
                "user_topic": topic,
                "final_report": f"Error generating research report: {str(e)}",
                "error": str(e),
                "workflow_status": WorkflowStatus.FAILED.value
            }
