# Sentinel - Aranea Terminal Interface

A terminal-style chat interface connected to a Gemini-powered backend with MongoDB authentication.

## Setup

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Activate the virtual environment:
```bash
source env/bin/activate
```

3. Install additional dependencies:
```bash
pip install pymongo bcrypt pydantic[email]
```

4. Configure environment variables in `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key
MONGODB_URI=your_mongodb_connection_string
```

**MongoDB URI Examples:**
- Local: `mongodb://localhost:27017/`
- Atlas: `mongodb+srv://username:password@cluster.mongodb.net/`

5. Start the backend server:
```bash
python app.py
```

The backend will run on `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies (if not already installed):
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:3000`

## Features

- ✨ Terminal-style UI with Aranea branding
- 🕷️ ASCII art spider logo
- 🔐 MongoDB-based user authentication
- 💬 Real-time chat with Gemini AI backend
- ⌨️ Elegant typing animation while waiting for responses
- 🎨 Purple and green terminal color scheme

## API Endpoints

### Authentication

**POST /auth/signup**
- Register a new user
- Body: `{ "username": "string", "email": "email@example.com", "password": "string" }`
- Validations:
  - Username: 3-30 characters, alphanumeric with underscores/hyphens
  - Email: Valid email format
  - Password: Minimum 6 characters

**POST /auth/login**
- Authenticate existing user
- Body: `{ "username": "string", "password": "string" }`
- Returns user data on success

### AI Generation

**POST /generate**
- Generate AI responses using Gemini
- Body: `{ "query": "string" }`
- Requires authenticated session (future enhancement)

## Usage

1. Ensure both backend and frontend servers are running
2. Open `http://localhost:3000` in your browser
3. Sign up for a new account or log in
4. Access the terminal interface from the home page
5. Type your message in the terminal input
6. Press Enter to send
7. Watch the typing animation while Aranea processes your request
8. Receive AI-generated responses in terminal format

## Tech Stack

**Frontend:**
- Next.js 14
- React 18
- Custom CSS with terminal aesthetics
- localStorage for session management

**Backend:**
- FastAPI
- Google Gemini AI
- MongoDB (with pymongo)
- bcrypt for password hashing
- Python 3.14

## Database Schema

### Users Collection
```json
{
  "username": "string (unique)",
  "email": "string (unique)",
  "password": "hashed_password",
  "created_at": "datetime",
  "last_login": "datetime"
}
```

## Security Features

- Password hashing with bcrypt
- Input validation using Pydantic
- Unique username and email constraints
- CORS configuration for frontend
- MongoDB unique indexes

## Development Notes

- Frontend uses localStorage for demo authentication
- Backend implements proper MongoDB authentication
- Password hashing ensures security
- Validation prevents common security issues
- Error handling provides user-friendly messages
