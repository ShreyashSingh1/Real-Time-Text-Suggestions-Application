# Real-Time Text Suggestion Application

A Python-based application that provides intelligent, context-aware text suggestions in real-time as users type. The system integrates powerful Large Language Models (LLMs) through LangChain and Groq to understand user intent and offer smart recommendations.

## Features

- Real-time text suggestions as you type
- WebSocket-based communication for instant feedback
- Integration with Groq LLM through LangChain
- Responsive and intuitive user interface
- Context-aware suggestions that adapt to your writing style

## Architecture

- **Frontend**: HTML, CSS, and JavaScript with WebSocket client
- **Backend**: FastAPI with WebSocket support
- **AI Integration**: LangChain with Groq LLM
- **Communication**: Real-time bidirectional WebSocket protocol

## Prerequisites

- Python 3.8 or higher
- Groq API key (or other LLM provider keys)

## Installation

1. Clone the repository

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory based on the `example.env` template and add your API keys:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

## Usage

1. Start the application:
   ```
   python app.py
   ```

2. Open your web browser and navigate to `http://localhost:8000`

3. Start typing in the text area and observe the real-time suggestions

4. Press Tab or click the "Accept Suggestion" button to accept the current suggestion

## Customization

You can customize the application by modifying the following files:

- `config.py`: Change API keys, model parameters, and server settings
- `llm_service.py`: Modify the system prompt or integrate different LLM providers
- `static/css/styles.css`: Customize the appearance of the application

## Extending the Application

This application can be extended for various use cases:

- Writing assistants
- Code completion tools
- Email composition helpers
- Learning and educational tools
- Domain-specific text generation

## License

MIT