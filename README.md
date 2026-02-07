# ARANEA - AI-Powered Penetration Testing Platform

🕷️ **Aranea** is an advanced conversational AI penetration testing platform that combines natural language processing with industry-standard security tools. Talk to your pentesting tools through an elegant terminal interface.

## Overview

### What is ARANEA?

ARANEA transforms complex penetration testing workflows into natural conversations. Instead of memorizing command syntax for dozens of tools, simply ask Aranea what you want to do, and it orchestrates the appropriate security tools, formats the results, and generates professional reports.

### How It Works

**Architecture Flow:**

```
User (Natural Language) 
    ↓
Terminal UI (Next.js + WebSocket)
    ↓
FastAPI Backend + AI Agent (Gemini 2.5)
    ↓
Tool Orchestration Layer
    ├─ Scanner (Masscan, RustScan, Nmap)
    ├─ Exploiter (Metasploit Framework)
    ├─ OSINT (Shodan)
    └─ Attacker (hping3)
    ↓
MongoDB (Session Storage)
    ↓
DocumenterAgent (Report Generation)
```

**Example Interaction:**
```bash
user@web:~$ Scan the network
aranea@web:~$ Scanning 192.168.1.0/24 with Masscan...
[Results formatted as table with 12 hosts discovered]

user@web:~$ Check port 3306 on 192.168.1.50
aranea@web:~$ Scanning port 3306... MySQL 5.0.45 detected
⚠️ Old version - searching for exploits...
[Lists 8 Metasploit modules with CVE references]
```

### Key Features

- 🤖 **AI-Powered Orchestration** - Natural language commands execute complex tool chains
- 🔍 **Multi-Tool Integration** - Masscan, RustScan, Nmap, Metasploit, Shodan, hping3
- 💬 **Real-Time WebSocket** - Live feedback during scans and exploits
- 📊 **Intelligent Formatting** - Raw tool output → Markdown tables with recommendations
- 📄 **Automated Reporting** - AI-generated PDF reports (OWASP/PTES compliant)
- 🔐 **Multi-User Support** - Isolated workspaces with MongoDB persistence
- 🕷️ **Terminal Aesthetic** - Retro terminal UI with modern UX

---

## Setup

### Prerequisites

**System Requirements:**
- macOS or Linux (Windows limited support)
- Python 3.10+
- Node.js 18+
- MongoDB (local or Atlas)
- Metasploit Framework
- Root/sudo access for network tools

**Required Tools:**
```bash
# Install security tools (macOS with Homebrew)
brew install masscan nmap hping
brew install --cask metasploit

# Or on Linux (Debian/Ubuntu)
sudo apt update
sudo apt install masscan nmap hping3 metasploit-framework

# RustScan (https://github.com/RustScan/RustScan)
# Follow installation instructions for your OS
```

---

### 1. Configure Sudo Access for Network Tools

Network scanning tools require root privileges. Configure passwordless sudo for specific commands:

```bash
sudo visudo
```

Add these lines at the end of the file:
```
# Allow passwordless sudo for pentesting tools
your_username ALL=(ALL) NOPASSWD: /usr/local/bin/masscan
your_username ALL=(ALL) NOPASSWD: /usr/bin/masscan
your_username ALL=(ALL) NOPASSWD: /usr/local/bin/hping
your_username ALL=(ALL) NOPASSWD: /usr/sbin/hping3
your_username ALL=(ALL) NOPASSWD: /usr/bin/hping3
```

Replace `your_username` with your actual username.

**Verify:**
```bash
sudo masscan --version  # Should not prompt for password
sudo hping3 --version   # Should not prompt for password
```

---

### 2. Setup MongoDB

**Option A - Local MongoDB:**
```bash
# macOS
brew install mongodb-community
brew services start mongodb-community

# Linux
sudo apt install mongodb
sudo systemctl start mongodb
```

**Option B - MongoDB Atlas (Cloud):**
1. Create free account at https://www.mongodb.com/cloud/atlas
2. Create a cluster
3. Get connection string: `mongodb+srv://<user>:<pass>@cluster.mongodb.net/`

---

### 3. Setup Metasploit RPC Daemon

Metasploit must run as an RPC server for programmatic access:

**Start msfrpcd:**
```bash
# Set a strong password
export MSF_PASSWORD="your_secure_password_here"

# Start the RPC daemon
msfrpcd -P $MSF_PASSWORD -p 55552 -a 127.0.0.1 -S
```

