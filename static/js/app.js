// Real-Time Text Suggestions - Frontend JavaScript

document.addEventListener('DOMContentLoaded', () => {
    // Load the spell checker
    const spellChecker = window.spellChecker;
    // DOM Elements
    const userInput = document.getElementById('userInput');
    const suggestionBox = document.getElementById('suggestion');
    const clearBtn = document.getElementById('clearBtn');
    const acceptBtn = document.getElementById('acceptBtn');
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    
    // Create spell check elements
    const spellCheckContainer = document.createElement('div');
    spellCheckContainer.className = 'spell-check-container';
    spellCheckContainer.style.display = 'none';
    document.querySelector('.text-input-container').appendChild(spellCheckContainer);
    
    // WebSocket connection
    let socket;
    let typingTimer;
    const doneTypingInterval = 500; // ms - delay before sending text for suggestions
    let isConnected = false;
    
    // Connect to WebSocket
    function connectWebSocket() {
        // Get the current host and construct the WebSocket URL
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        updateConnectionStatus('connecting');
        
        socket = new WebSocket(wsUrl);
        
        // WebSocket event handlers
        socket.onopen = () => {
            console.log('WebSocket connection established');
            isConnected = true;
            updateConnectionStatus('connected');
        };
        
        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.suggestion) {
                    displaySuggestion(data.suggestion);
                }
                
                // Handle spelling corrections from backend
                if (data.spelling_correction) {
                    displaySpellingCorrection(data.spelling_correction);
                }
                
                // Display usage metrics if available
                if (data.usage) {
                    // Create or update usage info element
                    let usageInfo = document.getElementById('usageInfo');
                    if (!usageInfo) {
                        usageInfo = document.createElement('div');
                        usageInfo.id = 'usageInfo';
                        usageInfo.className = 'usage-info';
                        document.querySelector('.info-panel').appendChild(usageInfo);
                    }
                    
                    // Format the cost to 6 decimal places
                    const formattedCost = '$' + data.usage.cost.toFixed(6);
                    
                    // Update usage info content
                    usageInfo.innerHTML = `
                        <h4>Last API Call:</h4>
                        <ul>
                            <li>Input tokens: ${data.usage.input_tokens}</li>
                            <li>Output tokens: ${data.usage.output_tokens}</li>
                            <li>Cost: ${formattedCost}</li>
                            <li>Duration: ${data.usage.duration.toFixed(3)}s</li>
                        </ul>
                    `;
                    
                    // Display summary if available
                    if (data.usage_summary) {
                        const totalCost = '$' + data.usage_summary.total_cost.toFixed(6);
                        const todayCost = '$' + data.usage_summary.today_cost.toFixed(6);
                        
                        usageInfo.innerHTML += `
                            <h4>Usage Summary:</h4>
                            <ul>
                                <li>Total requests: ${data.usage_summary.total_requests}</li>
                                <li>Total cost: ${totalCost}</li>
                                <li>Today's requests: ${data.usage_summary.today_requests}</li>
                                <li>Today's cost: ${todayCost}</li>
                            </ul>
                            <p><a href="/dashboard">View detailed dashboard →</a></p>
                        `;
                    }
                }
                
                // Display error if present
                if (data.error) {
                    let errorInfo = document.getElementById('errorInfo');
                    if (!errorInfo) {
                        errorInfo = document.createElement('div');
                        errorInfo.id = 'errorInfo';
                        errorInfo.className = 'error-info';
                        document.querySelector('.info-panel').appendChild(errorInfo);
                    }
                    
                    errorInfo.innerHTML = `<p class="error-message">${data.error}</p>`;
                    
                    // Auto-hide error after 5 seconds
                    setTimeout(() => {
                        errorInfo.innerHTML = '';
                    }, 5000);
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        // Display spelling correction from backend
        function displaySpellingCorrection(correction) {
            if (!correction || !correction.original || !correction.corrected) return;
            
            // Show the spelling correction in the spell check container
            spellCheckContainer.style.display = 'block';
            spellCheckContainer.innerHTML = '';
            
            const heading = document.createElement('h4');
            heading.textContent = 'Spelling Correction:';
            spellCheckContainer.appendChild(heading);
            
            const suggestionItem = document.createElement('div');
            suggestionItem.className = 'spell-suggestion-item';
            
            const wordSpan = document.createElement('span');
            wordSpan.className = 'misspelled-word';
            wordSpan.textContent = correction.original;
            
            const arrowSpan = document.createElement('span');
            arrowSpan.textContent = ' → ';
            
            const correctionSpan = document.createElement('span');
            correctionSpan.className = 'correction';
            correctionSpan.textContent = correction.corrected;
            
            const applyButton = document.createElement('button');
            applyButton.className = 'apply-correction';
            applyButton.textContent = 'Apply';
            applyButton.onclick = () => applySpellCorrection(correction.original, correction.corrected);
            
            suggestionItem.appendChild(wordSpan);
            suggestionItem.appendChild(arrowSpan);
            suggestionItem.appendChild(correctionSpan);
            suggestionItem.appendChild(applyButton);
            
            spellCheckContainer.appendChild(suggestionItem);
        }
        
        socket.onclose = () => {
            console.log('WebSocket connection closed');
            isConnected = false;
            updateConnectionStatus('disconnected');
            
            // Try to reconnect after a delay
            setTimeout(connectWebSocket, 3000);
        };
        
        socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            isConnected = false;
            updateConnectionStatus('disconnected');
        };
    }
    
    // Update the connection status indicator
    function updateConnectionStatus(status) {
        statusIndicator.className = 'status-indicator ' + status;
        
        switch (status) {
            case 'connected':
                statusText.textContent = 'Connected';
                break;
            case 'disconnected':
                statusText.textContent = 'Disconnected';
                break;
            case 'connecting':
                statusText.textContent = 'Connecting...';
                break;
        }
    }
    
    // Display suggestion in the suggestion box
    function displaySuggestion(suggestion) {
        if (suggestion && suggestion.trim() !== '') {
            suggestionBox.textContent = suggestion;
            suggestionBox.style.display = 'block';
        } else {
            suggestionBox.textContent = '';
            suggestionBox.style.display = 'none';
        }
    }
    
    // Check spelling in the input text
    function checkSpelling() {
        const text = userInput.value;
        if (!text || !spellChecker) return;
        
        // Find misspelled words
        const misspelledWords = spellChecker.findMisspelledWords(text);
        
        // Clear previous spell check results
        spellCheckContainer.innerHTML = '';
        
        // If no misspellings found, hide the container
        if (misspelledWords.length === 0) {
            spellCheckContainer.style.display = 'none';
            return;
        }
        
        // Display misspelled words and suggestions
        spellCheckContainer.style.display = 'block';
        const heading = document.createElement('h4');
        heading.textContent = 'Spelling Suggestions:';
        spellCheckContainer.appendChild(heading);
        
        misspelledWords.forEach(item => {
            const suggestionItem = document.createElement('div');
            suggestionItem.className = 'spell-suggestion-item';
            
            const wordSpan = document.createElement('span');
            wordSpan.className = 'misspelled-word';
            wordSpan.textContent = item.word;
            
            const arrowSpan = document.createElement('span');
            arrowSpan.textContent = ' → ';
            
            const correctionSpan = document.createElement('span');
            correctionSpan.className = 'correction';
            correctionSpan.textContent = item.correction;
            
            const applyButton = document.createElement('button');
            applyButton.className = 'apply-correction';
            applyButton.textContent = 'Apply';
            applyButton.onclick = () => applySpellCorrection(item.word, item.correction);
            
            suggestionItem.appendChild(wordSpan);
            suggestionItem.appendChild(arrowSpan);
            suggestionItem.appendChild(correctionSpan);
            suggestionItem.appendChild(applyButton);
            
            spellCheckContainer.appendChild(suggestionItem);
        });
    }
    
    // Apply a spelling correction
    function applySpellCorrection(misspelled, correction) {
        const text = userInput.value;
        
        // Escape special regex characters in the misspelled word
        const escapedMisspelled = misspelled.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        
        // Use a more robust regex pattern that handles special characters
        const correctedText = text.replace(new RegExp('\\b' + escapedMisspelled + '\\b', 'g'), correction);
        userInput.value = correctedText;
        
        // Re-check spelling after correction
        checkSpelling();
        
        // Send corrected text for suggestions
        clearTimeout(typingTimer);
        typingTimer = setTimeout(sendTextForSuggestion, doneTypingInterval);
        
        // Hide the spelling correction container after applying
        spellCheckContainer.style.display = 'none';
    }
    
    // Send text to server for suggestions
    function sendTextForSuggestion() {
        const text = userInput.value.trim();
        
        if (isConnected && text.length > 0) {
            socket.send(text);
        } else {
            displaySuggestion('');
        }
    }
    
    // Accept the current suggestion
    function acceptSuggestion() {
        const suggestion = suggestionBox.textContent;
        if (suggestion && suggestion.trim() !== '') {
            userInput.value += suggestion;
            displaySuggestion('');
            userInput.focus();
        }
    }
    
    // Event Listeners
    userInput.addEventListener('input', () => {
        // Clear any previous timers
        clearTimeout(typingTimer);
        
        // Check spelling as user types
        checkSpelling();
        
        // Start a new timer for suggestions
        typingTimer = setTimeout(sendTextForSuggestion, doneTypingInterval);
    });
    
    // Handle Tab key to accept suggestion
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Tab' && suggestionBox.textContent.trim() !== '') {
            e.preventDefault(); // Prevent default tab behavior
            acceptSuggestion();
        }
    });
    
    // Clear button
    clearBtn.addEventListener('click', () => {
        userInput.value = '';
        displaySuggestion('');
        userInput.focus();
    });
    
    // Accept suggestion button
    acceptBtn.addEventListener('click', acceptSuggestion);
    
    // Initialize WebSocket connection
    connectWebSocket();
});