// Lab Tools Plugin - Market Service integration
// This plugin provides agent tools to interact with Market Service

export default function (api) {
  const MARKET_SERVICE_URL = "http://localhost:8000";

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
