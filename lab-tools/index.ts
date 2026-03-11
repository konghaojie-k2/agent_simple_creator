// Lab Tools Plugin - Market Service integration
// This plugin provides agent tools to interact with Market Service
//
// Configuration:
// - Set MARKET_SERVICE_URL environment variable to override the default
// - Default: http://localhost:8000 (development)

export default function (api) {
  // Support environment variable configuration, fallback to localhost for development
  const MARKET_SERVICE_URL = typeof process !== 'undefined' && process.env?.MARKET_SERVICE_URL
    ? process.env.MARKET_SERVICE_URL
    : "http://localhost:8000";

  // ========== Helper Functions ==========
  
  async function makeRequest(endpoint, method = "GET", body = null) {
    const options = {
      method,
      headers: { "Content-Type": "application/json" },
    };
    if (body) options.body = JSON.stringify(body);
    
    const response = await fetch(`${MARKET_SERVICE_URL}${endpoint}`, options);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  }

  // ========== Data Tools ==========

  api.registerTool({
    name: "market_list_datasets",
    description: "List available datasets in the market. Returns a list of datasets with their metadata.",
    parameters: {
      type: "object",
      properties: {
        limit: { type: "number", default: 10, description: "Number of datasets to return" },
        offset: { type: "number", default: 0, description: "Offset for pagination" },
        dataset_type: { type: "string", description: "Filter by dataset type (e.g., json, csv)" },
        category: { type: "string", description: "Filter by category" },
      },
    },
    async execute(_id, params) {
      try {
        const queryParams = new URLSearchParams();
        if (params.limit) queryParams.append("limit", params.limit.toString());
        if (params.offset) queryParams.append("offset", params.offset.toString());
        if (params.dataset_type) queryParams.append("dataset_type", params.dataset_type);
        if (params.category) queryParams.append("category", params.category);

        const data = await makeRequest(`/api/market/datasets?${queryParams.toString()}`);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_get_dataset",
    description: "Get detailed information about a specific dataset",
    parameters: {
      type: "object",
      properties: {
        dataset_id: { type: "string", description: "The dataset ID" },
      },
      required: ["dataset_id"],
    },
    async execute(_id, params) {
      try {
        const data = await makeRequest(`/api/market/datasets/${params.dataset_id}`);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_search_datasets",
    description: "Search datasets by keyword in name or description",
    parameters: {
      type: "object",
      properties: {
        q: { type: "string", description: "Search keyword" },
        limit: { type: "number", default: 10 },
      },
      required: ["q"],
    },
    async execute(_id, params) {
      try {
        const queryParams = new URLSearchParams({ q: params.q, limit: (params.limit || 10).toString() });
        const data = await makeRequest(`/api/market/datasets/search?${queryParams.toString()}`);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_create_dataset",
    description: "Create a new dataset in the market",
    parameters: {
      type: "object",
      properties: {
        name: { type: "string", description: "Dataset name" },
        dataset_type: { type: "string", default: "json", description: "Dataset type (json, csv, etc.)" },
        description: { type: "string", description: "Dataset description" },
        category: { type: "string", description: "Dataset category" },
        tags: { type: "array", items: { type: "string" }, description: "Dataset tags" },
        is_public: { type: "boolean", default: false, description: "Make dataset publicly accessible" },
      },
      required: ["name"],
    },
    async execute(_id, params) {
      try {
        const data = await makeRequest("/api/market/datasets", "POST", params);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_upload_dataset",
    description: "Upload a dataset file to the market. Returns the created dataset with file info.",
    parameters: {
      type: "object",
      properties: {
        name: { type: "string", description: "Dataset name" },
        description: { type: "string", description: "Dataset description" },
        category: { type: "string", description: "Dataset category" },
        tags: { type: "string", description: "Comma-separated tags" },
        is_public: { type: "boolean", default: false, description: "Make dataset public" },
        file_url: { type: "string", description: "URL to download the file from" },
      },
      required: ["name", "file_url"],
    },
    async execute(_id, params) {
      try {
        // Download file from URL and upload
        const data = await makeRequest("/api/market/datasets/upload", "POST", params);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_delete_dataset",
    description: "Delete a dataset from the market",
    parameters: {
      type: "object",
      properties: {
        dataset_id: { type: "string", description: "The dataset ID to delete" },
      },
      required: ["dataset_id"],
    },
    async execute(_id, params) {
      try {
        await makeRequest(`/api/market/datasets/${params.dataset_id}`, "DELETE");
        return { content: [{ type: "text", text: "Dataset deleted successfully" }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  // ========== Analysis Tools ==========

  api.registerTool({
    name: "market_analyze_dataset",
    description: "Analyze a dataset and generate comprehensive metadata including semantic types, quality scores, and insights",
    parameters: {
      type: "object",
      properties: {
        dataset_id: { type: "string", description: "The dataset ID to analyze" },
        sample_size: { type: "number", default: 1000, description: "Number of rows to sample for analysis" },
      },
      required: ["dataset_id"],
    },
    async execute(_id, params) {
      try {
        const queryParams = new URLSearchParams();
        queryParams.append("dataset_id", params.dataset_id);
        if (params.sample_size) queryParams.append("sample_size", params.sample_size.toString());
        
        const data = await makeRequest(`/api/market/datasets/analyze?${queryParams.toString()}`);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_dataset_quality",
    description: "Get data quality report for a dataset including completeness, uniqueness, and consistency scores",
    parameters: {
      type: "object",
      properties: {
        dataset_id: { type: "string", description: "The dataset ID" },
      },
      required: ["dataset_id"],
    },
    async execute(_id, params) {
      try {
        const data = await makeRequest(`/api/market/datasets/${params.dataset_id}/quality`);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_dataset_schema",
    description: "Get dataset schema with column types and semantic information",
    parameters: {
      type: "object",
      properties: {
        dataset_id: { type: "string", description: "The dataset ID" },
        include_semantics: { type: "boolean", default: true, description: "Include semantic type information" },
      },
      required: ["dataset_id"],
    },
    async execute(_id, params) {
      try {
        const queryParams = new URLSearchParams();
        queryParams.append("include_semantics", params.include_semantics?.toString() || "true");
        const data = await makeRequest(`/api/market/datasets/${params.dataset_id}/schema?${queryParams.toString()}`);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_dataset_insights",
    description: "Get AI-generated insights and recommendations for a dataset",
    parameters: {
      type: "object",
      properties: {
        dataset_id: { type: "string", description: "The dataset ID" },
        sample_size: { type: "number", default: 1000 },
      },
      required: ["dataset_id"],
    },
    async execute(_id, params) {
      try {
        const queryParams = new URLSearchParams();
        queryParams.append("dataset_id", params.dataset_id);
        if (params.sample_size) queryParams.append("sample_size", params.sample_size.toString());
        const data = await makeRequest(`/api/market/datasets/${params.dataset_id}/insights?${queryParams.toString()}`);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  // ========== Document Tools ==========

  api.registerTool({
    name: "market_list_documents",
    description: "List available documents in the market",
    parameters: {
      type: "object",
      properties: {
        limit: { type: "number", default: 10 },
        offset: { type: "number", default: 0 },
      },
    },
    async execute(_id, params) {
      try {
        const queryParams = new URLSearchParams();
        if (params.limit) queryParams.append("limit", params.limit.toString());
        if (params.offset) queryParams.append("offset", params.offset.toString());

        const data = await makeRequest(`/api/market/documents?${queryParams.toString()}`);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_get_document",
    description: "Get detailed information about a specific document",
    parameters: {
      type: "object",
      properties: {
        document_id: { type: "string", description: "The document ID" },
      },
      required: ["document_id"],
    },
    async execute(_id, params) {
      try {
        const data = await makeRequest(`/api/market/documents/${params.document_id}`);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_search_documents",
    description: "Search documents by keyword",
    parameters: {
      type: "object",
      properties: {
        q: { type: "string", description: "Search keyword" },
        limit: { type: "number", default: 10 },
      },
      required: ["q"],
    },
    async execute(_id, params) {
      try {
        const queryParams = new URLSearchParams({ q: params.q, limit: (params.limit || 10).toString() });
        const data = await makeRequest(`/api/market/documents/search?${queryParams.toString()}`);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_upload_document",
    description: "Upload a document to the market",
    parameters: {
      type: "object",
      properties: {
        name: { type: "string", description: "Document name" },
        description: { type: "string", description: "Document description" },
        category: { type: "string", description: "Document category" },
        file_url: { type: "string", description: "URL to download the file from" },
        is_public: { type: "boolean", default: false },
      },
      required: ["name", "file_url"],
    },
    async execute(_id, params) {
      try {
        const data = await makeRequest("/api/market/documents/upload", "POST", params);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_delete_document",
    description: "Delete a document from the market",
    parameters: {
      type: "object",
      properties: {
        document_id: { type: "string", description: "The document ID to delete" },
      },
      required: ["document_id"],
    },
    async execute(_id, params) {
      try {
        await makeRequest(`/api/market/documents/${params.document_id}`, "DELETE");
        return { content: [{ type: "text", text: "Document deleted successfully" }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  // ========== Skill Tools ==========

  api.registerTool({
    name: "market_list_skills",
    description: "List available skills in the market",
    parameters: {
      type: "object",
      properties: {
        limit: { type: "number", default: 10 },
        offset: { type: "number", default: 0 },
      },
    },
    async execute(_id, params) {
      try {
        const queryParams = new URLSearchParams();
        if (params.limit) queryParams.append("limit", params.limit.toString());
        if (params.offset) queryParams.append("offset", params.offset.toString());

        const data = await makeRequest(`/api/market/skills?${queryParams.toString()}`);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_get_skill",
    description: "Get detailed information about a specific skill",
    parameters: {
      type: "object",
      properties: {
        skill_id: { type: "string", description: "The skill ID" },
      },
      required: ["skill_id"],
    },
    async execute(_id, params) {
      try {
        const data = await makeRequest(`/api/market/skills/${params.skill_id}`);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_search_skills",
    description: "Search skills by keyword",
    parameters: {
      type: "object",
      properties: {
        q: { type: "string", description: "Search keyword" },
        limit: { type: "number", default: 10 },
      },
      required: ["q"],
    },
    async execute(_id, params) {
      try {
        const queryParams = new URLSearchParams({ q: params.q, limit: (params.limit || 10).toString() });
        const data = await makeRequest(`/api/market/skills/search?${queryParams.toString()}`);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  // ========== Utility Tools ==========

  api.registerTool({
    name: "market_health_check",
    description: "Check if the Market Service is running and healthy",
    parameters: {
      type: "object",
      properties: {},
    },
    async execute(_id, params) {
      try {
        const data = await makeRequest("/health");
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_get_stats",
    description: "Get market statistics (total datasets, documents, skills)",
    parameters: {
      type: "object",
      properties: {},
    },
    async execute(_id, params) {
      try {
        const [datasets, documents, skills] = await Promise.all([
          makeRequest("/api/market/datasets?limit=1"),
          makeRequest("/api/market/documents?limit=1"),
          makeRequest("/api/market/skills?limit=1"),
        ]);
        
        return { 
          content: [{ 
            type: "text", 
            text: JSON.stringify({
              datasets_count: datasets.length || 0,
              documents_count: documents.length || 0,
              skills_count: skills.length || 0,
            }, null, 2) 
          }] 
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });
}

  // ========== Skill Installation Tools ==========

  api.registerTool({
    name: "market_install_skill",
    description: "Download and install a skill to local OpenClaw skills directory",
    parameters: {
      type: "object",
      properties: {
        skill_id: { type: "string", description: "The skill ID to install" },
        target_dir: { type: "string", description: "Target directory for installation (default: ~/.openclaw/skills)" },
      },
      required: ["skill_id"],
    },
    async execute(_id, params) {
      try {
        // First get skill details to get download URL
        const skill = await makeRequest(`/api/market/skills/${params.skill_id}`);
        
        if (!skill.download_url && !skill.file_url) {
          return { content: [{ type: "text", text: "Skill has no download URL" }] };
        }
        
        // Download skill file
        const downloadUrl = skill.download_url || skill.file_url;
        
        return { 
          content: [{ 
            type: "text", 
            text: JSON.stringify({
              message: "Skill download initiated",
              skill_name: skill.name,
              download_url: downloadUrl,
              target_dir: params.target_dir || "~/.openclaw/skills",
              instructions: "Use exec tool to download and extract the skill"
            }, null, 2) 
          }] 
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_list_installed_skills",
    description: "List skills installed in local OpenClaw skills directory",
    parameters: {
      type: "object",
      properties: {
        skills_dir: { type: "string", description: "Skills directory path" },
      },
    },
    async execute(_id, params) {
      try {
        // This would need exec to actually list local files
        // For now return instructions
        return { 
          content: [{ 
            type: "text", 
            text: JSON.stringify({
              message: "Use exec tool to list skills directory",
              default_dir: "~/.openclaw/skills",
              suggested_command: "ls -la ~/.openclaw/skills/"
            }, null, 2) 
          }] 
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_uninstall_skill",
    description: "Remove a skill from local OpenClaw skills directory",
    parameters: {
      type: "object",
      properties: {
        skill_name: { type: "string", description: "The skill name to uninstall" },
      },
      required: ["skill_name"],
    },
    async execute(_id, params) {
      try {
        return { 
          content: [{ 
            type: "text", 
            text: JSON.stringify({
              message: "Skill uninstall",
              skill_name: params.skill_name,
              instructions: "Use exec tool to remove skill directory",
              suggested_command: `rm -rf ~/.openclaw/skills/${params.skill_name}`
            }, null, 2) 
          }] 
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  // ========== Skill Configuration ==========

  api.registerTool({
    name: "market_configure_skill",
    description: "Configure a skill with custom parameters",
    parameters: {
      type: "object",
      properties: {
        skill_id: { type: "string", description: "Skill ID to configure" },
        config: { type: "object", description: "Configuration parameters" },
      },
      required: ["skill_id", "config"],
    },
    async execute(_id, params) {
      try {
        const data = await makeRequest(`/api/market/skills/${params.skill_id}/config`, "POST", params.config);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_get_skill_config",
    description: "Get current configuration for a skill",
    parameters: {
      type: "object",
      properties: {
        skill_id: { type: "string", description: "Skill ID" },
      },
      required: ["skill_id"],
    },
    async execute(_id, params) {
      try {
        const data = await makeRequest(`/api/market/skills/${params.skill_id}/config`);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_enable_skill",
    description: "Enable an installed skill",
    parameters: {
      type: "object",
      properties: {
        skill_id: { type: "string", description: "Skill ID to enable" },
      },
      required: ["skill_id"],
    },
    async execute(_id, params) {
      try {
        const data = await makeRequest(`/api/market/skills/${params.skill_id}/enable`, "POST");
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_disable_skill",
    description: "Disable an installed skill",
    parameters: {
      type: "object",
      properties: {
        skill_id: { type: "string", description: "Skill ID to disable" },
      },
      required: ["skill_id"],
    },
    async execute(_id, params) {
      try {
        const data = await makeRequest(`/api/market/skills/${params.skill_id}/disable`, "POST");
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_list_skill_categories",
    description: "List all skill categories",
    parameters: {
      type: "object",
      properties: {},
    },
    async execute(_id, _params) {
      try {
        const data = await makeRequest("/api/market/skills/categories");
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  // ========== Data Download Tools ==========

  api.registerTool({
    name: "market_download_dataset",
    description: "Get download URL for a dataset",
    parameters: {
      type: "object",
      properties: {
        dataset_id: { type: "string", description: "The dataset ID" },
      },
      required: ["dataset_id"],
    },
    async execute(_id, params) {
      try {
        const dataset = await makeRequest(`/api/market/datasets/${params.dataset_id}`);
        
        return { 
          content: [{ 
            type: "text", 
            text: JSON.stringify({
              dataset_id: params.dataset_id,
              name: dataset.name,
              file_path: dataset.file_path,
              download_url: dataset.download_url || dataset.file_url,
              instructions: "Use exec tool with curl to download the file"
            }, null, 2) 
          }] 
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_download_document",
    description: "Get download URL for a document",
    parameters: {
      type: "object",
      properties: {
        document_id: { type: "string", description: "The document ID" },
      },
      required: ["document_id"],
    },
    async execute(_id, params) {
      try {
        const document = await makeRequest(`/api/market/documents/${params.document_id}`);
        
        return { 
          content: [{ 
            type: "text", 
            text: JSON.stringify({
              document_id: params.document_id,
              name: document.name,
              file_path: document.file_path,
              download_url: document.download_url || document.file_url,
              instructions: "Use exec tool with curl to download the file"
            }, null, 2) 
          }] 
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });
}

  // ========== Document Analysis Tools ==========

  api.registerTool({
    name: "market_analyze_document",
    description: "Analyze a document and extract metadata, structure, and content summary",
    parameters: {
      type: "object",
      properties: {
        document_id: { type: "string", description: "The document ID to analyze" },
      },
      required: ["document_id"],
    },
    async execute(_id, params) {
      try {
        const document = await makeRequest(`/api/market/documents/${params.document_id}`);
        
        return { 
          content: [{ 
            type: "text", 
            text: JSON.stringify({
              document_id: params.document_id,
              name: document.name,
              type: document.type,
              size: document.size,
              uploaded_at: document.created_at,
              // Would integrate with document analysis service
              analysis: {
                word_count: "N/A",
                page_count: "N/A",
                summary: "Document analysis requires additional processing"
              }
            }, null, 2) 
          }] 
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  // ========== RAG/Tools Integration ==========

  api.registerTool({
    name: "market_search_rag",
    description: "Search across all market content using RAG (datasets, documents, skills)",
    parameters: {
      type: "object",
      properties: {
        q: { type: "string", description: "Search query" },
        type: { type: "string", description: "Filter by type: all, dataset, document, skill" },
        limit: { type: "number", default: 10 },
      },
      required: ["q"],
    },
    async execute(_id, params) {
      try {
        const searchType = params.type || "all";
        const results = [];
        
        if (searchType === "all" || searchType === "dataset") {
          const datasets = await makeRequest(`/api/market/datasets/search?q=${encodeURIComponent(params.q)}&limit=${params.limit || 5}`);
          results.push({ type: "dataset", results: datasets });
        }
        
        if (searchType === "all" || searchType === "document") {
          const documents = await makeRequest(`/api/market/documents/search?q=${encodeURIComponent(params.q)}&limit=${params.limit || 5}`);
          results.push({ type: "document", results: documents });
        }
        
        if (searchType === "all" || searchType === "skill") {
          const skills = await makeRequest(`/api/market/skills/search?q=${encodeURIComponent(params.q)}&limit=${params.limit || 5}`);
          results.push({ type: "skill", results: skills });
        }
        
        return { content: [{ type: "text", text: JSON.stringify(results, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  // ========== Content Management ==========

  api.registerTool({
    name: "market_update_dataset",
    description: "Update dataset metadata",
    parameters: {
      type: "object",
      properties: {
        dataset_id: { type: "string", description: "Dataset ID to update" },
        name: { type: "string", description: "New name" },
        description: { type: "string", description: "New description" },
        tags: { type: "array", items: { type: "string" }, description: "New tags" },
        category: { type: "string", description: "New category" },
      },
      required: ["dataset_id"],
    },
    async execute(_id, params) {
      try {
        const { dataset_id, ...updateData } = params;
        const data = await makeRequest(`/api/market/datasets/${dataset_id}`, "PUT", updateData);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_update_document",
    description: "Update document metadata",
    parameters: {
      type: "object",
      properties: {
        document_id: { type: "string", description: "Document ID to update" },
        name: { type: "string", description: "New name" },
        description: { type: "string", description: "New description" },
        category: { type: "string", description: "New category" },
      },
      required: ["document_id"],
    },
    async execute(_id, params) {
      try {
        const { document_id, ...updateData } = params;
        const data = await makeRequest(`/api/market/documents/${document_id}`, "PUT", updateData);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  // ========== Sharing/Publication Tools ==========

  api.registerTool({
    name: "market_share_dataset",
    description: "Share a private dataset publicly or with specific users",
    parameters: {
      type: "object",
      properties: {
        dataset_id: { type: "string", description: "Dataset ID to share" },
        visibility: { type: "string", enum: ["public", "private", "shared"], description: "Visibility level" },
        allowed_users: { type: "array", items: { type: "string" }, description: "User IDs to share with" },
      },
      required: ["dataset_id", "visibility"],
    },
    async execute(_id, params) {
      try {
        const data = await makeRequest(`/api/market/datasets/${params.dataset_id}/share`, "POST", {
          visibility: params.visibility,
          allowed_users: params.allowed_users,
        });
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_share_document",
    description: "Share a private document publicly or with specific users",
    parameters: {
      type: "object",
      properties: {
        document_id: { type: "string", description: "Document ID to share" },
        visibility: { type: "string", enum: ["public", "private", "shared"], description: "Visibility level" },
        allowed_users: { type: "array", items: { type: "string" }, description: "User IDs to share with" },
      },
      required: ["document_id", "visibility"],
    },
    async execute(_id, params) {
      try {
        const data = await makeRequest(`/api/market/documents/${params.document_id}/share`, "POST", {
          visibility: params.visibility,
          allowed_users: params.allowed_users,
        });
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_share_skill",
    description: "Share a private skill publicly or with specific users",
    parameters: {
      type: "object",
      properties: {
        skill_id: { type: "string", description: "Skill ID to share" },
        visibility: { type: "string", enum: ["public", "private", "shared"], description: "Visibility level" },
        allowed_users: { type: "array", items: { type: "string" }, description: "User IDs to share with" },
      },
      required: ["skill_id", "visibility"],
    },
    async execute(_id, params) {
      try {
        const data = await makeRequest(`/api/market/skills/${params.skill_id}/share`, "POST", {
          visibility: params.visibility,
          allowed_users: params.allowed_users,
        });
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_publish_to_public",
    description: "Publish a private resource to public marketplace",
    parameters: {
      type: "object",
      properties: {
        resource_type: { type: "string", enum: ["dataset", "document", "skill"], description: "Resource type" },
        resource_id: { type: "string", description: "Resource ID to publish" },
        name: { type: "string", description: "Public name" },
        description: { type: "string", description: "Public description" },
        tags: { type: "array", items: { type: "string" }, description: "Public tags" },
      },
      required: ["resource_type", "resource_id"],
    },
    async execute(_id, params) {
      try {
        const endpoint = `/api/market/${params.resource_type}s/${params.resource_id}/publish`;
        const data = await makeRequest(endpoint, "POST", {
          name: params.name,
          description: params.description,
          tags: params.tags,
        });
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  // ========== Permission Management Tools ==========

  api.registerTool({
    name: "market_grant_permission",
    description: "Grant permission to a user for a specific resource",
    parameters: {
      type: "object",
      properties: {
        resource_type: { type: "string", enum: ["dataset", "document", "skill"], description: "Resource type" },
        resource_id: { type: "string", description: "Resource ID" },
        user_id: { type: "string", description: "User ID to grant access" },
        permission: { type: "string", enum: ["read", "write", "admin"], description: "Permission level" },
      },
      required: ["resource_type", "resource_id", "user_id", "permission"],
    },
    async execute(_id, params) {
      try {
        const endpoint = `/api/market/${params.resource_type}s/${params.resource_id}/permissions`;
        const data = await makeRequest(endpoint, "POST", {
          user_id: params.user_id,
          permission: params.permission,
        });
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_revoke_permission",
    description: "Revoke permission from a user for a specific resource",
    parameters: {
      type: "object",
      properties: {
        resource_type: { type: "string", enum: ["dataset", "document", "skill"], description: "Resource type" },
        resource_id: { type: "string", description: "Resource ID" },
        user_id: { type: "string", description: "User ID to revoke access" },
      },
      required: ["resource_type", "resource_id", "user_id"],
    },
    async execute(_id, params) {
      try {
        const endpoint = `/api/market/${params.resource_type}s/${params.resource_id}/permissions/${params.user_id}`;
        const data = await makeRequest(endpoint, "DELETE");
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_list_permissions",
    description: "List all permissions for a specific resource",
    parameters: {
      type: "object",
      properties: {
        resource_type: { type: "string", enum: ["dataset", "document", "skill"], description: "Resource type" },
        resource_id: { type: "string", description: "Resource ID" },
      },
      required: ["resource_type", "resource_id"],
    },
    async execute(_id, params) {
      try {
        const endpoint = `/api/market/${params.resource_type}s/${params.resource_id}/permissions`;
        const data = await makeRequest(endpoint);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_check_permission",
    description: "Check if current user has permission to access a resource",
    parameters: {
      type: "object",
      properties: {
        resource_type: { type: "string", enum: ["dataset", "document", "skill"], description: "Resource type" },
        resource_id: { type: "string", description: "Resource ID" },
        required_permission: { type: "string", enum: ["read", "write", "admin"], description: "Required permission level" },
      },
      required: ["resource_type", "resource_id", "required_permission"],
    },
    async execute(_id, params) {
      try {
        const endpoint = `/api/market/${params.resource_type}s/${params.resource_id}/check-permission?permission=${params.required_permission}`;
        const data = await makeRequest(endpoint);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  // ========== Version Management Tools ==========

  api.registerTool({
    name: "market_list_versions",
    description: "List all versions of a resource",
    parameters: {
      type: "object",
      properties: {
        resource_type: { type: "string", enum: ["dataset", "document", "skill"], description: "Resource type" },
        resource_id: { type: "string", description: "Resource ID" },
      },
      required: ["resource_type", "resource_id"],
    },
    async execute(_id, params) {
      try {
        const endpoint = `/api/market/${params.resource_type}s/${params.resource_id}/versions`;
        const data = await makeRequest(endpoint);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_create_version",
    description: "Create a new version of an existing resource",
    parameters: {
      type: "object",
      properties: {
        resource_type: { type: "string", enum: ["dataset", "document", "skill"], description: "Resource type" },
        resource_id: { type: "string", description: "Resource ID" },
        version_note: { type: "string", description: "Version description/changelog" },
      },
      required: ["resource_type", "resource_id"],
    },
    async execute(_id, params) {
      try {
        const endpoint = `/api/market/${params.resource_type}s/${params.resource_id}/versions`;
        const data = await makeRequest(endpoint, "POST", { note: params.version_note });
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_rollback_version",
    description: "Rollback to a previous version of a resource",
    parameters: {
      type: "object",
      properties: {
        resource_type: { type: "string", enum: ["dataset", "document", "skill"], description: "Resource type" },
        resource_id: { type: "string", description: "Resource ID" },
        version: { type: "string", description: "Version to rollback to" },
      },
      required: ["resource_type", "resource_id", "version"],
    },
    async execute(_id, params) {
      try {
        const endpoint = `/api/market/${params.resource_type}s/${params.resource_id}/versions/${params.version}/rollback`;
        const data = await makeRequest(endpoint, "POST");
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  // ========== Category & Tag Tools ==========

  api.registerTool({
    name: "market_list_categories",
    description: "List all categories",
    parameters: {
      type: "object",
      properties: {
        resource_type: { type: "string", enum: ["dataset", "document", "skill"], description: "Resource type" },
      },
      required: ["resource_type"],
    },
    async execute(_id, params) {
      try {
        const endpoint = `/api/market/${params.resource_type}s/categories`;
        const data = await makeRequest(endpoint);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_create_category",
    description: "Create a new category",
    parameters: {
      type: "object",
      properties: {
        resource_type: { type: "string", enum: ["dataset", "document", "skill"], description: "Resource type" },
        name: { type: "string", description: "Category name" },
        description: { type: "string", description: "Category description" },
      },
      required: ["resource_type", "name"],
    },
    async execute(_id, params) {
      try {
        const endpoint = `/api/market/${params.resource_type}s/categories`;
        const data = await makeRequest(endpoint, "POST", {
          name: params.name,
          description: params.description,
        });
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_list_tags",
    description: "List all tags or get tag details",
    parameters: {
      type: "object",
      properties: {
        resource_type: { type: "string", enum: ["dataset", "document", "skill"], description: "Resource type" },
        tag_name: { type: "string", description: "Specific tag name (optional)" },
      },
      required: ["resource_type"],
    },
    async execute(_id, params) {
      try {
        const endpoint = params.tag_name 
          ? `/api/market/${params.resource_type}s/tags/${params.tag_name}`
          : `/api/market/${params.resource_type}s/tags`;
        const data = await makeRequest(endpoint);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  // ========== Import/Export Tools ==========

  api.registerTool({
    name: "market_export_resource",
    description: "Export a resource as a downloadable package",
    parameters: {
      type: "object",
      properties: {
        resource_type: { type: "string", enum: ["dataset", "document", "skill"], description: "Resource type" },
        resource_id: { type: "string", description: "Resource ID" },
        format: { type: "string", enum: ["json", "zip"], default: "json", description: "Export format" },
      },
      required: ["resource_type", "resource_id"],
    },
    async execute(_id, params) {
      try {
        const endpoint = `/api/market/${params.resource_type}s/${params.resource_id}/export?format=${params.format || "json"}`;
        const data = await makeRequest(endpoint);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_import_resource",
    description: "Import a resource from a package",
    parameters: {
      type: "object",
      properties: {
        resource_type: { type: "string", enum: ["dataset", "document", "skill"], description: "Resource type" },
        package_url: { type: "string", description: "URL to the package" },
        name: { type: "string", description: "Name for imported resource" },
      },
      required: ["resource_type", "package_url"],
    },
    async execute(_id, params) {
      try {
        const endpoint = `/api/market/${params.resource_type}s/import`;
        const data = await makeRequest(endpoint, "POST", {
          package_url: params.package_url,
          name: params.name,
        });
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  // ========== Activity Log Tools ==========

  api.registerTool({
    name: "market_get_activity_log",
    description: "Get activity log for a resource or user",
    parameters: {
      type: "object",
      properties: {
        resource_type: { type: "string", enum: ["dataset", "document", "skill"], description: "Resource type" },
        resource_id: { type: "string", description: "Resource ID" },
        user_id: { type: "string", description: "User ID" },
        limit: { type: "number", default: 20, description: "Number of entries" },
      },
      required: [],
    },
    async execute(_id, params) {
      try {
        let endpoint = "/api/market/activity?";
        if (params.resource_type && params.resource_id) {
          endpoint += `resource_type=${params.resource_type}&resource_id=${params.resource_id}`;
        } else if (params.user_id) {
          endpoint += `user_id=${params.user_id}`;
        }
        endpoint += `&limit=${params.limit || 20}`;
        const data = await makeRequest(endpoint);
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  // ========== Backup Tools ==========

  api.registerTool({
    name: "market_create_backup",
    description: "Create a backup of market data",
    parameters: {
      type: "object",
      properties: {
        include_datasets: { type: "boolean", default: true },
        include_documents: { type: "boolean", default: true },
        include_skills: { type: "boolean", default: true },
      },
      required: [],
    },
    async execute(_id, params) {
      try {
        const endpoint = "/api/market/backup";
        const data = await makeRequest(endpoint, "POST", {
          include_datasets: params.include_datasets,
          include_documents: params.include_documents,
          include_skills: params.include_skills,
        });
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_restore_backup",
    description: "Restore from a backup",
    parameters: {
      type: "object",
      properties: {
        backup_id: { type: "string", description: "Backup ID to restore" },
      },
      required: ["backup_id"],
    },
    async execute(_id, params) {
      try {
        const endpoint = `/api/market/backup/${params.backup_id}/restore`;
        const data = await makeRequest(endpoint, "POST");
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_list_backups",
    description: "List available backups",
    parameters: {
      type: "object",
      properties: {},
    },
    async execute(_id, _params) {
      try {
        const data = await makeRequest("/api/market/backup");
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });
}
