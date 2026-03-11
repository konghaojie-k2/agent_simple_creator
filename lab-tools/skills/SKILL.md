---
name: lab-tools
description: Lab Tools plugin for Market Service integration. Provides tools for data, documents, and skills management with AI-Native analysis.
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
| `market_upload_dataset` | Upload a dataset file |
| `market_delete_dataset` | Delete a dataset |
| `market_download_dataset` | Get dataset download URL |

### Analysis Tools (AI-Native)

| Tool | Description |
|------|-------------|
| `market_analyze_dataset` | Comprehensive dataset analysis |
| `market_dataset_quality` | Data quality report |
| `market_dataset_schema` | Schema with semantic types |
| `market_dataset_insights` | AI-generated insights |

### Document Tools

| Tool | Description |
|------|-------------|
| `market_list_documents` | List available documents |
| `market_get_document` | Get document details |
| `market_search_documents` | Search documents |
| `market_upload_document` | Upload a document |
| `market_delete_document` | Delete a document |
| `market_download_document` | Get document download URL |

### Skill Tools

| Tool | Description |
|------|-------------|
| `market_list_skills` | List available skills |
| `market_get_skill` | Get skill details |
| `market_search_skills` | Search skills |
| `market_install_skill` | Download and install skill locally |
| `market_list_installed_skills` | List locally installed skills |
| `market_uninstall_skill` | Remove skill from local |

### Utility Tools

| Tool | Description |
|------|-------------|
| `market_health_check` | Check service health |
| `market_get_stats` | Market statistics |

## Usage Example

```
Agent: "List all available datasets"
Tool: market_list_datasets

Agent: "Analyze the sales data"
Tool: market_analyze_dataset dataset_id="xxx"

Agent: "Install the skill for data analysis"
Tool: market_install_skill skill_id="xxx"

Agent: "Download this dataset to use"
Tool: market_download_dataset dataset_id="xxx"
```
