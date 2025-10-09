"""CS/IT Planner Agent for creating specialized research plans."""

import logging
import json
from typing import Dict, Any
from gemini_client import gemini_client
from models import AgentState, ResearchPlan
from config import CS_IT_DOMAIN_ONLY, CS_IT_KEYWORDS

logger = logging.getLogger(__name__)


class PlannerAgent:
    """Agent responsible for creating CS/IT-focused research plans."""
    
    def __init__(self):
        """Initialize the CS/IT Planner Agent."""
        self.name = "CS/IT Planner Agent"
        logger.info(f"Initialized {self.name}")
    
    def create_research_plan(self, state: AgentState) -> Dict[str, Any]:
        """
        Create a comprehensive research plan for the given topic.
        
        Args:
            state: Current agent state containing the user topic
            
        Returns:
            Updated state with research plan
        """
        logger.info(f"{self.name} creating research plan for topic: {state.user_topic}")
        
        system_prompt = """You are an expert CS/IT research planner with extensive experience in computer science and information technology research. Your role is to create comprehensive, well-structured research plans specifically for CS/IT topics.

Key responsibilities:
1. Break down CS/IT topics into technical research components
2. Identify key technical questions and research directions
3. Suggest effective search strategies for academic and industry sources
4. Focus on recent developments, trends, and practical applications
5. Ensure coverage of both theoretical and practical aspects

CS/IT Research Focus:
- Academic papers (ArXiv, IEEE, ACM)
- Open source projects and repositories (GitHub)
- Industry reports and whitepapers
- Technical blogs and documentation
- Conference proceedings and workshops
- Real-world implementations and case studies

Your research plans should be:
- Technically accurate and current
- Focused on CS/IT domains and applications
- Include both academic and industry perspectives
- Emphasize recent developments and trends
- Practical and actionable for CS/IT professionals"""

        user_prompt = f"""
Create a comprehensive CS/IT research plan for the following topic: "{state.user_topic}"

Please provide a detailed research plan that includes:

1. **Main Research Questions** (3-5 key technical questions that need to be answered)
2. **Sub-topics** (4-6 specific CS/IT areas to investigate)
3. **Search Strategies** (3-4 different approaches to gather CS/IT information)
4. **Expected Sources** (types of CS/IT sources that would be valuable)
5. **Research Depth** (recommended depth level: 1-5, where 5 is most comprehensive)

Focus on:
- Recent developments and current trends
- Technical implementations and practical applications
- Academic research and industry adoption
- Open source projects and real-world usage
- Performance, scalability, and security considerations

Format your response as a JSON object with these exact keys:
- "main_questions": [list of main technical research questions]
- "sub_topics": [list of CS/IT sub-topics to explore]
- "search_strategies": [list of CS/IT search strategies]
- "expected_sources": [list of expected CS/IT source types]
- "research_depth": [integer from 1-5]

Example:
{{
  "main_questions": ["What are the latest advances in X?", "How is X implemented in practice?", "What are the performance characteristics of X?"],
  "sub_topics": ["Core algorithms", "Implementation approaches", "Performance optimization", "Security considerations"],
  "search_strategies": ["ArXiv paper analysis", "GitHub repository review", "Industry case studies", "Technical documentation review"],
  "expected_sources": ["ArXiv papers", "GitHub repositories", "IEEE/ACM publications", "Technical blogs", "Open source projects"],
  "research_depth": 4
}}
"""

        try:
            response = gemini_client.generate_structured_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                expected_format="JSON object with specified keys",
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
            research_plan_data = json.loads(response)
            
            # Validate and create ResearchPlan object
            research_plan = ResearchPlan(**research_plan_data)
            
            logger.info(f"{self.name} successfully created research plan with {len(research_plan.main_questions)} main questions")
            
            # Update state
            state.research_plan = research_plan.dict()
            
            return {"research_plan": research_plan.dict()}
            
        except json.JSONDecodeError as e:
            logger.error(f"{self.name} failed to parse JSON response: {e}")
            # Fallback: create a basic research plan
            fallback_plan = self._create_fallback_plan(state.user_topic)
            state.research_plan = fallback_plan
            return {"research_plan": fallback_plan}
            
        except Exception as e:
            logger.error(f"{self.name} failed to create research plan: {e}")
            # Fallback: create a basic research plan
            fallback_plan = self._create_fallback_plan(state.user_topic)
            state.research_plan = fallback_plan
            return {"research_plan": fallback_plan}
    
    def _create_fallback_plan(self, topic: str) -> Dict[str, Any]:
        """Create a basic fallback research plan."""
        logger.warning(f"{self.name} using fallback research plan for topic: {topic}")
        
        return {
            "main_questions": [
                f"What is the current understanding of {topic}?",
                f"What are the key challenges related to {topic}?",
                f"What are the future prospects for {topic}?"
            ],
            "sub_topics": [
                "Background and context",
                "Current state",
                "Challenges and limitations",
                "Future trends"
            ],
            "search_strategies": [
                "Literature review",
                "Current news and reports",
                "Expert opinions"
            ],
            "expected_sources": [
                "Academic papers",
                "Industry reports",
                "News articles",
                "Expert interviews"
            ],
            "research_depth": 3
        }
    
    def refine_plan(self, state: AgentState, feedback: str) -> Dict[str, Any]:
        """
        Refine the research plan based on feedback.
        
        Args:
            state: Current agent state
            feedback: Feedback from the critic agent
            
        Returns:
            Updated state with refined research plan
        """
        logger.info(f"{self.name} refining research plan based on feedback")
        
        system_prompt = """You are an expert research planner. You need to refine an existing research plan based on specific feedback. Your goal is to improve the plan to address the identified issues while maintaining its comprehensive nature.

Consider the feedback carefully and make targeted improvements to:
- Research questions (make them more specific or comprehensive as needed)
- Sub-topics (add missing areas or remove irrelevant ones)
- Search strategies (improve or add new approaches)
- Expected sources (expand or refine source types)
- Research depth (adjust if needed)

Maintain the same JSON format as the original plan."""

        user_prompt = f"""
Original research plan:
{json.dumps(state.research_plan, indent=2)}

Feedback to address:
{feedback}

Please provide a refined research plan that addresses the feedback while maintaining comprehensive coverage of the topic "{state.user_topic}".

Return the refined plan in the same JSON format as the original.
"""

        try:
            response = gemini_client.generate_structured_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                expected_format="JSON object with same structure as original plan",
                temperature=0.4
            )
            
            # Parse the JSON response
            refined_plan_data = json.loads(response.strip())
            
            # Validate and create ResearchPlan object
            research_plan = ResearchPlan(**refined_plan_data)
            
            logger.info(f"{self.name} successfully refined research plan")
            
            # Update state
            state.research_plan = research_plan.dict()
            
            return {"research_plan": research_plan.dict()}
            
        except Exception as e:
            logger.error(f"{self.name} failed to refine research plan: {e}")
            # Return original plan if refinement fails
            return {"research_plan": state.research_plan}
