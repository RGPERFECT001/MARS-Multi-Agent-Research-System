"""CS/IT Writer Agent for creating technical reports."""

import logging
from typing import Dict, Any
from gemini_client import gemini_client
from models import AgentState

logger = logging.getLogger(__name__)


class WriterAgent:
    """Agent responsible for writing comprehensive CS/IT technical reports."""
    
    def __init__(self):
        """Initialize the CS/IT Writer Agent."""
        self.name = "CS/IT Writer Agent"
        logger.info(f"Initialized {self.name}")
    
    def write_report(self, state: AgentState) -> Dict[str, Any]:
        """
        Write a comprehensive report based on the synthesized research data.
        
        Args:
            state: Current agent state containing synthesized data
            
        Returns:
            Updated state with draft report
        """
        logger.info(f"{self.name} writing report for topic: {state.user_topic}")
        
        # Increment writing attempts
        state.writing_attempts += 1
        
        system_prompt = """You are an expert CS/IT technical writer with extensive experience in creating comprehensive technical reports for computer science and information technology topics. Your role is to transform research data into clear, technically accurate, and actionable reports for CS/IT professionals.

Writing principles:
1. Structure information logically with clear technical hierarchy
2. Use precise, technical language appropriate for CS/IT professionals
3. Support claims with evidence from academic papers, repositories, and industry sources
4. Present balanced technical viewpoints including alternative approaches
5. Ensure comprehensive coverage of technical findings and practical implications
6. Make the report technically engaging and actionable

CS/IT Report structure should include:
- Executive summary with key technical insights
- Technical background and context
- Main findings organized by technical themes
- Implementation details and practical applications
- Performance analysis and technical considerations
- Security, scalability, and reliability aspects
- Future directions and research gaps
- References to academic papers, repositories, and technical sources

Your writing should be technically authoritative, well-reasoned, and thoroughly supported by real research data from CS/IT sources."""

        user_prompt = f"""
CS/IT Research Topic: "{state.user_topic}"

Research Plan:
{state.research_plan}

Synthesized Research Data:
{state.synthesized_data}

Write a comprehensive CS/IT technical report based on this research. The report should be well-structured, technically accurate, and thoroughly cover all the key findings from the research.

Report Requirements:
1. **Length**: 2500-3500 words
2. **Structure**: Use clear technical headings and subheadings
3. **Content**: Cover all key technical findings from the research
4. **Evidence**: Support all major claims with evidence from academic papers, repositories, and industry sources
5. **Balance**: Include any conflicting technical approaches or alternative viewpoints
6. **Clarity**: Use precise, technical language appropriate for CS/IT professionals
7. **Completeness**: Ensure comprehensive coverage of the technical topic

CS/IT Report Structure:
- **Executive Summary** (300-400 words) - Key technical insights and findings
- **Technical Background** (400-500 words) - Context and technical foundations
- **Main Technical Findings** (organized by themes, 1500-2000 words)
- **Implementation and Practical Applications** (400-600 words)
- **Performance and Technical Considerations** (300-400 words)
- **Future Directions and Research Gaps** (300-400 words)

Guidelines:
- Use the research plan's main technical questions as a guide for structure
- Incorporate findings from all CS/IT source types (ArXiv, GitHub, industry reports)
- Address any conflicting technical approaches transparently
- Provide specific technical examples and evidence for key points
- Include code snippets, algorithms, or technical specifications where relevant
- Reference specific papers, repositories, and technical sources
- Maintain a technical, analytical tone appropriate for CS/IT professionals
- Ensure smooth transitions between technical sections
- Make the report technically engaging while remaining professional and actionable

Please write the complete CS/IT technical report following these guidelines.
"""

        try:
            response = gemini_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.6
            )
            
            logger.info(f"{self.name} successfully wrote report ({len(response)} characters)")
            
            # Update state
            state.draft_report = response
            
            return {"draft_report": response}
            
        except Exception as e:
            logger.error(f"{self.name} failed to write report: {e}")
            # Fallback: create a basic report
            fallback_report = self._create_fallback_report(state)
            state.draft_report = fallback_report
            return {"draft_report": fallback_report}
    
    def _create_fallback_report(self, state: AgentState) -> str:
        """Create a basic fallback report."""
        logger.warning(f"{self.name} using fallback report for topic: {state.user_topic}")
        
        return f"""# Research Report: {state.user_topic}

## Executive Summary

This report provides a comprehensive analysis of {state.user_topic}, examining current understanding, key challenges, and future prospects. The research reveals significant developments in this area with both opportunities and challenges for stakeholders.

## Introduction

{state.user_topic} represents an important area of study with implications across multiple domains. This report synthesizes current research and analysis to provide a comprehensive overview of the topic.

## Key Findings

Based on the research conducted, several key findings emerge:

1. **Current State**: {state.user_topic} has seen significant development in recent years
2. **Challenges**: Several key challenges remain to be addressed
3. **Future Prospects**: The future outlook appears promising with emerging opportunities

## Analysis

The research indicates that {state.user_topic} is evolving rapidly, with both opportunities and challenges present. Stakeholders should consider these factors when making decisions related to this area.

## Conclusions

This research provides valuable insights into {state.user_topic} and suggests several areas for future investigation and development.

*Note: This is a fallback report due to technical limitations. The full research system would provide more detailed analysis.*"""
    
    def revise_report(self, state: AgentState, feedback: str) -> Dict[str, Any]:
        """
        Revise the report based on feedback from the critic agent.
        
        Args:
            state: Current agent state
            feedback: Feedback from the critic agent
            
        Returns:
            Updated state with revised draft report
        """
        logger.info(f"{self.name} revising report based on feedback")
        
        # Increment writing attempts
        state.writing_attempts += 1
        
        system_prompt = """You are an expert technical writer. You need to revise an existing report based on specific feedback. Your goal is to address the identified issues while maintaining the report's comprehensive nature and professional quality.

Revision approach:
1. Carefully analyze the feedback to understand what needs improvement
2. Maintain the overall structure while making targeted improvements
3. Enhance clarity, completeness, and accuracy as needed
4. Address any gaps or weaknesses identified
5. Ensure the revised report meets all original requirements

Focus on:
- Improving unclear or confusing sections
- Adding missing information or analysis
- Strengthening weak arguments or evidence
- Enhancing overall coherence and flow
- Maintaining professional tone and style"""

        user_prompt = f"""
Research Topic: "{state.user_topic}"

Original Report:
{state.draft_report}

Feedback for Revision:
{feedback}

Please revise the report to address the feedback while maintaining its comprehensive nature and professional quality. Make targeted improvements based on the specific issues identified.

Guidelines for revision:
- Address all points raised in the feedback
- Maintain the original report structure unless changes are specifically requested
- Ensure all improvements enhance clarity and completeness
- Keep the same length and depth as the original
- Maintain professional tone and style
- Ensure smooth integration of any new content

Provide the complete revised report.
"""

        try:
            response = gemini_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5
            )
            
            logger.info(f"{self.name} successfully revised report")
            
            # Update state
            state.draft_report = response
            
            return {"draft_report": response}
            
        except Exception as e:
            logger.error(f"{self.name} failed to revise report: {e}")
            # Return original report if revision fails
            return {"draft_report": state.draft_report}
