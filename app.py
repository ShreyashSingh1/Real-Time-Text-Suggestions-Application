import json
import logging
from typing import List, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from llm_service import get_text_suggestions, cost_tracker
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Real-Time Text Suggestions")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Remaining connections: {len(self.active_connections)}")

    async def send_suggestion(self, websocket: WebSocket, response):
        # If response is a string (for backward compatibility), convert to dict
        if isinstance(response, str):
            response = {"suggestion": response}
        await websocket.send_text(json.dumps(response))

manager = ConnectionManager()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """Serve the API usage dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/usage")
async def get_api_usage():
    """API endpoint to get usage data for the dashboard"""
    # Get complete usage data for dashboard
    usage_data = cost_tracker.usage_data
    
    # Ensure the API calls are sorted by timestamp (newest first)
    usage_data["api_calls"] = sorted(
        usage_data["api_calls"], 
        key=lambda x: x["timestamp"], 
        reverse=True
    )
    
    # Return the data as JSON
    return JSONResponse(content=usage_data)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received text: {data[:20]}..." if len(data) > 20 else f"Received text: {data}")
            
            # Process the text and get suggestions
            response = await get_text_suggestions(data)
            
            # Send response back to the client
            await manager.send_suggestion(websocket, response)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {str(e)}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG_MODE
    )