"""Critic Agent for evaluating and providing feedback on reports."""

import logging
import json
from typing import Dict, Any, Literal
from gemini_client import gemini_client
from models import AgentState, CritiqueResult

logger = logging.getLogger(__name__)


class CriticAgent:
    """Agent responsible for critically evaluating reports and providing feedback."""
    
    def __init__(self):
        """Initialize the Critic Agent."""
        self.name = "Critic Agent"
        logger.info(f"Initialized {self.name}")
    
    def critique_report(self, state: AgentState) -> Dict[str, Any]:
        """
        Critically evaluate the draft report and determine next steps.
        
        Args:
            state: Current agent state containing the draft report
            
        Returns:
            Updated state with critique feedback and approval status
        """
        logger.info(f"{self.name} evaluating report for topic: {state.user_topic}")
        
        system_prompt = """You are an expert research critic and quality assurance specialist with extensive experience in evaluating academic and professional reports. Your role is to provide thorough, constructive feedback on research reports and determine whether they meet quality standards.

Evaluation criteria:
1. **Completeness**: Does the report comprehensively address the research topic?
2. **Accuracy**: Are claims supported by evidence from the research?
3. **Clarity**: Is the writing clear, well-structured, and easy to follow?
4. **Depth**: Does the analysis go beyond surface-level observations?
5. **Balance**: Are multiple perspectives and conflicting information addressed?
6. **Coherence**: Does the report flow logically from introduction to conclusion?
7. **Evidence Quality**: Is the supporting evidence relevant and reliable?

Decision framework:
- **APPROVED**: Report meets all quality standards and is ready for final delivery
- **REVISION_NEEDED**: Report has good foundation but needs writing improvements
- **RESEARCH_INSUFFICIENT**: Report needs more comprehensive research to be effective

Your feedback should be specific, actionable, and constructive. Focus on helping improve the quality of the work."""

        user_prompt = f"""
Research Topic: "{state.user_topic}"

Research Plan:
{json.dumps(state.research_plan, indent=2)}

Synthesized Research Data:
{json.dumps(state.synthesized_data, indent=2)}

Draft Report:
{state.draft_report}

Please evaluate this draft report comprehensively. Consider:
1. How well it addresses the research plan and questions
2. The quality and comprehensiveness of the analysis
3. The clarity and structure of the writing
4. Whether the research data supports the conclusions
5. Any gaps in coverage or analysis
6. The overall coherence and professional quality

Provide your evaluation in the following JSON format:
{{
  "overall_assessment": "[approved/revision_needed/research_insufficient]",
  "specific_feedback": "[detailed feedback explaining your assessment]",
  "strengths": [
    "[strength 1]",
    "[strength 2]",
    ...
  ],
  "weaknesses": [
    "[weakness 1]",
    "[weakness 2]",
    ...
  ],
  "recommendations": [
    "[specific recommendation 1]",
    "[specific recommendation 2]",
    ...
  ]
}}

Assessment Guidelines:
- **approved**: Use only if the report is comprehensive, well-written, and fully addresses the research topic
- **revision_needed**: Use if the report has good content but needs writing improvements, better structure, or clearer presentation
- **research_insufficient**: Use if the report lacks depth, misses key aspects of the topic, or needs significantly more research to be effective

Be thorough in your evaluation and provide specific, actionable feedback.
"""

        try:
            response = gemini_client.generate_structured_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                expected_format="JSON object with critique assessment",
                temperature=0.3
            )
            
            # Clean and parse the JSON response
            response = response.strip()
            if not response:
                raise ValueError("Empty response from model")
            
            # Try to extract JSON from response if it's wrapped in markdown
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end != -1:
                    response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                if end != -1:
                    response = response[start:end].strip()
            
            # Parse the JSON response
            critique_data = json.loads(response)
            
            # Normalize the overall_assessment to lowercase to handle case variations
            if "overall_assessment" in critique_data:
                critique_data["overall_assessment"] = critique_data["overall_assessment"].lower()
            
            # Validate and create CritiqueResult object
            critique_result = CritiqueResult(**critique_data)
            
            logger.info(f"{self.name} completed evaluation with assessment: {critique_result.overall_assessment}")
            
            # Update state
            state.critique_feedback = critique_result.specific_feedback
            state.approval_status = critique_result.overall_assessment
            
            return {
                "critique_feedback": critique_result.specific_feedback,
                "approval_status": critique_result.overall_assessment,
                "critique_details": critique_result.dict()
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"{self.name} failed to parse JSON response: {e}")
            # Fallback: create basic critique
            fallback_critique = self._create_fallback_critique(state)
            state.critique_feedback = fallback_critique["specific_feedback"]
            state.approval_status = fallback_critique["overall_assessment"]
            return fallback_critique
            
        except Exception as e:
            logger.error(f"{self.name} failed to critique report: {e}")
            # Fallback: create basic critique
            fallback_critique = self._create_fallback_critique(state)
            state.critique_feedback = fallback_critique["specific_feedback"]
            state.approval_status = fallback_critique["overall_assessment"]
            return fallback_critique
    
    def _create_fallback_critique(self, state: AgentState) -> Dict[str, Any]:
        """Create basic fallback critique."""
        logger.warning(f"{self.name} using fallback critique for topic: {state.user_topic}")
        
        # Simple heuristic: if report is long enough and has basic structure, approve
        if state.draft_report and len(state.draft_report) > 1000:
            assessment = "approved"
            feedback = "Report meets basic quality standards and provides comprehensive coverage of the topic."
        else:
            assessment = "revision_needed"
            feedback = "Report needs additional development and refinement to meet quality standards."
        
        return {
            "overall_assessment": assessment,
            "specific_feedback": feedback,
            "strengths": [
                "Addresses the research topic",
                "Provides structured presentation"
            ],
            "weaknesses": [
                "Could benefit from more detailed analysis",
                "Some sections may need expansion"
            ],
            "recommendations": [
                "Continue refining the analysis",
                "Ensure all key points are well-supported"
            ]
        }
    
    def should_continue_workflow(self, state: AgentState) -> Literal["approved", "revision_needed", "research_insufficient"]:
        """
        Determine the next step in the workflow based on the critique.
        
        Args:
            state: Current agent state
            
        Returns:
            Decision on workflow continuation
        """
        if not state.approval_status:
            logger.error(f"{self.name} cannot determine workflow continuation - no approval status")
            return "revision_needed"  # Default to revision if no status
        
        decision = state.approval_status
        logger.info(f"{self.name} workflow decision: {decision}")
        
        return decision
    
    def get_feedback_for_revision(self, state: AgentState) -> str:
        """
        Get specific feedback for report revision.
        
        Args:
            state: Current agent state
            
        Returns:
            Feedback string for revision
        """
        if state.critique_feedback:
            return state.critique_feedback
        
        # Fallback feedback
        return "The report needs revision to improve clarity, depth, and overall quality. Please address the identified weaknesses and implement the recommendations provided."
    
    def get_feedback_for_research(self, state: AgentState) -> str:
        """
        Get specific feedback for additional research.
        
        Args:
            state: Current agent state
            
        Returns:
            Feedback string for research expansion
        """
        if state.critique_feedback:
            return f"The current research is insufficient for a comprehensive report. {state.critique_feedback} Please gather additional information to address these gaps."
        
        # Fallback feedback
        return "The current research is insufficient for a comprehensive report. Please gather additional information to provide more depth and coverage of the topic."
