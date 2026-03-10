---
name: lab-tools
description: Lab Tools plugin for Market Service integration. Provides tools for data, documents, and skills management.
---

# Lab Tools

This plugin provides agent tools to interact with the Market Service.

## Configuration

```json
{
  "plugins": {
    "entries": {
      "lab-tools": {
        "enabled": true
      }
    }
  }
}
```

## Tools

### Data Tools

| Tool | Description |
|------|-------------|
| `market_list_datasets` | List available datasets |
| `market_get_dataset` | Get dataset details by ID |
| `market_search_datasets` | Search datasets by keyword |
| `market_create_dataset` | Create a new dataset |
| `market_delete_dataset` | Delete a dataset |

### Document Tools

| Tool | Description |
|------|-------------|
| `market_list_documents` | List available documents |
| `market_get_document` | Get document details by ID |
| `market_search_documents` | Search documents by keyword |

### Skill Tools

| Tool | Description |
|------|-------------|
| `market_list_skills` | List available skills |
| `market_get_skill` | Get skill details by ID |
| `market_search_skills` | Search skills by keyword |

### Utility Tools

| Tool | Description |
|------|-------------|
| `market_health_check` | Check if Market Service is healthy |
| `market_get_stats` | Get market statistics |

## Usage Example

```
Agent: "List all available datasets"
Tool: market_list_datasets
Result: [...]

Agent: "Search for sales data"
Tool: market_search_datasets q="sales"
Result: [...]
```
