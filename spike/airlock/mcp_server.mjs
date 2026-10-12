import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";

const server = new Server({ name: "fake-fs", version: "1.0.0" }, { capabilities: { tools: {} } });
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    { name: "read_file", description: "read", inputSchema: { type: "object", properties: { path: { type: "string" } }, required: ["path"] } },
    { name: "write_file", description: "write", inputSchema: { type: "object", properties: { path: { type: "string" } }, required: ["path"] } },
  ],
}));
server.setRequestHandler(CallToolRequestSchema, async (req) => ({
  content: [{ type: "text", text: `SERVER-EXECUTED: ${req.params.name} ${req.params.arguments?.path}` }],
}));
await server.connect(new StdioServerTransport());
