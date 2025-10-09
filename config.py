"""Configuration settings for the multi-agent research system."""

import os
import json
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Google AI Studio Gemini API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Multi-model configuration
MODELS_CONFIG_FILE = os.getenv("MODELS_CONFIG_FILE", "models_config.json")

# Legacy single model support
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

# Parse models configuration from JSON file
def load_models_config():
    """Load models configuration from JSON file."""
    try:
        # Check if config file exists
        if os.path.exists(MODELS_CONFIG_FILE):
            with open(MODELS_CONFIG_FILE, 'r') as f:
                models = json.load(f)
        else:
            # Fallback to default configuration
            models = [
                {
                    "name": "gemini-1.5-pro",
                    "api_key": "GOOGLE_API_KEY",
                    "temperature": 0.7,
                    "max_tokens": 8192,
                    "priority": 1
                },
                {
                    "name": "gemini-1.5-flash",
                    "api_key": "GOOGLE_API_KEY",
                    "temperature": 0.7,
                    "max_tokens": 8192,
                    "priority": 2
                }
            ]
        
        # Replace API key references with actual keys
        for model in models:
            if model["api_key"] == "GOOGLE_API_KEY":
                model["api_key"] = GOOGLE_API_KEY
        
        return models
        
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.warning(f"Error loading models config: {e}. Using fallback configuration.")
        # Fallback to single model configuration
        return [{
            "name": GEMINI_MODEL,
            "api_key": GOOGLE_API_KEY,
            "temperature": 0.7,
            "max_tokens": 8192,
            "priority": 1
        }]

# Load models configuration
MODELS = load_models_config()

# Validate required environment variables
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is required")

# Sort models by priority
MODELS.sort(key=lambda x: x["priority"])

# Multi-model fallback configuration
MAX_MODEL_RETRIES = 3
RATE_LIMIT_RETRY_DELAY = 60  # seconds
MODEL_SWITCH_DELAY = 5  # seconds

# CS/IT Domain Configuration
CS_IT_DOMAIN_ONLY = True  # Restrict to CS/IT domains only
CS_IT_KEYWORDS = [
    'artificial intelligence', 'machine learning', 'deep learning', 'neural network',
    'computer vision', 'natural language processing', 'nlp', 'data science',
    'software engineering', 'programming', 'algorithm', 'data structure',
    'database', 'cybersecurity', 'cryptography', 'blockchain', 'distributed system',
    'cloud computing', 'web development', 'mobile development', 'devops',
    'computer science', 'information technology', 'computing', 'technology',
    'software', 'hardware', 'networking', 'operating system', 'computer graphics',
    'human computer interaction', 'hci', 'robotics', 'automation', 'ai',
    'ml', 'dl', 'cv', 'api', 'framework', 'library', 'tool', 'platform',
    'architecture', 'design pattern', 'optimization', 'performance',
    'scalability', 'reliability', 'security', 'privacy', 'data mining',
    'big data', 'analytics', 'visualization', 'user interface', 'ux', 'ui'
]

# Data Source Configuration
ARXIV_MAX_RESULTS = 20
GITHUB_MAX_REPOS = 10
STACKOVERFLOW_MAX_QUESTIONS = 10
REDDIT_MAX_POSTS = 10
NEWS_MAX_ARTICLES = 10

# Agent Configuration - Reduced limits to prevent infinite loops
MAX_ITERATIONS = 5
MAX_RESEARCH_ATTEMPTS = 2
MAX_WRITING_ATTEMPTS = 2

# Research Configuration
DEFAULT_SEARCH_DEPTH = 3
DEFAULT_TIMEOUT = 30

# Output Configuration
OUTPUT_DIR = "outputs"
REPORTS_DIR = f"{OUTPUT_DIR}/reports"
LOGS_DIR = f"{OUTPUT_DIR}/logs"

# Ensure output directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
