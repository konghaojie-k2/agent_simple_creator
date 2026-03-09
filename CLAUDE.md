# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agent Builder is an AI agent creation platform with multi-LLM provider support (DeepSeek, Qwen, OpenAI). The project consists of:

- **Backend**: FastAPI + SQLAlchemy (async) + SQLite
- **Frontend**: Next.js 14 + React + Tailwind CSS v3
- **Auth**: my-auth framework (integrated from local path)

## Common Commands

### Backend (cd backend)

```bash
# Install dependencies
uv sync

# Install myauth (editable mode) - required for auth
uv pip install -e "C:\Users\17625\Documents\GitHub\my-auth"

# Run development server
uv run uvicorn src.agent_builder.main:app --reload --port 8000

# Run tests
uv run pytest

# Run a single test
uv run pytest tests/test_file.py::test_function_name -v
```

### Frontend (cd frontend)

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

### Access

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Architecture

### Backend Structure
```
backend/src/agent_builder/
├── api/routes/         # API endpoints (agents, chat, providers)
├── core/               # Config, database, security
├── db/                 # SQLAlchemy models
├── schemas/            # Pydantic models
├── services/           # Business logic (agent_service, llm_service)
├── myauth_integration/ # Auth integration
└── main.py             # FastAPI application entry
```

### Frontend Structure
```
frontend/src/
├── app/(auth)/         # Login, register pages
├── app/(dashboard)/    # Agents, chat, providers pages
├── components/         # React components
├── contexts/           # AuthContext
├── hooks/              # Custom hooks (useChat)
├── lib/                # API client
└── types/              # TypeScript types
```

## Environment Variables

### Backend (.env)
```
JWT_SECRET=your-32-character-secret-key
DATABASE_URL=sqlite+aiosqlite:///./agent_builder.db
MYAUTH_DB_URL=sqlite+aiosqlite:///./myauth.db
ENCRYPTION_KEY=your-encryption-key
CORS_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Important Notes

1. **Windows Environment**: Use quoted paths like `cd "path/to/dir"`, avoid `&&` syntax
2. **Encoding**:
   - **Python files**: Must include `# -*- coding: utf-8 -*-`
   - **Frontend (TypeScript/JS)**: Do NOT add Python encoding declarations
3. **myauth Integration**: Auth integrated from `C:\Users\17625\Documents\GitHub\my-auth`
4. **API Keys**: Stored encrypted using Fernet in the database
5. **Async**: Use `async/await` for all database and HTTP operations
6. **Logging**: Use `loguru` for logging, not the standard `logging` module

## 日志规范 (Logging)

项目使用 `loguru` 库进行日志记录：

```python
from loguru import logger

# 基本使用
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")

# 配置 (在 main.py 中)
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="DEBUG",
)
```

**注意**: 不要使用标准库的 `logging` 模块，统一使用 `loguru`。

## Additional Guidelines

For detailed coding standards, import conventions, and API patterns, see [AGENTS.md](./AGENTS.md).
