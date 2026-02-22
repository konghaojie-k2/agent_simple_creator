# -*- coding: utf-8 -*-
"""Core configuration module."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings:
    """Application settings."""

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "default-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./agent_builder.db")
    MYAUTH_DB_URL: str = os.getenv("MYAUTH_DB_URL", "sqlite+aiosqlite:///./myauth.db")

    # Encryption
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")

    # CORS
    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

    # App
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Workspaces
    WORKSPACES_DIR: str = os.getenv("WORKSPACES_DIR", "./workspaces")

    # Mini-Agent config
    SYSTEM_PROMPT_PATH: str = os.getenv("SYSTEM_PROMPT_PATH", "mini_agent/config/system_prompt.md")
    MAX_STEPS: int = int(os.getenv("MAX_STEPS", "50"))
    TOKEN_LIMIT: int = int(os.getenv("TOKEN_LIMIT", "80000"))

    @property
    def encryption_key_bytes(self) -> bytes:
        """Get encryption key as bytes."""
        if not self.ENCRYPTION_KEY:
            raise ValueError("ENCRYPTION_KEY is not set in .env")
        return self.ENCRYPTION_KEY.encode() if len(self.ENCRYPTION_KEY) == 32 else self.ENCRYPTION_KEY.encode()[:32].ljust(32, b'0')


settings = Settings()
