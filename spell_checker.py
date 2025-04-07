import logging
import re
from typing import Optional, List
from spellchecker import SpellChecker as PySpellChecker

import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class SpellChecker:
    """A class to handle spell checking and correction functionality"""
    
    def __init__(self):
        """Initialize the spell checker"""
        try:
            self.checker = PySpellChecker()
            self.is_available = True
            logger.info("Spell checker initialized successfully")
        except Exception as e:
            self.is_available = False
            logger.error(f"Failed to initialize spell checker: {str(e)}")
    
    def correct_text(self, text: str) -> str:
        """Correct spelling errors in the provided text
        
        Args:
            text: The input text to check for spelling errors
            
        Returns:
            The corrected text with spelling errors fixed
        """
        if not self.is_available:
            return text
        
        # Split text into words while preserving punctuation and spacing
        words_with_positions = self._tokenize_with_positions(text)
        
        # Create a new text with corrections
        result = list(text)
        
        # Process words in reverse order to avoid position shifts
        for word, start, end in reversed(words_with_positions):
            # Skip very short words, numbers, and special terms
            if len(word) <= 2 or word.isdigit() or self._is_special_term(word):
                continue
                
            corrected = self.correct_word(word)
            if corrected != word:
                # Replace the misspelled word with its correction
                result[start:end] = corrected
        
        return ''.join(result)
    
    def correct_word(self, word: str) -> str:
        """Correct a single word if it's misspelled
        
        Args:
            word: The word to check and potentially correct
            
        Returns:
            The corrected word or the original if no correction needed
        """
        if not self.is_available:
            return word
            
        # Preserve capitalization
        is_capitalized = word[0].isupper() if word else False
        
        # Convert to lowercase for spell checking
        word_lower = word.lower()
        
        # Check if the word is misspelled
        if self.checker.unknown([word_lower]):
            correction = self.checker.correction(word_lower)
            if correction and correction != word_lower:
                # Restore original capitalization
                if is_capitalized:
                    correction = correction.capitalize()
                return correction
        
        return word
    
    def _tokenize_with_positions(self, text: str) -> List[tuple]:
        """Split text into words with their positions
        
        Args:
            text: The input text
            
        Returns:
            List of tuples (word, start_pos, end_pos)
        """
        words_with_positions = []
        # Find all words in the text
        for match in re.finditer(r'\b[a-zA-Z]+\b', text):
            word = match.group(0)
            start_pos = match.start()
            end_pos = match.end()
            
            # Skip words that are too short based on config
            if len(word) < config.SPELL_CHECK_MIN_WORD_LENGTH:
                continue
                
            # Skip capitalized words if configured to do so (likely proper nouns)
            if config.SPELL_CHECK_IGNORE_CAPITALIZED and word[0].isupper():
                continue
                
            words_with_positions.append((word, start_pos, end_pos))
        return words_with_positions
    
    def _is_special_term(self, word: str) -> bool:
        """Check if the word is a special term that should not be corrected
        
        Args:
            word: The word to check
            
        Returns:
            True if the word is a special term, False otherwise
        """
        # List of terms to ignore (e.g., technical terms, abbreviations)
        special_terms = {'api', 'json', 'html', 'css', 'js', 'url', 'http', 'https'}
        return word.lower() in special_terms

# Create a singleton instance
spell_checker = SpellChecker()

def correct_spelling(text: str) -> str:
    """Correct spelling errors in the provided text
    
    Args:
        text: The input text to check for spelling errors
        
    Returns:
        The corrected text with spelling errors fixed
    """
    # Skip spell checking if disabled in config or if text is empty
    if not config.ENABLE_SPELL_CHECK or not text or len(text.strip()) == 0:
        return text
    
    try:
        return spell_checker.correct_text(text)
    except Exception as e:
        logger.error(f"Error in spell correction: {str(e)}")
        # In case of any error, return the original text
        return text