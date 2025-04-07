import logging
import asyncio
import time
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
from langchain.callbacks.base import BaseCallbackHandler, BaseCallbackManager

import config
from spell_checker import correct_spelling

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Use pricing and rate limit information from config
class GroqPricing:
    """Groq pricing information from config"""
    # Get pricing from config
    @staticmethod
    def get_pricing(model):
        """Get pricing for a specific model"""
        return config.GROQ_PRICING.get(model, config.GROQ_PRICING.get("llama3-8b-8192"))
    
    # Get rate limits from config
    @staticmethod
    def get_rate_limit(model):
        """Get rate limit for a specific model"""
        return config.GROQ_RATE_LIMITS.get(model, config.GROQ_RATE_LIMITS.get("llama3-8b-8192"))
    
    # Default model if not specified
    DEFAULT_MODEL = config.DEFAULT_MODEL

# Cost tracking class
class CostTracker:
    """Tracks API usage, costs, and rate limits for LLM API calls"""
    
    def __init__(self, log_file=None):
        self.log_file = LOGS_DIR / (log_file or config.COST_LOG_FILE)
        self.usage_data = self._load_usage_data()
        self.request_timestamps = []
        self.daily_cost_limit = config.DAILY_COST_LIMIT
        self.rate_limit_threshold = config.RATE_LIMIT_THRESHOLD
        
    def _load_usage_data(self) -> Dict:
        """Load existing usage data or create new structure"""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error loading usage data from {self.log_file}. Creating new data.")
        
        # Initialize new usage data structure
        return {
            "total_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "requests_by_date": {},
            "api_calls": []
        }
    
    def _save_usage_data(self):
        """Save usage data to log file"""
        with open(self.log_file, 'w') as f:
            json.dump(self.usage_data, f, indent=2)
    
    def log_api_call(self, model: str, input_tokens: int, output_tokens: int, 
                    duration: float, success: bool, error: Optional[str] = None):
        """Log details of an API call"""
        # Calculate cost based on token usage and model pricing
        pricing = GroqPricing.get_pricing(model)
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        # Get current date for grouping
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Create API call record
        api_call = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "duration": duration,
            "success": success
        }
        
        if error:
            api_call["error"] = error
        
        # Update usage statistics
        self.usage_data["total_requests"] += 1
        self.usage_data["total_input_tokens"] += input_tokens
        self.usage_data["total_output_tokens"] += output_tokens
        self.usage_data["total_cost"] += total_cost
        
        # Update date-based statistics
        if today not in self.usage_data["requests_by_date"]:
            self.usage_data["requests_by_date"][today] = {
                "requests": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": 0.0
            }
        
        self.usage_data["requests_by_date"][today]["requests"] += 1
        self.usage_data["requests_by_date"][today]["input_tokens"] += input_tokens
        self.usage_data["requests_by_date"][today]["output_tokens"] += output_tokens
        self.usage_data["requests_by_date"][today]["cost"] += total_cost
        
        # Add API call to history (limit to last 1000 calls to prevent file growth)
        self.usage_data["api_calls"].append(api_call)
        if len(self.usage_data["api_calls"]) > 1000:
            self.usage_data["api_calls"] = self.usage_data["api_calls"][-1000:]
        
        # Save updated data
        self._save_usage_data()
        
        # Log summary
        logger.info(f"API Call: {input_tokens} input tokens, {output_tokens} output tokens, ${total_cost:.6f} cost")
        
        return api_call
    
    def check_rate_limit(self, model: str) -> bool:
        """Check if we're approaching rate limits"""
        # Skip check if cost tracking is disabled
        if not config.ENABLE_COST_TRACKING:
            return True
            
        # Clean up old timestamps (older than 1 minute)
        current_time = time.time()
        self.request_timestamps = [ts for ts in self.request_timestamps if current_time - ts < 60]
        
        # Get rate limit for model
        rate_limit = GroqPricing.get_rate_limit(model)
        
        # Check if we're at the configured threshold of the rate limit
        return len(self.request_timestamps) < (rate_limit * self.rate_limit_threshold)
    
    def record_request(self):
        """Record a timestamp for rate limiting"""
        self.request_timestamps.append(time.time())
        
    def check_daily_cost_limit(self) -> bool:
        """Check if we've exceeded the daily cost limit"""
        # Skip check if cost tracking is disabled
        if not config.ENABLE_COST_TRACKING:
            return True
            
        # Get today's usage
        today = datetime.now().strftime("%Y-%m-%d")
        today_usage = self.usage_data["requests_by_date"].get(today, {"cost": 0.0})
        
        # Check if we've exceeded the daily cost limit
        return today_usage["cost"] < self.daily_cost_limit
    
    def get_usage_summary(self) -> Dict:
        """Get a summary of API usage and costs"""
        return {
            "total_requests": self.usage_data["total_requests"],
            "total_input_tokens": self.usage_data["total_input_tokens"],
            "total_output_tokens": self.usage_data["total_output_tokens"],
            "total_cost": self.usage_data["total_cost"],
            "today_usage": self.usage_data["requests_by_date"].get(
                datetime.now().strftime("%Y-%m-%d"), 
                {"requests": 0, "input_tokens": 0, "output_tokens": 0, "cost": 0.0}
            )
        }

# Initialize cost tracker
cost_tracker = CostTracker()

