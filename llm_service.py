import logging
import asyncio
from typing import Dict, Any, Optional

from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate

import config
from spell_checker import correct_spelling

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize the LLM
def get_llm():
    """Initialize and return the LLM client"""
    try:
        llm = ChatGroq(
            groq_api_key=config.GROQ_API_KEY,
            model_name=config.DEFAULT_MODEL,
            temperature=config.TEMPERATURE,
            max_tokens=config.MAX_TOKENS
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

async def get_text_suggestions(user_text: str) -> str:
    """Generate text suggestions based on user input
    
    Args:
        user_text: The text input from the user
        
    Returns:
        A string containing the suggested text continuation
    """
    try:
        # Skip processing for very short inputs
        if len(user_text.strip()) < 3:
            return ""
            
        # Apply spell checking to correct any spelling errors
        corrected_text = correct_spelling(user_text)
        
        # Log if corrections were made
        if corrected_text != user_text:
            logger.info(f"Spelling corrected: '{user_text}' → '{corrected_text}'")
            
        # Use the corrected text for generating suggestions
        user_text = corrected_text
            
        llm = get_llm()
        
        # Create messages directly
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Based on this text, suggest a natural continuation:\n\n{user_text}"}
        ]
        
        # Generate the suggestion directly using the LLM
        response = await asyncio.to_thread(lambda: llm.invoke(messages))
        
        # Extract and clean the suggestion
        suggestion = response.content.strip()
        
        logger.info(f"Generated suggestion: {suggestion[:30]}..." if len(suggestion) > 30 
                   else f"Generated suggestion: {suggestion}")
        
        return suggestion
        
    except Exception as e:
        logger.error(f"Error generating suggestion: {str(e)}")
        return ""