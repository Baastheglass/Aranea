import uvicorn
import os
import re
import time
import subprocess
from fastapi import FastAPI, Body, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, field_validator
from dotenv import load_dotenv
from pymetasploit3.msfrpc import MsfRpcClient
from agent import Agent, DocumenterAgent
from agent_tools import Exploiter
from db import Database
from websocket_manager import ws_manager
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.pdfgen import canvas
from datetime import datetime
from bson import ObjectId
import tempfile

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
    allow_origins=[
        "http://localhost:3000",
        "https://aranea.vercel.app"
    ],
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

@app.get("/chats/{chat_id}/report")
async def generate_report(chat_id: str):
    """
    Generate a pentesting report PDF for a specific chat using DocumenterAgent
    """
    print(f"[REPORT] Starting report generation for chat ID: {chat_id}")
    
    # Check if chat exists - convert string chat_id to ObjectId for MongoDB query
    try:
        chat_object_id = ObjectId(chat_id)
        print(f"[REPORT] Converted chat_id to ObjectId: {chat_object_id}")
    except Exception as e:
        print(f"[REPORT] ERROR - Invalid chat ID format: {e}")
        raise HTTPException(status_code=400, detail="Invalid chat ID format")
    
    print(f"[REPORT] Fetching chat from database...")
    chat = db.chats.find_one({"_id": chat_object_id})
    if not chat:
        print(f"[REPORT] ERROR - Chat not found")
        raise HTTPException(status_code=404, detail="Chat not found")
    print(f"[REPORT] Chat found: {chat.get('title', 'Untitled')}")
    
    print(f"[REPORT] Fetching chat messages...")
    messages = db.get_chat_messages(chat_id)
    if not messages:
        print(f"[REPORT] ERROR - Chat has no messages")
        raise HTTPException(status_code=404, detail="Chat has no messages")
    print(f"[REPORT] Found {len(messages)} messages")
    
    # Use DocumenterAgent to generate the report content
    print(f"[REPORT] Initializing DocumenterAgent...")
    documenter = DocumenterAgent()
    
    # Prepare engagement info
    engagement_info = {
        'chat_title': chat.get('title', 'Untitled Chat'),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'tester': 'Aranea Security Team',
        'client': 'Client Organization',
        'engagement_type': 'AI-Assisted Penetration Testing'
    }
    print(f"[REPORT] Engagement info prepared: {engagement_info['chat_title']}")
    
    # Generate markdown report using AI
    try:
        print(f"[REPORT] Generating markdown report with AI...")
        markdown_report = documenter.generate_report(db, chat_id, engagement_info)
        print(f"[REPORT] Markdown report generated ({len(markdown_report)} characters)")
    except Exception as e:
        print(f"[REPORT] ERROR - Failed to generate report with DocumenterAgent: {e}")
        import traceback
        print(f"[REPORT] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")
    
    # Create PDF from markdown
    print(f"[REPORT] Creating temporary PDF file...")
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf_path = temp_pdf.name
    temp_pdf.close()
    print(f"[REPORT] PDF path: {pdf_path}")
    
    # Convert markdown to PDF
    print(f"[REPORT] Initializing PDF document...")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Define custom styles
    print(f"[REPORT] Defining custom styles...")
    
    # Professional color scheme
    primary_color = colors.HexColor('#1E3A8A')  # Deep blue
    secondary_color = colors.HexColor('#3B82F6')  # Bright blue
    accent_color = colors.HexColor('#60A5FA')  # Light blue
    danger_color = colors.HexColor('#DC2626')  # Red for critical
    warning_color = colors.HexColor('#F59E0B')  # Orange for high
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=primary_color,
        spaceAfter=24,
        spaceBefore=0,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=34
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=primary_color,
        spaceAfter=10,
        spaceBefore=16,
        fontName='Helvetica-Bold',
        borderWidth=0,
        borderPadding=0,
        borderColor=primary_color,
        leftIndent=0
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=secondary_color,
        spaceAfter=8,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=8,
        alignment=TA_LEFT,
        fontName='Helvetica',
        leading=14
    )
    
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=body_style,
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=4
    )
    
    code_style = ParagraphStyle(
        'CustomCode',
        parent=styles['Code'],
        fontSize=8,
        textColor=colors.HexColor('#374151'),
        spaceAfter=8,
        fontName='Courier',
        backColor=colors.HexColor('#F3F4F6'),
        leftIndent=15,
        rightIndent=15,
        borderWidth=1,
        borderColor=colors.HexColor('#D1D5DB'),
        borderPadding=8,
        leading=11
    )
    
    info_box_style = ParagraphStyle(
        'InfoBox',
        parent=body_style,
        backColor=colors.HexColor('#EFF6FF'),
        borderWidth=1,
        borderColor=accent_color,
        borderPadding=10,
        leftIndent=10,
        rightIndent=10,
        spaceAfter=12
    )
    
    # Add cover page elements
    print(f"[REPORT] Creating cover page...")
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph("PENETRATION TESTING REPORT", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Add engagement info box
    info_data = [
        ['Client:', engagement_info.get('client', 'N/A')],
        ['Date:', engagement_info.get('date', 'N/A')],
        ['Tester:', engagement_info.get('tester', 'N/A')],
        ['Engagement Type:', engagement_info.get('engagement_type', 'N/A')]
    ]
    
    info_table = Table(info_data, colWidths=[1.5*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#EFF6FF')),
        ('TEXTCOLOR', (0, 0), (0, -1), primary_color),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BFDBFE')),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(PageBreak())
    
    # Parse markdown and convert to PDF elements
    print(f"[REPORT] Parsing markdown and converting to PDF elements...")
    lines = markdown_report.split('\n')
    in_code_block = False
    code_content = []
    line_count = 0
    section_count = 0
    
    for line in lines:
        line_count += 1
        line = line.rstrip()
        
        # Handle code blocks
        if line.startswith('```'):
            if in_code_block:
                # End code block
                if code_content:
                    code_text = '\n'.join(code_content)
                    # Escape special characters for XML
                    code_text = code_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    code_text = code_text.replace('\n', '<br/>')
                    elements.append(Paragraph(code_text, code_style))
                    elements.append(Spacer(1, 6))
                code_content = []
                in_code_block = False
            else:
                # Start code block
                in_code_block = True
            continue
        
        if in_code_block:
            code_content.append(line)
            continue
        
        # Skip empty lines
        if not line.strip():
            elements.append(Spacer(1, 6))
            continue
        
        try:
            # Parse markdown headers
            if line.startswith('# '):
                text = line[2:].strip()
                text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                # Skip the first title as we added it in cover page
                if line_count > 1:
                    elements.append(Paragraph(text, title_style))
            elif line.startswith('## '):
                section_count += 1
                text = line[3:].strip()
                text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                # Add section separator line
                elements.append(Spacer(1, 12))
                elements.append(Paragraph(f"{section_count}. {text}", heading_style))
                # Add horizontal line under heading
                elements.append(Spacer(1, 2))
            elif line.startswith('### '):
                text = line[4:].strip()
                text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                elements.append(Paragraph(text, subheading_style))
            elif line.startswith('- ') or line.startswith('* '):
                # Bullet point
                text = line[2:].strip()
                text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                # Handle inline bold with proper regex
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                elements.append(Paragraph(f"• {text}", bullet_style))
            elif line.startswith('**') and line.endswith('**') and line.count('**') == 2:
                # Bold text (simple case - entire line)
                text = line[2:-2]
                text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                bold_style = ParagraphStyle('Bold', parent=body_style, fontName='Helvetica-Bold')
                elements.append(Paragraph(text, bold_style))
            else:
                # Regular paragraph
                text = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                # Handle inline bold with proper regex - match **text** patterns
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                elements.append(Paragraph(text, body_style))
        except Exception as e:
            print(f"[REPORT] ERROR parsing line {line_count}: {line[:100]}")
            print(f"[REPORT] Error: {e}")
            # Skip problematic lines instead of crashing
            continue
    
    print(f"[REPORT] Parsed {line_count} lines, created {len(elements)} PDF elements")
    
    # Build PDF
    try:
        print(f"[REPORT] Building PDF document...")
        doc.build(elements)
        print(f"[REPORT] PDF built successfully")
    except Exception as e:
        print(f"[REPORT] ERROR building PDF: {e}")
        import traceback
        print(f"[REPORT] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to build PDF: {str(e)}")
    
    # Return the PDF file
    filename = f"pentest_report_{chat.get('title', 'chat').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    print(f"[REPORT] Returning PDF file: {filename}")
    return FileResponse(
        pdf_path,
        media_type='application/pdf',
        filename=filename
    )

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