# -*- coding: utf-8 -*-
"""Seed default experiment templates."""

import asyncio
import uuid
from sqlalchemy import select

from agent_builder.core.database import async_session_factory, init_db
from agent_builder.db.models import ExperimentTemplate


# Default document templates
DOCUMENT_TEMPLATES = [
    {
        "name": "README Generator",
        "description": "Generate a README.md file from project description",
        "experiment_type": "document",
        "template_config": {
            "prompt_template": "Generate a comprehensive README.md for a project with the following description:\n\n{{description}}",
            "output_file": "README.md",
            "output_format": "markdown",
        },
        "is_public": True,
    },
    {
        "name": "API Documentation Generator",
        "description": "Generate API documentation from OpenAPI spec",
        "experiment_type": "document",
        "template_config": {
            "prompt_template": "Generate detailed API documentation from this OpenAPI specification:\n\n{{openapi_spec}}",
            "output_file": "API_DOCS.md",
            "output_format": "markdown",
        },
        "is_public": True,
    },
    {
        "name": "Code Comments Generator",
        "description": "Generate documentation comments for code files",
        "experiment_type": "document",
        "template_config": {
            "prompt_template": "Add comprehensive documentation comments to this code:\n\n```\n{{code}}\n```",
            "output_file": "documented_code.txt",
            "output_format": "code",
        },
        "is_public": True,
    },
    {
        "name": "Technical Documentation Writer",
        "description": "Write technical documentation on a given topic",
        "experiment_type": "document",
        "template_config": {
            "prompt_template": "Write comprehensive technical documentation about: {{topic}}",
            "output_file": "TECHNICAL_DOC.md",
            "output_format": "markdown",
        },
        "is_public": True,
    },
]

# Default skill creation templates
SKILL_TEMPLATES = [
    {
        "name": "CLI Tool Creator",
        "description": "Create a command-line tool with specified functionality",
        "experiment_type": "skill_creation",
        "template_config": {
            "prompt_template": "Create a CLI tool with the following requirements:\n{{requirements}}\n\nWrite the complete Python code that implements this tool.",
            "output_file": "cli_tool.py",
            "output_format": "code",
        },
        "is_public": True,
    },
    {
        "name": "API Wrapper Creator",
        "description": "Create a Python wrapper for an API",
        "experiment_type": "skill_creation",
        "template_config": {
            "prompt_template": "Create a Python API wrapper for: {{api_description}}\n\nInclude proper error handling, rate limiting, and documentation.",
            "output_file": "api_wrapper.py",
            "output_format": "code",
        },
        "is_public": True,
    },
]

# Default data analysis templates
DATA_TEMPLATES = [
    {
        "name": "Data Cleaning Pipeline",
        "description": "Create a data cleaning pipeline",
        "experiment_type": "data_analysis",
        "template_config": {
            "prompt_template": "Create a data cleaning pipeline for the following dataset:\n{{data_description}}\n\nWrite Python code using pandas to clean and preprocess the data.",
            "output_file": "data_cleaning.py",
            "output_format": "code",
        },
        "is_public": True,
    },
    {
        "name": "Data Visualization Generator",
        "description": "Generate visualizations for data",
        "experiment_type": "data_analysis",
        "template_config": {
            "prompt_template": "Create data visualizations for:\n{{data_description}}\n\nGenerate Python code using matplotlib/seaborn to create meaningful charts.",
            "output_file": "visualizations.py",
            "output_format": "code",
        },
        "is_public": True,
    },
]


async def seed_templates():
    """Seed the database with default templates."""
    await init_db()

    async with async_session_factory() as db:
        # Check if templates already exist
        result = await db.execute(select(ExperimentTemplate).limit(1))
        existing = result.scalars().first()

        if existing:
            print("Templates already exist, skipping seed.")
            return

        # Add all templates
        all_templates = DOCUMENT_TEMPLATES + SKILL_TEMPLATES + DATA_TEMPLATES

        for template_data in all_templates:
            template = ExperimentTemplate(
                id=str(uuid.uuid4()),
                user_id=None,  # Public templates have no owner
                **template_data,
            )
            db.add(template)

        await db.commit()
        print(f"Seeded {len(all_templates)} default templates.")


if __name__ == "__main__":
    asyncio.run(seed_templates())
