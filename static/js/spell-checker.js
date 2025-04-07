/**
 * Client-side spell checker for real-time text suggestions
 * This module provides spell checking functionality for the frontend
 */

class ClientSpellChecker {
    constructor() {
        // Common misspelled words and their corrections
        this.dictionary = {
            // Common misspellings
            'teh': 'the',
            'adn': 'and',
            'taht': 'that',
            'waht': 'what',
            'wiht': 'with',
            'becuase': 'because',
            'recieve': 'receive',
            'thier': 'their',
            'theyre': 'they\'re',
            'definately': 'definitely',
            'seperate': 'separate',
            'occured': 'occurred',
            'alot': 'a lot',
            'untill': 'until',
            'accross': 'across',
            'beleive': 'believe',
            'suprise': 'surprise',
            'tommorow': 'tomorrow',
            'wierd': 'weird',
            'reccomend': 'recommend',
            'accomodate': 'accommodate',
            'occurence': 'occurrence',
            'neccessary': 'necessary',
            'embarass': 'embarrass',
            'goverment': 'government',
            'proffesional': 'professional',
            'similiar': 'similar',
            'acheive': 'achieve',
            'begining': 'beginning',
            'concious': 'conscious',
            'enviroment': 'environment',
            'existance': 'existence',
            'foriegn': 'foreign',
            'independant': 'independent',
            'liason': 'liaison',
            'maintainance': 'maintenance',
            'millenium': 'millennium',
            'occassion': 'occasion',
            'prefered': 'preferred',
            'priviledge': 'privilege',
            'truely': 'truly',
            'wether': 'whether'
        };
        
        // Words to ignore (technical terms, abbreviations, etc.)
        this.ignoreList = [
            'api', 'json', 'html', 'css', 'js', 'url', 'http', 'https',
            'npm', 'git', 'ui', 'ux', 'sdk', 'xml', 'ajax', 'dom', 'sql',
            'php', 'npm', 'cli', 'gui', 'api', 'ftp', 'ssl', 'ssh', 'tcp',
            'ip', 'dns', 'cpu', 'gpu', 'ram', 'ssd', 'hdd', 'os', 'ide'
        ];
    }

    /**
     * Check if a word is misspelled
     * @param {string} word - The word to check
     * @returns {boolean} - True if the word is misspelled, false otherwise
     */
    isMisspelled(word) {
        // Ignore short words (1-2 characters)
        if (word.length <= 2) return false;
        
        // Ignore words with numbers
        if (/\d/.test(word)) return false;
        
        // Ignore capitalized words (likely proper nouns)
        if (word[0] === word[0].toUpperCase() && word.length > 1) return false;
        
        // Ignore words in the ignore list
        if (this.ignoreList.includes(word.toLowerCase())) return false;
        
        // Check if the word is in our dictionary of common misspellings
        return this.dictionary.hasOwnProperty(word.toLowerCase());
    }

    /**
     * Get the correction for a misspelled word
     * @param {string} word - The misspelled word
     * @returns {string|null} - The correction or null if no correction is found
     */
    getCorrection(word) {
        return this.dictionary[word.toLowerCase()] || null;
    }

    /**
     * Find misspelled words in a text
     * @param {string} text - The text to check
     * @returns {Array} - Array of objects with misspelled words and their positions
     */
    findMisspelledWords(text) {
        const words = text.match(/\b[a-zA-Z]+\b/g) || [];
        const misspellings = [];
        
        for (const word of words) {
            if (this.isMisspelled(word)) {
                const correction = this.getCorrection(word);
                const startIndex = text.indexOf(word);
                
                misspellings.push({
                    word: word,
                    correction: correction,
                    startIndex: startIndex,
                    endIndex: startIndex + word.length
                });
            }
        }
        
        return misspellings;
    }
}

// Export the spell checker
const spellChecker = new ClientSpellChecker();