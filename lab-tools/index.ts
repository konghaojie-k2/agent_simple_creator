// Lab Tools Plugin - Market Service integration
// This plugin provides agent tools to interact with Market Service

export default function (api) {
  const MARKET_SERVICE_URL = "http://localhost:8000";

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

        const response = await fetch(
          `${MARKET_SERVICE_URL}/api/market/datasets?${queryParams.toString()}`
        );
        const data = await response.json();
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
        const response = await fetch(
          `${MARKET_SERVICE_URL}/api/market/datasets/${params.dataset_id}`
        );
        const data = await response.json();
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });

  api.registerTool({
    name: "market_search_datasets",
    description: "Search datasets by keyword",
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
        const response = await fetch(
          `${MARKET_SERVICE_URL}/api/market/datasets/search?${queryParams.toString()}`
        );
        const data = await response.json();
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

        const response = await fetch(
          `${MARKET_SERVICE_URL}/api/market/documents?${queryParams.toString()}`
        );
        const data = await response.json();
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
        const response = await fetch(
          `${MARKET_SERVICE_URL}/api/market/documents/${params.document_id}`
        );
        const data = await response.json();
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

        const response = await fetch(
          `${MARKET_SERVICE_URL}/api/market/skills?${queryParams.toString()}`
        );
        const data = await response.json();
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
        const response = await fetch(
          `${MARKET_SERVICE_URL}/api/market/skills/${params.skill_id}`
        );
        const data = await response.json();
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
        const response = await fetch(
          `${MARKET_SERVICE_URL}/api/market/skills/search?${queryParams.toString()}`
        );
        const data = await response.json();
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error.message}` }] };
      }
    },
  });
}
