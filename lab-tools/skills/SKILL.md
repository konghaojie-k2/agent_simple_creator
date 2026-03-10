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

- `market_list_datasets` - List available datasets
- `market_get_dataset` - Get dataset details
- `market_search_datasets` - Search datasets by keyword

### Document Tools

- `market_list_documents` - List available documents
- `market_get_document` - Get document details
- `market_search_documents` - Search documents by keyword

### Skill Tools

- `market_list_skills` - List available skills
- `market_get_skill` - Get skill details
- `market_search_skills` - Search skills by keyword
