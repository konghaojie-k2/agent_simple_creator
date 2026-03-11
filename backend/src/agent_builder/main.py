# -*- coding: utf-8 -*-
"""FastAPI application entry point - Market Service."""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from myauth import AuthFramework
from loguru import logger

from agent_builder.core.config import settings
from agent_builder.core.database import init_db
from agent_builder.myauth_integration.auth import get_current_user

# 配置 loguru
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
)

# Import routes after app is created to avoid circular imports
from agent_builder.api.routes.documents import router as documents_router
from agent_builder.api.routes.datasets import router as datasets_router
from agent_builder.api.routes.skills import router as skills_router
from agent_builder.api.routes.market_permissions import router as market_permissions_router


# Global auth framework instance
auth: AuthFramework = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    global auth

    # Initialize database
    await init_db()

    # Initialize myauth
    config_path = Path(__file__).parent.parent.parent / "config.toml"
    if config_path.exists():
        auth = AuthFramework(
            db_url=settings.MYAUTH_DB_URL,
            secret=settings.JWT_SECRET,
            use_sqlite=True,
            admin_email="admin@example.com",
            admin_password="admin123",
        )
        
        # Register auth framework with app for CurrentUser dependency
        app.state.auth_framework = auth
        
        # Initialize auth (creates tables, admin user, etc.)
        await auth.init(app)
        
        # Include myauth router
        from myauth.router import create_auth_router
        auth_router = create_auth_router(auth)
        app.include_router(auth_router)

    yield

    # Shutdown
    if auth:
        await auth.close()


# Create FastAPI app
app = FastAPI(
    title="Market Service API",
    description="Data/Document/Skill Market Service",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (Market Service only)
app.include_router(documents_router)  # Doc Market 路由
app.include_router(datasets_router)  # Data Market 路由
app.include_router(skills_router)  # Skill Market 路由
app.include_router(market_permissions_router)  # Market 权限/共享/版本等路由


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Market Service API", "version": "0.1.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/debug/auth")
async def debug_auth(
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """Debug endpoint to check authentication."""
    return {"user_id": user_id, "status": "authenticated"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
