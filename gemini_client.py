"""Multi-model Gemini API client with fallback support for the multi-agent research system."""

import logging
import time
from typing import Dict, Any, Optional, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from config import MODELS, MAX_MODEL_RETRIES, RATE_LIMIT_RETRY_DELAY, MODEL_SWITCH_DELAY

logger = logging.getLogger(__name__)


class ModelStatus:
    """Track the status of each model."""
    
    def __init__(self, model_config: Dict[str, Any]):
        self.name = model_config["name"]
        self.api_key = model_config["api_key"]
        self.temperature = model_config.get("temperature", 0.7)
        self.max_tokens = model_config.get("max_tokens", 8192)
        self.priority = model_config.get("priority", 1)
        
        # Status tracking
        self.is_available = True
        self.rate_limited_until = None
        self.error_count = 0
        self.last_used = None
        self.llm_instance = None
    
    def is_rate_limited(self) -> bool:
        """Check if model is currently rate limited."""
        if self.rate_limited_until is None:
            return False
        return time.time() < self.rate_limited_until
    
    def set_rate_limited(self, duration: int = RATE_LIMIT_RETRY_DELAY):
        """Mark model as rate limited."""
        self.rate_limited_until = time.time() + duration
        logger.warning(f"Model {self.name} rate limited until {time.ctime(self.rate_limited_until)}")
    
    def increment_error(self):
        """Increment error count."""
        self.error_count += 1
        if self.error_count >= MAX_MODEL_RETRIES:
            self.is_available = False
            logger.error(f"Model {self.name} marked as unavailable after {self.error_count} errors")
    
    def reset_error_count(self):
        """Reset error count."""
        self.error_count = 0
        self.is_available = True
    
    def get_llm(self) -> ChatGoogleGenerativeAI:
        """Get or create LLM instance."""
        if self.llm_instance is None:
            self.llm_instance = ChatGoogleGenerativeAI(
                model=self.name,
                google_api_key=self.api_key,
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )
        return self.llm_instance


class MultiModelGeminiClient:
    """Multi-model client with automatic fallback for rate limits."""
    
    def __init__(self):
        """Initialize the multi-model client."""
        self.models = {}
        self.current_model_index = 0
        
        # Initialize model status tracking
        for model_config in MODELS:
            model_name = model_config["name"]
            self.models[model_name] = ModelStatus(model_config)
            logger.info(f"Initialized model: {model_name} (priority: {model_config['priority']})")
        
        logger.info(f"Multi-model client initialized with {len(self.models)} models")
    
    def _get_available_model(self) -> Optional[ModelStatus]:
        """Get the next available model."""
        available_models = [
            model for model in self.models.values()
            if model.is_available and not model.is_rate_limited()
        ]
        
        if not available_models:
            logger.error("No available models found")
            return None
        
        # Sort by priority and return the best one
        available_models.sort(key=lambda x: x.priority)
        return available_models[0]
    
    def _handle_rate_limit_error(self, model: ModelStatus, error: Exception):
        """Handle rate limit errors."""
        error_str = str(error).lower()
        
        if any(keyword in error_str for keyword in [
            "rate limit", "quota", "429", "too many requests", 
            "resource exhausted", "limit exceeded"
        ]):
            model.set_rate_limited()
            logger.warning(f"Rate limit detected for model {model.name}")
            return True
        return False
    
    def _handle_general_error(self, model: ModelStatus, error: Exception):
        """Handle general errors."""
        model.increment_error()
        logger.error(f"Error with model {model.name}: {error}")
        
        # If all models are exhausted, reset error counts
        if all(not m.is_available for m in self.models.values()):
            logger.warning("All models exhausted, resetting error counts")
            for m in self.models.values():
                m.reset_error_count()
    
    def generate_response(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate a response using available models with fallback.
        
        Args:
            system_prompt: The system prompt providing context and instructions
            user_prompt: The user prompt with the specific request
            temperature: Controls randomness in generation (uses model default if None)
            
        Returns:
            Generated response text
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        last_error = None
        
        for attempt in range(len(self.models)):
            model = self._get_available_model()
            if not model:
                break
            
            try:
                logger.info(f"Using model: {model.name}")
                
                # Get LLM instance and update temperature if needed
                llm = model.get_llm()
                if temperature is not None:
                    llm.temperature = temperature
                
                # Generate response
                response = llm.invoke(messages)
                
                # Update model status on success
                model.last_used = time.time()
                model.reset_error_count()
                
                logger.info(f"Successfully generated response using model: {model.name}")
                return response.content
                
            except Exception as e:
                last_error = e
                
                # Handle rate limit errors
                if self._handle_rate_limit_error(model, e):
                    logger.info(f"Switching from rate-limited model {model.name}")
                    time.sleep(MODEL_SWITCH_DELAY)
                    continue
                
                # Handle other errors
                self._handle_general_error(model, e)
                logger.info(f"Switching from failed model {model.name}")
                time.sleep(MODEL_SWITCH_DELAY)
        
        # If we get here, all models failed
        error_msg = f"All models failed. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    def generate_structured_response(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        expected_format: str,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate a structured response with specific format requirements.
        
        Args:
            system_prompt: The system prompt providing context and instructions
            user_prompt: The user prompt with the specific request
            expected_format: Description of the expected output format
            temperature: Controls randomness in generation (uses model default if None)
            
        Returns:
            Generated response text in the expected format
        """
        structured_prompt = f"""
{system_prompt}

Expected Output Format:
{expected_format}

Please ensure your response follows this format exactly.
"""
        
        return self.generate_response(
            system_prompt=structured_prompt,
            user_prompt=user_prompt,
            temperature=temperature
        )
    
    def batch_generate(
        self, 
        prompts: List[tuple[str, str]], 
        temperature: Optional[float] = None
    ) -> List[str]:
        """
        Generate responses for multiple prompts in batch.
        
        Args:
            prompts: List of (system_prompt, user_prompt) tuples
            temperature: Controls randomness in generation
            
        Returns:
            List of generated responses
        """
        responses = []
        for system_prompt, user_prompt in prompts:
            response = self.generate_response(system_prompt, user_prompt, temperature)
            responses.append(response)
        return responses
    
    def get_model_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all models."""
        status = {}
        for name, model in self.models.items():
            status[name] = {
                "available": model.is_available,
                "rate_limited": model.is_rate_limited(),
                "error_count": model.error_count,
                "last_used": model.last_used,
                "priority": model.priority
            }
        return status
    
    def reset_all_models(self):
        """Reset all models to available status."""
        for model in self.models.values():
            model.reset_error_count()
            model.rate_limited_until = None
        logger.info("All models reset to available status")


# Global instance
gemini_client = MultiModelGeminiClient()