# Callback handler for token counting
class TokenCountingHandler(BaseCallbackHandler):
    """Callback handler that counts tokens for cost tracking"""
    
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.start_time = None
        self.end_time = None
        
    def on_llm_start(self, serialized, prompts, **kwargs):
        """Called when LLM starts processing"""
        self.start_time = time.time()
        # Estimate input tokens (this is approximate)
        for prompt in prompts:
            # Rough estimate: 1 token ≈ 4 characters for English text
            self.input_tokens += len(prompt) // 4
    
    def on_llm_end(self, response, **kwargs):
        """Called when LLM finishes processing"""
        self.end_time = time.time()
        # Estimate output tokens (this is approximate)
        if hasattr(response, 'generations') and response.generations:
            for gen in response.generations[0]:
                # Rough estimate: 1 token ≈ 4 characters for English text
                self.output_tokens += len(gen.text) // 4
    
    def get_duration(self):
        """Get the duration of the API call"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0

# Initialize the LLM
def get_llm(callback_handler=None):
    """Initialize and return the LLM client
    
    Args:
        callback_handler: Optional callback handler for token counting
        
    Returns:
        Initialized LLM client
    """
    try:
        # Check if we have a valid API key
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in environment variables")
            
        # Create a BaseCallbackManager if a handler is provided
        callbacks = BaseCallbackManager([callback_handler]) if callback_handler else None
        
        llm = ChatGroq(
            groq_api_key="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",
            model_name=config.DEFAULT_MODEL,
            temperature=config.TEMPERATURE,
            max_tokens=config.MAX_TOKENS,
            callbacks=callbacks
        )
        return llm
    except Exception as e:
        logger.error(f"Error initializing LLM: {str(e)}")
        raise

# Create a system prompt for text suggestions
SYSTEM_PROMPT = """
You are an intelligent text suggestion assistant. Your task is to provide helpful, 
context-aware text suggestions as the user types. Consider the following guidelines:

1. Analyze the user's current text and predict what they might want to type next
2. Provide concise, relevant suggestions that flow naturally from their current text
3. Consider the context, tone, and purpose of their writing
4. For technical or specialized content, offer domain-specific suggestions
5. For creative writing, suggest compelling continuations that match their style

Provide ONLY the suggested text continuation without any explanations or prefixes.
"""

async def get_text_suggestions(user_text: str) -> dict:
    """Generate text suggestions based on user input
    
    Args:
        user_text: The text input from the user
        
    Returns:
        A dictionary containing the suggested text continuation, spelling corrections,
        and usage metrics
    """
    try:
        # Skip processing for very short inputs
        if len(user_text.strip()) < 3:
            return {"suggestion": ""}
            
        # Apply spell checking to correct any spelling errors
        corrected_text = correct_spelling(user_text)
        
        # Track spelling corrections to send to frontend
        spelling_correction = None
        
        # Log if corrections were made
        if corrected_text != user_text:
            logger.info(f"Spelling corrected: '{user_text}' → '{corrected_text}'")
            # Create spelling correction data for frontend
            spelling_correction = {
                "original": user_text,
                "corrected": corrected_text
            }
            
        # Use the corrected text for generating suggestions
        user_text = corrected_text
        
        # Skip cost checks if cost tracking is disabled
        if config.ENABLE_COST_TRACKING:
            # Check daily cost limit before making API call
            if not cost_tracker.check_daily_cost_limit():
                logger.warning("Daily cost limit reached. Blocking API calls.")
                return {
                    "suggestion": "",
                    "error": "Daily cost limit reached. Please try again tomorrow.",
                    "cost_limit_exceeded": True
                }
                
            # Check rate limits before making API call
            if not cost_tracker.check_rate_limit(config.DEFAULT_MODEL):
                logger.warning("Rate limit threshold reached. Throttling API calls.")
                return {
                    "suggestion": "",
                    "error": "Rate limit threshold reached. Please try again in a moment.",
                    "rate_limited": True
                }
        
        # Record this request for rate limiting
        cost_tracker.record_request()
        
        # Create token counting callback handler
        token_handler = TokenCountingHandler()
            
        # Get LLM with token counting
        llm = get_llm(callback_handler=token_handler)
        
        # Create messages directly
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Based on this text, suggest a natural continuation:\n\n{user_text}"}
        ]
        
        # Generate the suggestion directly using the LLM
        start_time = time.time()
        response = await asyncio.to_thread(lambda: llm.invoke(messages))
        duration = time.time() - start_time
        
        # Extract and clean the suggestion
        suggestion = response.content.strip()
        
        # Log token usage and cost
        api_call = cost_tracker.log_api_call(
            model=config.DEFAULT_MODEL,
            input_tokens=token_handler.input_tokens,
            output_tokens=token_handler.output_tokens,
            duration=duration,
            success=True
        )
        
        logger.info(f"Generated suggestion: {suggestion[:30]}..." if len(suggestion) > 30 
                   else f"Generated suggestion: {suggestion}")
        
        # Get usage summary
        usage_summary = cost_tracker.get_usage_summary()
        
        # Return suggestion, spelling corrections, and usage metrics
        result = {
            "suggestion": suggestion,
            "usage": {
                "input_tokens": token_handler.input_tokens,
                "output_tokens": token_handler.output_tokens,
                "cost": api_call["total_cost"],
                "duration": duration
            },
            "usage_summary": {
                "total_cost": usage_summary["total_cost"],
                "total_requests": usage_summary["total_requests"],
                "today_cost": usage_summary["today_usage"]["cost"],
                "today_requests": usage_summary["today_usage"]["requests"]
            }
        }
        
        if spelling_correction:
            result["spelling_correction"] = spelling_correction
            
        return result
        
    except Exception as e:
        logger.error(f"Error generating suggestion: {str(e)}")
        
        # Log failed API call if possible
        try:
            cost_tracker.log_api_call(
                model=config.DEFAULT_MODEL,
                input_tokens=0,  # We don't know how many tokens were processed
                output_tokens=0,
                duration=0.0,
                success=False,
                error=str(e)
            )
        except Exception as log_error:
            logger.error(f"Error logging failed API call: {str(log_error)}")
        
        return {"suggestion": "", "error": str(e)}