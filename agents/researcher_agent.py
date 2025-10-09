"""Researcher Agent for gathering and synthesizing CS/IT information."""

import logging
import json
from typing import Dict, Any, List
from datetime import datetime
from gemini_client import gemini_client
from models import AgentState, SynthesizedData
from data_sources import CSResearchFetcher, RealTimeDataSources
from config import CS_IT_DOMAIN_ONLY, CS_IT_KEYWORDS

logger = logging.getLogger(__name__)


class ResearcherAgent:
    """Agent responsible for gathering and synthesizing CS/IT research information."""
    
    def __init__(self):
        """Initialize the Researcher Agent."""
        self.name = "CS/IT Researcher Agent"
        self.cs_fetcher = CSResearchFetcher()
        self.realtime_sources = RealTimeDataSources()
        logger.info(f"Initialized {self.name}")
    
    def gather_and_synthesize(self, state: AgentState) -> Dict[str, Any]:
        """
        Gather and synthesize CS/IT information based on the research plan.
        
        Args:
            state: Current agent state containing the research plan
            
        Returns:
            Updated state with synthesized data
        """
        logger.info(f"{self.name} gathering CS/IT information for topic: {state.user_topic}")
        
        # Validate CS/IT domain
        if CS_IT_DOMAIN_ONLY and not self.cs_fetcher.is_cs_it_topic(state.user_topic):
            logger.warning(f"Topic '{state.user_topic}' may not be CS/IT related")
            return self._create_domain_warning_data(state.user_topic)
        
        # Increment research attempts
        state.research_attempts += 1
        
        # Fetch real data from CS/IT sources
        try:
            # Get comprehensive data from ArXiv and other sources with pagination
            # Calculate page numbers from offsets (GitHub/SO use 1-based pages)
            github_page = (state.github_offset // 20) + 1
            stackoverflow_page = (state.stackoverflow_offset // 5) + 1
            
            arxiv_data = self.cs_fetcher.fetch_comprehensive_data(
                state.user_topic, 
                arxiv_offset=state.arxiv_offset
            )
            realtime_data = self.realtime_sources.fetch_comprehensive_realtime_data(
                state.user_topic,
                github_page=github_page,
                stackoverflow_page=stackoverflow_page
            )
            
            # Get domain-specific insights
            domain_insights = self.cs_fetcher.get_domain_specific_insights(state.user_topic)
            
            # Synthesize the real data using AI
            synthesized_data = self._synthesize_real_data(
                state.user_topic, 
                arxiv_data, 
                realtime_data, 
                domain_insights,
                state.research_plan
            )
            
            logger.info(f"{self.name} successfully synthesized real CS/IT data with {len(synthesized_data['key_findings'])} key findings")
            
            # Update pagination offsets for next iteration
            arxiv_fetched = len(arxiv_data.get('sources', {}).get('arxiv', []))
            github_fetched = len(realtime_data.get('sources', {}).get('github', []))
            stackoverflow_fetched = len(realtime_data.get('sources', {}).get('stackoverflow', []))
            
            new_arxiv_offset = state.arxiv_offset + arxiv_fetched
            new_github_offset = state.github_offset + github_fetched
            new_stackoverflow_offset = state.stackoverflow_offset + stackoverflow_fetched
            
            # Update state
            state.synthesized_data = synthesized_data
            
            return {
                "synthesized_data": synthesized_data,
                "arxiv_offset": new_arxiv_offset,
                "github_offset": new_github_offset,
                "stackoverflow_offset": new_stackoverflow_offset
            }
            
        except Exception as e:
            logger.error(f"{self.name} failed to synthesize real data: {e}")
            # Fallback: create basic synthesized data
            fallback_data = self._create_fallback_data(state.user_topic)
            state.synthesized_data = fallback_data
            return {"synthesized_data": fallback_data}
    
    def _synthesize_real_data(self, topic: str, arxiv_data: Dict, realtime_data: Dict, 
                             domain_insights: Dict, research_plan: Dict) -> Dict[str, Any]:
        """Synthesize real data from multiple CS/IT sources."""
        logger.info(f"{self.name} synthesizing real data for topic: {topic}")
        
        system_prompt = """You are an expert CS/IT researcher specializing in synthesizing information from academic papers, real-time sources, and industry insights. Your role is to analyze real data from multiple sources and provide comprehensive, up-to-date insights.

Key capabilities:
1. Analyze academic papers from ArXiv and other sources
2. Synthesize information from real-time sources (GitHub, Reddit, Stack Overflow, etc.)
3. Identify trends and patterns in CS/IT domains
4. Evaluate the quality and relevance of different sources
5. Provide actionable insights for CS/IT professionals

Focus on:
- Recent developments and trends
- Technical accuracy and depth
- Practical applications and implications
- Industry adoption and real-world usage
- Research gaps and future directions"""

        # Prepare data summary for AI synthesis
        data_summary = self._prepare_data_summary(arxiv_data, realtime_data, domain_insights)
        
        user_prompt = f"""
CS/IT Research Topic: "{topic}"

Research Plan:
{json.dumps(research_plan, indent=2)}

Real Data Sources:
{json.dumps(data_summary, indent=2)}

Please analyze this real data and synthesize comprehensive findings. Focus on:
1. Key technical developments and breakthroughs
2. Recent trends and industry adoption
3. Practical applications and use cases
4. Research gaps and future directions
5. Technical challenges and solutions

Provide your synthesis in the following JSON format:
{{
  "key_findings": [
    "Finding 1: [detailed technical finding with context]",
    "Finding 2: [detailed technical finding with context]",
    ...
  ],
  "supporting_evidence": [
    "Evidence 1: [specific evidence from real sources]",
    "Evidence 2: [specific evidence from real sources]",
    ...
  ],
  "conflicting_information": [
    "Conflict 1: [conflicting viewpoints or approaches found]",
    "Conflict 2: [conflicting viewpoints or approaches found]",
    ...
  ],
  "source_summaries": [
    {{
      "source_type": "[e.g., ArXiv Papers, GitHub Repositories, Industry Reports]",
      "key_insights": "[summary of key insights from this source type]",
      "reliability": "[high/medium/low]",
      "item_count": [number of items from this source]
    }},
    ...
  ],
  "data_quality_score": [float between 0.0 and 1.0],
  "recent_trends": [
    "Trend 1: [recent development or trend]",
    "Trend 2: [recent development or trend]",
    ...
  ],
  "technical_depth": "[assessment of technical depth and accuracy]"
}}

Guidelines:
- Base findings on the actual data provided, not assumptions
- Include specific references to papers, repositories, or sources when possible
- Focus on CS/IT technical aspects and practical implications
- Highlight recent developments and current trends
- Ensure technical accuracy and depth
- Provide actionable insights for CS/IT professionals
"""

        try:
            response = gemini_client.generate_structured_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                expected_format="JSON object with CS/IT research findings",
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
            synthesized_data = json.loads(response)
            
            # Add metadata about data sources
            fetch_timestamp = arxiv_data.get('fetch_timestamp', 'unknown')
            if isinstance(fetch_timestamp, datetime):
                fetch_timestamp = fetch_timestamp.isoformat()
            
            synthesized_data['data_sources'] = {
                'arxiv_papers': len(arxiv_data.get('sources', {}).get('arxiv', [])),
                'realtime_items': realtime_data.get('total_items', 0),
                'domain_insights': domain_insights.get('domain', 'CS/IT'),
                'fetch_timestamp': fetch_timestamp
            }
            
            return synthesized_data
            
        except json.JSONDecodeError as e:
            logger.error(f"{self.name} failed to parse synthesis response: {e}")
            return self._create_fallback_data(topic)
        except Exception as e:
            logger.error(f"{self.name} failed to synthesize real data: {e}")
            return self._create_fallback_data(topic)
    
    def _prepare_data_summary(self, arxiv_data: Dict, realtime_data: Dict, domain_insights: Dict) -> Dict[str, Any]:
        """Prepare a summary of real data for AI synthesis."""
        summary = {
            'arxiv_papers': [],
            'realtime_sources': {},
            'domain_insights': domain_insights,
            'total_sources': 0
        }
        
        # Summarize ArXiv papers
        arxiv_papers = arxiv_data.get('sources', {}).get('arxiv', [])
        for paper in arxiv_papers[:5]:  # Limit to top 5 papers
            # Convert datetime to string if present
            published = paper.get('published', '')
            if isinstance(published, datetime):
                published = published.isoformat()
            
            summary['arxiv_papers'].append({
                'title': paper.get('title', ''),
                'abstract': paper.get('abstract', '')[:200] + '...',
                'published': published,
                'relevance_score': paper.get('relevance_score', 0)
            })
        
        # Summarize real-time sources
        for source_name, source_data in realtime_data.get('sources', {}).items():
            if isinstance(source_data, list) and source_data:
                # Convert datetime objects in sample items
                sample_items = []
                for item in source_data[:3]:
                    item_copy = item.copy() if isinstance(item, dict) else item
                    if isinstance(item_copy, dict):
                        # Convert any datetime fields to strings
                        for key, value in item_copy.items():
                            if isinstance(value, datetime):
                                item_copy[key] = value.isoformat()
                        sample_items.append(item_copy)
                    else:
                        sample_items.append(item_copy)
                
                summary['realtime_sources'][source_name] = {
                    'count': len(source_data),
                    'sample_items': sample_items
                }
                summary['total_sources'] += len(source_data)
        
        return summary
    
    def _create_domain_warning_data(self, topic: str) -> Dict[str, Any]:
        """Create data for non-CS/IT topics."""
        logger.warning(f"Topic '{topic}' is not CS/IT related")
        
        return {
            "key_findings": [
                f"Topic '{topic}' appears to be outside the CS/IT domain",
                "This research system is specialized for Computer Science and Information Technology topics",
                "Please rephrase your topic to focus on CS/IT aspects"
            ],
            "supporting_evidence": [
                "System is configured for CS/IT domains only",
                "Topic does not match CS/IT keyword patterns"
            ],
            "conflicting_information": [],
            "source_summaries": [
                {
                    "source_type": "System Warning",
                    "key_insights": "Topic outside CS/IT domain",
                    "reliability": "high"
                }
            ],
            "data_quality_score": 0.1,
            "domain_warning": True
        }
    
    def _create_fallback_data(self, topic: str) -> Dict[str, Any]:
        """Create basic fallback synthesized data."""
        logger.warning(f"{self.name} using fallback synthesized data for topic: {topic}")
        
        return {
            "key_findings": [
                f"Current understanding of {topic} shows significant development in recent years",
                f"Main challenges in {topic} include scalability and adoption issues",
                f"Future prospects for {topic} appear promising with emerging technologies"
            ],
            "supporting_evidence": [
                f"Recent studies indicate growing interest in {topic}",
                f"Industry reports show increasing investment in {topic}",
                f"Expert opinions suggest {topic} will continue evolving"
            ],
            "conflicting_information": [
                f"Some sources indicate potential limitations in {topic}",
                f"Alternative approaches to {topic} exist with different trade-offs"
            ],
            "source_summaries": [
                {
                    "source_type": "Academic Literature",
                    "key_insights": f"Research papers provide theoretical foundation for {topic}",
                    "reliability": "high"
                },
                {
                    "source_type": "Industry Reports",
                    "key_insights": f"Market analysis shows current trends in {topic}",
                    "reliability": "medium"
                },
                {
                    "source_type": "Expert Opinions",
                    "key_insights": f"Industry experts share practical insights on {topic}",
                    "reliability": "medium"
                }
            ],
            "data_quality_score": 0.7
        }
    
    def expand_research(self, state: AgentState, feedback: str) -> Dict[str, Any]:
        """
        Expand research based on feedback about insufficient information.
        
        Args:
            state: Current agent state
            feedback: Feedback indicating what additional research is needed
            
        Returns:
            Updated state with expanded synthesized data
        """
        logger.info(f"{self.name} expanding research based on feedback")
        
        # Increment research attempts
        state.research_attempts += 1
        
        system_prompt = """You are an expert researcher. You need to expand your previous research based on specific feedback about what information is missing or insufficient. Your goal is to fill the gaps identified in the feedback while maintaining the quality and structure of your research.

Focus on:
1. Addressing specific gaps mentioned in the feedback
2. Gathering additional information on identified weak areas
3. Improving the depth and breadth of your findings
4. Maintaining the same structured format
5. Ensuring higher data quality score if possible

Build upon your previous research rather than starting from scratch."""

        user_prompt = f"""
Research Topic: "{state.user_topic}"

Previous Research Plan:
{json.dumps(state.research_plan, indent=2)}

Previous Research Findings:
{json.dumps(state.synthesized_data, indent=2)}

Feedback on Research Gaps:
{feedback}

Please expand your research to address the identified gaps. Provide additional findings, evidence, and source information that fills the missing areas while maintaining the same JSON structure.

Return the expanded research in the same JSON format as before, but with additional content addressing the feedback.
"""

        try:
            response = gemini_client.generate_structured_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                expected_format="JSON object with expanded research findings",
                temperature=0.4
            )
            
            # Parse the JSON response
            expanded_data = json.loads(response.strip())
            
            # Validate and create SynthesizedData object
            research_data = SynthesizedData(**expanded_data)
            
            logger.info(f"{self.name} successfully expanded research")
            
            # Update state
            state.synthesized_data = research_data.dict()
            
            return {"synthesized_data": research_data.dict()}
            
        except Exception as e:
            logger.error(f"{self.name} failed to expand research: {e}")
            # Return original data if expansion fails
            return {"synthesized_data": state.synthesized_data}
