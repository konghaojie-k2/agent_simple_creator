# AGENTS.md - Agent Builder Project Guidelines

## Project Overview

Agent Builder is a simple AI agent creation platform supporting multiple LLM providers (DeepSeek, Qwen, OpenAI). The project consists of:

- **Backend**: FastAPI + SQLAlchemy (async) + SQLite
- **Frontend**: Next.js 14 + React + Tailwind CSS v3
- **Auth**: my-auth framework (integrated from local path)

---

## Build Commands

### Backend

```bash
# Navigate to backend directory
cd backend

# Install dependencies
uv sync

# Install myauth (editable mode)
uv pip install -e "C:\Users\17625\Documents\GitHub\my-auth"

# Run development server
uv run uvicorn src.agent_builder.main:app --reload --port 8000

# Run with Python directly
uv run python -m src.agent_builder.main

# Run tests
uv run pytest

# Run a single test
uv run pytest tests/test_file.py::test_function_name -v
```

### Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run linting
npm run lint
```

---

## Code Style Guidelines

### Python (Backend)

#### Encoding
- All Python files must include encoding declaration:
```python
# -*- coding: utf-8 -*-
```

#### Imports (Sorted by: stdlib → third-party → local)
```python
# Standard library
import os
import json
from typing import Optional
from pathlib import Path

# Third-party
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# Local application
from app.core.config import settings
from app.core.database import get_db
from app.schemas.pydantic import AgentCreate
from app.services.agent_service import AgentService
```

#### Naming Conventions
- **Files**: snake_case (e.g., `agent_service.py`, `llm_service.py`)
- **Classes**: PascalCase (e.g., `AgentService`, `LLMProvider`)
- **Functions/Variables**: snake_case (e.g., `get_current_user`, `api_key`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_STEPS`, `DEFAULT_TIMEOUT`)
- **Async functions**: Prefix with `async_` or use `await` pattern

#### Function/Class Structure
```python
# -*- coding: utf-8 -*-
"""Module docstring."""

from typing import Optional


class ExampleClass:
    """Class docstring."""

    def __init__(self, param: str):
        """Initialize example class."""
        self.param = param

    async def async_method(self, value: int) -> str:
        """Async method docstring.
        
        Args:
            value: Description of value
            
        Returns:
            Description of return value
        """
        result = await self._process(value)
        return result

    def _private_method(self) -> None:
        """Private method (prefixed with underscore)."""
        pass
```

#### Error Handling
- Use custom exceptions for domain-specific errors
- Return appropriate HTTP status codes
- Include error details in responses:
```python
from fastapi import HTTPException, status

async def get_item(item_id: str):
    item = await db.get(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found"
        )
    return item
```

#### Type Hints
- Use type hints for all function parameters and return values
- Use Optional for nullable types:
```python
def func(name: Optional[str] = None) -> Optional[str]:
    ...
```

#### Database Models (SQLAlchemy)
```python
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

class Agent(Base):
    """Agent model."""
    
    __tablename__ = "agents"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

---

### TypeScript/JavaScript (Frontend)

#### File Structure
- Use kebab-case for component files: `agent-list.tsx`
- Use PascalCase for React components: `AgentList.tsx`

#### Imports (Sorted alphabetically within groups)
```typescript
// React/Next.js
import { useEffect, useState } from 'react'
import Link from 'next/link'

// Third-party
import { agentsApi, providersApi } from '@/lib/api'

// Types
import { Agent, LLMProvider } from '@/types'
```

#### Naming Conventions
- **Components**: PascalCase (e.g., `AgentCard`, `ChatWindow`)
- **Functions/Hooks**: camelCase (e.g., `useAuth`, `handleSubmit`)
- **Constants**: UPPER_SNAKE_CASE
- **Interfaces/Types**: PascalCase (e.g., `AgentResponse`)

#### React Components
```typescript
'use client';

import { useEffect, useState } from 'react';
import { agentsApi } from '@/lib/api';
import { Agent } from '@/types';

interface AgentListProps {
  userId: string;
}

export default function AgentList({ userId }: AgentListProps) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAgents();
  }, [userId]);

  const loadAgents = async () => {
    try {
      const data = await agentsApi.list();
      setAgents(data);
    } catch (error) {
      console.error('Failed to load agents:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      {agents.map((agent) => (
        <div key={agent.id}>{agent.name}</div>
      ))}
    </div>
  );
}
```

#### Type Definitions
```typescript
export interface Agent {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  system_prompt?: string;
  provider_id?: string;
  model: string;
  max_steps: number;
}

export interface CreateAgentRequest {
  name: string;
  description?: string;
  system_prompt?: string;
  provider_id?: string;
  model: string;
  max_steps?: number;
}
```

---

## API Design Patterns

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/agents | List all agents |
| POST | /api/agents | Create new agent |
| GET | /api/agents/{id} | Get specific agent |
| PUT | /api/agents/{id} | Update agent |
| DELETE | /api/agents/{id} | Delete agent |
| POST | /api/chat/{agent_id} | Stream chat response |

### Request/Response Patterns

- Use Pydantic models for request/response validation
- Include appropriate HTTP status codes
- Use streaming for chat responses (SSE)

---

## Database

- **Backend**: SQLite with SQLAlchemy async (aiosqlite)
- **Auth DB**: Separate SQLite database for my-auth
- **Location**: Project root (`.db` files)

---

## Environment Variables

### Backend (.env)
```bash
JWT_SECRET=your-32-character-secret-key
DATABASE_URL=sqlite+aiosqlite:///./agent_builder.db
MYAUTH_DB_URL=sqlite+aiosqlite:///./myauth.db
ENCRYPTION_KEY=your-encryption-key
CORS_ORIGINS=http://localhost:3000
DEBUG=true
WORKSPACES_DIR=./workspaces
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Testing

### Backend Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/test_agent.py

# Run specific test
uv run pytest tests/test_agent.py::test_create_agent -v
```

### Frontend Tests
```bash
# Run lint
npm run lint

# Build check
npm run build
```

---

## Important Notes

1. **Windows Environment**: Use `cd "path/to/dir"` with quotes, avoid `&&` syntax
2. **Encoding**: Always use UTF-8 encoding for all files
3. **myauth Integration**: Currently integrated from local path `C:\Users\17625\Documents\GitHub\my-auth`
4. **API Keys**: Stored encrypted using Fernet in the database
5. **Async**: Use `async/await` for all database and HTTP operations

---

## Project Structure

```
agent_simple_creator/
├── backend/
│   ├── src/
│   │   └── agent_builder/
│   │       ├── api/routes/     # API endpoints
│   │       ├── core/           # Config, DB, Security
│   │       ├── db/             # SQLAlchemy models
│   │       ├── schemas/        # Pydantic models
│   │       ├── services/       # Business logic
│   │       ├── myauth_integration/  # Auth integration
│   │       └── main.py         # FastAPI app
│   ├── tests/                  # Unit/Integration tests
│   ├── scripts/                # Init scripts
│   ├── pyproject.toml          # uv project config
│   └── .env                   # Environment variables
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js pages
│   │   ├── components/        # React components
│   │   ├── lib/              # Utilities
│   │   ├── contexts/          # Auth contexts
│   │   ├── hooks/            # Custom hooks
│   │   └── types/            # TypeScript types
│   └── package.json
└── AGENTS.md                 # Project guidelines
```
