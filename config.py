import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

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