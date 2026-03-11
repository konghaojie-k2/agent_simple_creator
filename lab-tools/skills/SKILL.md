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

### Analysis Tools (AI-Native)

| Tool | Description |
|------|-------------|
| `market_analyze_dataset` | Comprehensive dataset analysis with semantic types, quality scores, and insights |
| `market_dataset_quality` | Get data quality report (completeness, uniqueness, consistency) |
| `market_dataset_schema` | Get schema with column types and semantic information |
| `market_dataset_insights` | Get AI-generated insights and recommendations |

### Document Tools

| Tool | Description |
|------|-------------|
| `market_list_documents` | List available documents |
| `market_get_document` | Get document details by ID |
| `market_search_documents` | Search documents by keyword |
| `market_upload_document` | Upload a document |
| `market_delete_document` | Delete a document |

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

Agent: "Analyze the sales data dataset"
Tool: market_analyze_dataset dataset_id="xxx"
Result: { semantic_types: {...}, quality_score: 85, insights: [...] }

Agent: "What's the quality of dataset xyz?"
Tool: market_dataset_quality dataset_id="xyz"
Result: { completeness: 95%, uniqueness: 98%, consistency: 90% }
```
