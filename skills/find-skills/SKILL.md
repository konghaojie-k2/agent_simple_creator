---
name: find-skills
description: Discover and install skills from various sources. This skill should be used when users need to find skills, add external tools, or extend Agent capabilities.
---

# Find Skills

This skill helps discover and install skills from multiple sources.

## Skill Sources

### 1. Local Skills (Agent Directory)

Location: `workspaces/{user_id}/{agent_id}/skills/`

These are skills specific to this Agent.

### 2. Shared Skills (Global)

Location: `skills/` (project root)

These are shared skills available to all Agents.

### 3. Experiences (Agent History)

Location: `workspaces/{user_id}/{agent_id}/experiences/`

These are skills learned from past experiments.

### 4. MCP Servers (External APIs)

External tools via Model Context Protocol.

## How to Find Skills

### Method 1: List Available Skills

Use the `get_skill` tool to see what skills are available:

```python
# This will return metadata about all available skills
# from shared, agent-specific, and experience sources
```

### Method 2: Search by Capability

If you need a specific capability:

1. Check local skills first
2. Check shared skills
3. Search MCP servers (if configured)

## How to Add External Tools

### Option 1: Create a Skill (Recommended)

Create a new skill directory with SKILL.md:

```
workspaces/{user_id}/{agent_id}/skills/my-tool/
├── SKILL.md
└── scripts/
    └── tool.py
```

Example SKILL.md:
```yaml
---
name: my-external-tool
description: Interface with external API X. Use when you need to fetch data from service X.
---

# My External Tool

## Setup

1. Configure API key in environment
2. Test connectivity

## Usage

Use `scripts/api_client.py` to make requests:

```python
python scripts/api_client.py --endpoint /data --param value
```
```

### Option 2: Add to Tool Registry (Advanced)

For reusable tools across all Agents, add to `tool_registry.py`:

```python
# In _register_default_tools()
self.tools["my_tool"] = self._my_tool

async def _my_tool(self, param: str) -> Dict[str, Any]:
    """Tool description"""
    result = await call_external_api(param)
    return {"success": True, "result": result}
```

### Option 3: MCP Server (For External APIs)

Configure an MCP server in the database:

```json
{
  "name": "weather-api",
  "transport": "stdio",
  "command": "python",
  "args": ["-m", "weather_mcp_server"],
  "env": {"API_KEY": "your_key"}
}
```

Then use `discover_skills` to find available tools.

### Option 4: Install from Git/URL

Clone skill repository:

```bash
cd workspaces/{user_id}/{agent_id}/skills
git clone https://github.com/example/skill-name.git
```

Then reload skills with `get_skill` tool.

## Workflow: Adding a New Tool

1. **Identify need**: What capability is missing?
2. **Check existing**: Use `get_skill` to see if similar skill exists
3. **Choose method**:
   - Simple wrapper → Create Skill
   - Reusable across Agents → Add to Tool Registry
   - External API → Configure MCP Server
4. **Implement**: Create SKILL.md and supporting files
5. **Test**: Use in an experiment
6. **Share**: If useful, move to shared skills

## Example: Adding a Translation Tool

### Step 1: Create Skill Directory

```bash
mkdir -p workspaces/user1/agent1/skills/translator/scripts
```

### Step 2: Create SKILL.md

```yaml
---
name: translator
description: Translate text between languages. Use when users need content translated.
---

# Translator

## Supported Languages

- English, Chinese, Japanese, French, German

## Usage

```python
python scripts/translate.py --text "Hello" --to zh
```
```

### Step 3: Create Script

```python
# scripts/translate.py
import argparse
import requests

def translate(text: str, target: str) -> str:
    # Call translation API
    response = requests.post(
        "https://api.translator.com/translate",
        json={"text": text, "target": target}
    )
    return response.json()["translation"]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--to", required=True)
    args = parser.parse_args()
    print(translate(args.text, args.to))
```

### Step 4: Test

```python
# In experiment, use:
get_skill(skill_name="translator")
# Then follow the instructions
```

## Tips

- **Start simple**: Create basic SKILL.md first, add resources later
- **Document clearly**: Explain when and how to use the skill
- **Test thoroughly**: Verify in experiments before sharing
- **Version control**: Track changes to skills over time