**Alternative - Auto-start on login (macOS):**
Create `~/Library/LaunchAgents/com.metasploit.msfrpcd.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.metasploit.msfrpcd</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/metasploit-framework/bin/msfrpcd</string>
        <string>-P</string>
        <string>your_password</string>
        <string>-p</string>
        <string>55552</string>
        <string>-a</string>
        <string>127.0.0.1</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

Load it: `launchctl load ~/Library/LaunchAgents/com.metasploit.msfrpcd.plist`

**Verify msfrpcd is running:**
```bash
lsof -i :55552  # Should show msfrpcd listening
```

---

### 4. Backend Setup

**1. Navigate to backend directory:**
```bash
cd backend
```

**2. Activate virtual environment:**
```bash
source env/bin/activate
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Configure environment variables:**

Create `.env` file in `backend/` directory:
```env
# Google Gemini AI (Required)
GOOGLE_API_KEY=your_gemini_api_key_here
GOOGLE_DOCUMENTER_API_KEY=your_second_gemini_key_here

# MongoDB (Required)
MONGODB_URI=mongodb://localhost:27017/

# Metasploit RPC (Required)
MSF_RPC_PASSWORD=your_secure_password_here
MSF_RPC_PORT=55552

# Shodan OSINT (Optional but recommended)
SHODAN_COOKIE_NAME=polito
SHODAN_COOKIE=your_shodan_session_cookie_value
```

**How to get each variable:**

**Google Gemini API Keys:**
1. Go to https://aistudio.google.com/app/apikey
2. Create two API keys (one for main agent, one for documenter)
3. Copy both keys into `.env`

**MongoDB URI:**
- Local: `mongodb://localhost:27017/`
- Atlas: `mongodb+srv://username:password@cluster.mongodb.net/`

**Metasploit RPC:**
- Use the same password you set when starting msfrpcd
- Default port is 55552

**Shodan Cookie (Optional):**
1. Sign up at https://www.shodan.io
2. Log in to your account
3. Open browser DevTools → Application/Storage → Cookies
4. Find cookie named `polito` and copy its value
5. Paste into `.env`

**5. Start the backend server:**
```bash
python app.py
```

Backend will run on `http://localhost:8000`

**Expected output:**
```
✓ msfrpcd started successfully
✓ MsfRpcClient initialized successfully
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### 5. Frontend Setup

**1. Navigate to frontend directory:**
```bash
cd frontend
```

**2. Install dependencies:**
```bash
npm install
```

**3. Start development server:**
```bash
npm run dev
```

Frontend will run on `http://localhost:3000`

---

### 6. Verify Installation

**Test backend health:**
```bash
curl http://localhost:8000/
```

**Test Metasploit connection:**
```python
python3 << EOF
from pymetasploit3.msfrpc import MsfRpcClient
client = MsfRpcClient('your_password', port=55552, ssl=True)
print(f"✓ Connected! Exploits available: {len(client.modules.exploits)}")
EOF
```

**Test complete flow:**
1. Open browser to `http://localhost:3000`
2. Sign up for an account
3. Create a new chat
4. Type: "What can you do?"
5. Aranea should list available capabilities

---

## Usage

### Basic Commands

**Reconnaissance:**
```bash
Scan the network
Scan 192.168.1.100
Check port 80 on 192.168.1.50
Find servers for google.com
```

**Exploitation:**
```bash
Find vulnerabilities for MySQL
Run vsftpd exploit on 192.168.1.50
Show active sessions
Execute whoami on session 1
```

**Stress Testing:**
```bash
Flood 192.168.1.100 port 80
Stop flood attack on 192.168.1.100:80
Show active attacks
```

**Documentation:**
```bash
Generate a penetration test report
Show engagement summary
```

### Available Functions

**Scanner Module:**
- `scan_entire_network()` - Network-wide host discovery
- `scan_target(ip_address)` - Comprehensive port scan
- `scan_specific_port(ip_address, port)` - Detailed service analysis
- `get_ip_of_website(website)` - DNS resolution
- `find_website_servers(hostname)` - Shodan OSINT

**Exploiter Module:**
- `find_vulnerabilities_for_service(service_name)` - Search Metasploit DB
- `run_exploit(exploit_name, target_ip, options)` - Execute exploit
- `get_sessions()` - List active sessions
- `execute_command(session_id, command)` - Run command on compromised host
- `stop_session(session_id)` - Terminate session

**Attacker Module:**
- `flood(target_ip, target_port)` - Launch DDoS attack
- `stop_flood(attack_id)` - Stop attack
- `list_active_attacks()` - Show running attacks

**Documenter Module:**
- `generate_pentest_report(engagement_info)` - Create PDF report
- `get_engagement_summary()` - Quick statistics

---

## Architecture

