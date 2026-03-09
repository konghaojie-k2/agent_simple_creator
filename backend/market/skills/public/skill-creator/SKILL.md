---
name: skill-creator
description: Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Agent's capabilities with specialized knowledge, workflows, or tool integrations.
---

# Skill Creator

This skill provides guidance for creating effective skills.

## About Skills

Skills are modular, self-contained packages that extend Agent's capabilities by providing specialized knowledge, workflows, and tools.

### Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   └── description: (required)
│   └── Markdown instructions (required)
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash/etc.)
    ├── references/       - Documentation loaded into context as needed
    └── assets/           - Files used in output
```

## Skill Creation Process

### Step 1: Initialize Skill

Create the skill directory structure:

```bash
mkdir -p my-skill/{scripts,references,assets}
```

### Step 2: Create SKILL.md

Template:

```yaml
---
name: my-skill
description: Describe what this skill does and when to use it
---

# My Skill

## Purpose

Brief description of the skill's purpose.

## When to Use

Describe the scenarios where this skill should be triggered.

## Workflow

1. Step one
2. Step two
3. Step three

## Available Resources

- `scripts/tool.py` - Description of what this script does
- `references/guide.md` - Reference documentation
```

### Step 3: Add Resources (Optional)

Add scripts, references, or assets as needed.

### Step 4: Test Skill

Use the skill in an experiment to verify it works as expected.

### Step 5: Package

The skill is ready to use when:
- SKILL.md has proper YAML frontmatter
- Description clearly explains when to use the skill
- All referenced resources exist

## Example: Creating a Weather Skill

```yaml
---
name: weather-checker
description: Check weather information for any location. Use this skill when users ask about weather, forecasts, or climate data.
---

# Weather Checker

## Purpose

This skill helps check weather information for any location.

## When to Use

Use this skill when:
- User asks about current weather
- User needs weather forecast
- User asks about climate conditions

## Workflow

1. Parse location from user query
2. Use `scripts/fetch_weather.py` to get data
3. Format and present results

## Available Resources

- `scripts/fetch_weather.py` - Fetches weather data from API
```
