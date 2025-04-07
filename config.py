import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Log the API key for debugging (ensure this is removed in production)
logger = logging.getLogger(__name__)
logger.info("GROQ_API_KEY loaded successfully")  # Updated to avoid exposing the key

# LLM Configuration
DEFAULT_MODEL = "llama3-8b-8192"
MAX_TOKENS = 100
TEMPERATURE = 0.7

# WebSocket Configuration
WS_PING_INTERVAL = 30  # seconds
DEBUG_MODE = True

# Server Configuration
HOST = "0.0.0.0"
PORT = 8000

# Spell Checker Configuration
ENABLE_SPELL_CHECK = True  # Set to False to disable spell checking
SPELL_CHECK_MIN_WORD_LENGTH = 3  # Minimum word length to check for spelling errors
SPELL_CHECK_IGNORE_CAPITALIZED = True  # Ignore words that start with a capital letter (proper nouns)

# Cost Tracking Configuration
ENABLE_COST_TRACKING = True  # Set to False to disable cost tracking
COST_LOG_FILE = "api_usage.json"  # File to store API usage data
DAILY_COST_LIMIT = 5.0  # Maximum cost allowed per day in USD
RATE_LIMIT_THRESHOLD = 0.8  # Percentage of rate limit at which to start throttling (0.0-1.0)

# Groq API Rate Limits (as of implementation date)
# These values may change based on Groq's policies
GROQ_RATE_LIMITS = {
    "llama3-8b-8192": 500,  # 500 requests per minute
}

# Groq API Pricing (as of implementation date)
# These values may change based on Groq's pricing
GROQ_PRICING = {
    "llama3-8b-8192": {
        "input": 0.20,  # $0.20 per 1M input tokens
        "output": 0.70,  # $0.70 per 1M output tokens
    }
}