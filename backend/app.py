import uvicorn
from fastapi import FastAPI, Body, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator
from agent import Agent
from db import Database
from websocket_manager import ws_manager

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
agent = Agent()
db = Database()

# Pydantic models for request validation
class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 30:
            raise ValueError('Username must be less than 30 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class LoginRequest(BaseModel):
    username: str
    password: str
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v:
            raise ValueError('Username is required')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not v:
            raise ValueError('Password is required')
        return v

# Authentication endpoints
@app.post("/auth/signup")
async def signup(request: SignupRequest):
    """
    Register a new user
    """
    success, message, user_data = db.create_user(
        request.username,
        request.email,
        request.password
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": message,
        "user": user_data
    }

@app.post("/auth/login")
async def login(request: LoginRequest):
    """
    Authenticate existing user
    """
    success, message, user_data = db.authenticate_user(
        request.username,
        request.password
    )
    
    if not success:
        raise HTTPException(status_code=401, detail=message)
    
    return {
        "success": True,
        "message": message,
        "user": user_data
    }

# Existing endpoint
@app.post("/generate")
async def generate_content(query: str = Body(..., embed=True)):
    response = agent.generate(query)
    return {"response": response}

# WebSocket endpoint
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await ws_manager.connect(websocket, session_id)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Handle the message based on type
            if data.get("type") == "query":
                query = data.get("message")
                
                # Agent handles all event emissions internally
                await agent.respond(query, ws_manager=ws_manager, session_id=session_id)
    
    except WebSocketDisconnect:
        ws_manager.disconnect(session_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        ws_manager.disconnect(session_id)
        print(f"WebSocket error: {e}")
        ws_manager.disconnect(session_id)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)