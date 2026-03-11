# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Market Service** - Data/Document/Skill Market for Agents

- **Backend**: FastAPI + SQLAlchemy (async) + SQLite
- **Auth**: my-auth framework
- **Access**: OpenClaw Agent via lab-tools plugin

## Architecture

```
OpenClaw (Agent) ←→ Market Service API ←→ lab-tools plugin
                           (FastAPI)
```

## Commands

### Backend

```bash
cd backend

# Install dependencies
uv sync

# Install myauth (editable mode) - required for auth
uv pip install -e "C:\Users\17625\Documents\GitHub\my-auth"

# Install pandas for data analysis
uv pip install pandas pyarrow

# Run development server
uv run uvicorn src.agent_builder.main:app --reload --port 8000
```

### Access

- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Environment Variables

### Backend (.env)

```
JWT_SECRET=your-32-character-secret-key
DATABASE_URL=sqlite+aiosqlite:///./agent_builder.db
MYAUTH_DB_URL=sqlite+aiosqlite:///./myauth.db
ENCRYPTION_KEY=your-encryption-key
CORS_ORIGINS=http://localhost:3000
```

## Project Structure

```
backend/src/agent_builder/
├── api/routes/         # API endpoints (datasets, documents, skills, permissions)
├── core/               # Config, database, security
├── db/                 # SQLAlchemy models
├── schemas/            # Pydantic models
├── services/market/    # Market services (data, documents, skills)
└── main.py             # FastAPI application entry
```

## Important Notes

1. **Windows Environment**: Use quoted paths like `cd "path/to/dir"`, avoid `&&` syntax
2. **Encoding**: Python files must include `# -*- coding: utf-8 -*-`
3. **myauth Integration**: Auth integrated from `C:\Users\17625\Documents\GitHub\my-auth`
4. **Logging**: Use `loguru` for logging, not the standard `logging` module

## API Endpoints

### Datasets
- `POST /api/market/datasets` - Create dataset
- `POST /api/market/datasets/upload` - Upload dataset file
- `GET /api/market/datasets` - List datasets
- `GET /api/market/datasets/{id}` - Get dataset
- `PATCH /api/market/datasets/{id}/visibility` - Update visibility
- `DELETE /api/market/datasets/{id}` - Delete dataset
- `GET /api/market/datasets/{id}/analyze` - Analyze dataset
- `GET /api/market/datasets/{id}/quality` - Get quality score
- `GET /api/market/datasets/{id}/schema` - Get schema
- `GET /api/market/datasets/{id}/insights` - Get insights

### Skills
- `POST /api/market/skills` - Create skill
- `POST /api/market/skills/upload` - Upload skill
- `GET /api/market/skills` - List skills
- `GET /api/market/skills/filesystem` - List filesystem skills
- `PATCH /api/market/skills/{id}/visibility` - Update visibility
- `DELETE /api/market/skills/{id}` - Delete skill

### Documents
- `POST /api/market/documents` - Create document
- `POST /api/market/documents/upload` - Upload document
- `GET /api/market/documents` - List documents
- `GET /api/market/documents/search` - Search documents
- `DELETE /api/market/documents/{id}` - Delete document

### Permissions
- `POST /api/market/{resource_type}s/{resource_id}/permissions` - Grant permission
- `GET /api/market/{resource_type}s/{resource_id}/check-permission` - Check permission