### Technology Stack

**Frontend:**
- Next.js 13+ (React framework)
- WebSocket client for real-time communication
- react-markdown for result rendering
- Custom CSS modules for terminal styling

**Backend:**
- Python 3.10+ (FastAPI framework)
- Uvicorn (ASGI server)
- PyMetasploit3 (Metasploit RPC client)
- Selenium + BeautifulSoup (Shodan scraping)

**AI/ML:**
- Google Gemini 2.5 Flash
- Function calling API
- Multi-agent architecture (MainAgent + DocumenterAgent)

**Database:**
- MongoDB (document store)
- Collections: users, chats, messages
- PyMongo driver

**Security Tools:**
- Masscan (network discovery)
- RustScan (port scanning)
- Nmap (service enumeration)
- Metasploit Framework (exploitation)
- hping3 (stress testing)
- Shodan (OSINT)

### File Structure

```
Sentinel/
├── backend/
│   ├── agent.py              # Main AI agent and DocumenterAgent
│   ├── agent_tools.py        # Scanner, Exploiter, Attacker classes
│   ├── app.py                # FastAPI server and routes
│   ├── db.py                 # MongoDB interface
│   ├── constants.py          # AI prompts and system instructions
│   ├── websocket_manager.py  # WebSocket connection management
│   ├── shodan_search.py      # Shodan web scraper
│   ├── requirements.txt      # Python dependencies
│   └── .env                  # Environment variables (create this)
│
├── frontend/
│   ├── components/
│   │   ├── ChatInterface.js  # Main chat terminal UI
│   │   ├── ChatSidebar.js    # Chat navigation sidebar
│   │   └── AuthForm.js       # Login/signup forms
│   ├── pages/
│   │   ├── index.js          # Landing page
│   │   ├── login.js          # Login page
│   │   ├── signup.js         # Signup page
│   │   └── chat.js           # Main application
│   ├── styles/
│   │   └── globals.css       # Terminal theme styles
│   └── package.json
│
└── README.md
```

---

## API Endpoints

### Authentication
- `POST /auth/signup` - Register new user
- `POST /auth/login` - Authenticate user

### Chat Management
- `GET /chats/{username}` - List user's chats
- `POST /chats/{username}` - Create new chat
- `PUT /chats/{chat_id}` - Update chat title
- `DELETE /chats/{chat_id}` - Delete chat
- `GET /chats/{chat_id}/messages` - Get chat history

### AI Interaction
- `WS /ws/{username}/{chat_id}` - WebSocket for real-time chat
- `POST /generate` - Direct API call (non-WebSocket)

### Reporting
- `GET /chats/{chat_id}/report` - Generate and download PDF report

---

## Security Considerations

⚠️ **IMPORTANT:** This is a penetration testing tool. Use responsibly and ethically.

**Best Practices:**
- Only test systems you own or have written authorization to test
- Keep MongoDB credentials secure
- Use strong passwords for MSF RPC
- Never expose the backend API to the public internet
- Run in isolated network environments for testing
- Follow responsible disclosure for any vulnerabilities found

**Built-in Safeguards:**
- Authentication required for all operations
- MongoDB stores complete audit trails
- AI prompts include ethical guidelines
- Session-based isolation between users

---

## Troubleshooting

**"WebSocket not connected"**
- Verify backend is running on port 8000
- Check browser console for connection errors
- Ensure no firewall blocking WebSocket connections

**"msfrpcd connection failed"**
- Verify msfrpcd is running: `lsof -i :55552`
- Check password matches in .env file
- Try restarting msfrpcd: `pkill msfrpcd && msfrpcd -P <password> -p 55552 -a 127.0.0.1`

**"Permission denied" for scans**
- Verify sudo visudo configuration
- Test: `sudo masscan --version` (should not ask for password)
- Check tool paths in visudo match actual install locations

**Shodan results not working**
- Cookie may have expired - get new one from browser
- Check SHODAN_COOKIE value in .env
- Try testing Shodan manually in browser while logged in

**MongoDB connection issues**
- Verify MongoDB is running: `mongosh` or `mongo`
- Check MONGODB_URI format in .env
- For Atlas, ensure IP whitelist includes your IP

---

## Contributing

This is an educational/research project. Contributions welcome for:
- Additional tool integrations
- Improved result formatting
- Enhanced reporting templates
- Bug fixes and security improvements

---

## License

Educational and research purposes only. Always obtain proper authorization before conducting security testing.

---

## Acknowledgments

Built with:
- Google Gemini AI
- Metasploit Framework
- MongoDB
- FastAPI
- Next.js
- And the entire open-source security community
