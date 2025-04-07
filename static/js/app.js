// Real-Time Text Suggestions - Frontend JavaScript

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const userInput = document.getElementById('userInput');
    const suggestionBox = document.getElementById('suggestion');
    const clearBtn = document.getElementById('clearBtn');
    const acceptBtn = document.getElementById('acceptBtn');
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    
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
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
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
        
        // Start a new timer
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