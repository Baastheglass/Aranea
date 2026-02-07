import uvicorn
import os
import time
import subprocess
from fastapi import FastAPI, Body, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator
from dotenv import load_dotenv
from pymetasploit3.msfrpc import MsfRpcClient
from agent import Agent
from agent_tools import Exploiter
from db import Database
from websocket_manager import ws_manager

# Load environment variables
load_dotenv()

def is_port_in_use(port):
    """Check if a port is in use"""
    result = subprocess.run(
        ["lsof", "-i", f":{port}", "-t"],
        capture_output=True,
        text=True
    )
    return bool(result.stdout.strip())

def kill_process_on_port(port):
    """Kill any process using the specified port"""
    result = subprocess.run(
        ["lsof", "-i", f":{port}", "-t"],
        capture_output=True,
        text=True
    )
    pids = result.stdout.strip().split('\n')
    for pid in pids:
        if pid:
            print(f"Killing process {pid} on port {port}")
            subprocess.run(["kill", "-9", pid])
    time.sleep(2)  # Wait for processes to fully terminate

# Initialize msfrpcd and MsfRpcClient at startup
password = os.getenv("MSF_RPC_PASSWORD")
port = os.getenv("MSF_RPC_PORT", "55552")

# First, kill any existing msfrpcd processes
print("Checking for existing msfrpcd processes...")
os.system("pkill -9 -f msfrpcd")
time.sleep(2)

# Also kill anything on the RPC port
if is_port_in_use(port):
    print(f"Port {port} is in use, killing process...")
    kill_process_on_port(port)

# Now start msfrpcd
print(f"Starting msfrpcd on port {port}...")
cmd = f"msfrpcd -P {password} -p {port} -a 127.0.0.1"
ret = os.system(cmd)
if ret == 0:
    print("✓ msfrpcd started successfully")
else:
    print(f"⚠ msfrpcd exited with code {ret}")

# Wait for msfrpcd to fully start
print("Waiting for msfrpcd to initialize...")
time.sleep(5)

# Initialize MsfRpcClient with retry logic
msf_client = None
max_retries = 3
retry_delay = 3

for attempt in range(max_retries):
    try:
        print(f"Attempting to connect to msfrpcd (attempt {attempt + 1}/{max_retries})...")
        msf_client = MsfRpcClient(password, port=int(port), ssl=True)
        print("✓ MsfRpcClient initialized successfully")
        break
    except Exception as e:
        print(f"⚠ Connection attempt {attempt + 1} failed: {e}")
        if attempt < max_retries - 1:
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        else:
            print("✗ Failed to connect to msfrpcd after all retries")
            print("⚠ Starting server without Metasploit functionality...")
            msf_client = None

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services with msfrpcd client (may be None if connection failed)
if msf_client:
    exploiter = Exploiter(msf_client)
    agent = Agent(exploiter=exploiter)
else:
    print("⚠ Starting with limited functionality (no Metasploit)")
    exploiter = None
    agent = Agent(exploiter=None)
    
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

class CreateChatRequest(BaseModel):
    username: str
    title: str = None

class SaveMessageRequest(BaseModel):
    chat_id: str
    sender: str
    text: str

class UpdateChatTitleRequest(BaseModel):
    chat_id: str
    title: str

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

# Chat management endpoints
@app.post("/chats/create")
async def create_chat(request: CreateChatRequest):
    """
    Create a new chat session for a user
    """
    success, message, chat_data = db.create_chat(request.username, request.title)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": message,
        "chat": chat_data
    }

@app.get("/chats/{username}")
async def get_user_chats(username: str):
    """
    Get all chat sessions for a user
    """
    chats = db.get_user_chats(username)
    return {
        "success": True,
        "chats": chats
    }

@app.get("/chats/{chat_id}/messages")
async def get_chat_messages(chat_id: str):
    """
    Get all messages for a specific chat
    """
    messages = db.get_chat_messages(chat_id)
    return {
        "success": True,
        "messages": messages
    }

@app.post("/chats/message")
async def save_message(request: SaveMessageRequest):
    """
    Save a message to a chat
    """
    success, message, message_data = db.save_message(
        request.chat_id,
        request.sender,
        request.text
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": message,
        "message_data": message_data
    }

@app.put("/chats/title")
async def update_chat_title(request: UpdateChatTitleRequest):
    """
    Update the title of a chat
    """
    success, message = db.update_chat_title(request.chat_id, request.title)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": message
    }

@app.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str):
    """
    Delete a chat and all its messages
    """
    success, message = db.delete_chat(chat_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": message
    }

# Existing endpoint
@app.post("/generate")
async def generate_content(query: str = Body(..., embed=True)):
    response = agent.generate(query)
    return {"response": response}

# WebSocket endpoint
@app.websocket("/ws/{username}/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, username: str, chat_id: str):
    session_id = f"{username}_{chat_id}"
    await ws_manager.connect(websocket, session_id)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Handle the message based on type
            if data.get("type") == "query":
                query = data.get("message")
                
                # Save user message to database
                db.save_message(chat_id, username, query)
                
                # Agent handles all event emissions internally and saves its response to DB
                await agent.respond(
                    query,
                    ws_manager=ws_manager,
                    session_id=session_id,
                    db=db,
                    chat_id=chat_id,
                    username=username
                )
    
    except WebSocketDisconnect:
        ws_manager.disconnect(session_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        ws_manager.disconnect(session_id)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)