# Agent Builder

Simple Agent Builder with Multi-Provider Support (DeepSeek, Qwen, OpenAI, etc.)

## Quick Start

### 1. Backend

```bash
cd backend

# Install dependencies (if not already)
uv sync

# Install myauth (required for authentication)
uv pip install -e "C:\Users\17625\Documents\GitHub\my-auth"

# Start the backend server
uv run uvicorn src.agent_builder.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend

# Install dependencies (if not already)
npm install

# Start the development server
npm run dev
```

### 3. Access

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Configuration

### Environment Variables

Create a `.env` file in the `backend` directory:

```bash
# JWT Secret (at least 32 characters)
JWT_SECRET=your-production-secret-key-min-32-characters

# Database URL
DATABASE_URL=sqlite+aiosqlite:///./agent_builder.db

# myauth Database URL
MYAUTH_DB_URL=sqlite+aiosqlite:///./myauth.db

# Encryption Key for API keys
ENCRYPTION_KEY=your-32-character-encryption-key

# CORS
CORS_ORIGINS=http://localhost:3000
```

## Features

- Multi-Provider Support: DeepSeek, Qwen, OpenAI, and custom OpenAI-compatible APIs
- Custom System Prompts for each agent
- Streaming Chat Responses
- SQLite Database
- API Key Encryption
- Separate Workspace Directories for each agent

## API Endpoints

- `POST /api/providers` - Create LLM provider
- `GET /api/providers` - List providers
- `POST /api/agents` - Create agent
- `GET /api/agents` - List agents
- `POST /api/chat/{agent_id}` - Chat with agent (streaming)
