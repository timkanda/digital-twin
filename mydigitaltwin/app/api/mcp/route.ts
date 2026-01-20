import { NextRequest, NextResponse } from "next/server";
import { ragQuery, getVectorInfo } from "@/app/actions";

// MCP Protocol Types
interface MCPRequest {
  jsonrpc: "2.0";
  id: string | number;
  method: string;
  params?: Record<string, unknown>;
}

interface MCPResponse {
  jsonrpc: "2.0";
  id: string | number;
  result?: unknown;
  error?: {
    code: number;
    message: string;
    data?: unknown;
  };
}

// MCP Tool definitions
const TOOLS = [
  {
    name: "ask_digital_twin",
    description: "Ask the digital twin a question about their professional background, skills, experience, education, or career goals.",
    inputSchema: {
      type: "object",
      properties: {
        question: {
          type: "string",
          description: "The question to ask the digital twin",
        },
      },
      required: ["question"],
    },
  },
  {
    name: "get_profile_info",
    description: "Get information about the digital twin's vector database status",
    inputSchema: {
      type: "object",
      properties: {},
      required: [],
    },
  },
];

// Handle MCP requests
async function handleMCPRequest(request: MCPRequest): Promise<MCPResponse> {
  const { id, method, params } = request;

  try {
    switch (method) {
      case "initialize":
        return {
          jsonrpc: "2.0",
          id,
          result: {
            protocolVersion: "2024-11-05",
            serverInfo: {
              name: "digital-twin-mcp",
              version: "1.0.0",
            },
            capabilities: {
              tools: {},
            },
          },
        };

      case "tools/list":
        return {
          jsonrpc: "2.0",
          id,
          result: {
            tools: TOOLS,
          },
        };

      case "tools/call":
        const toolName = params?.name as string;
        const toolArgs = params?.arguments as Record<string, unknown>;

        if (toolName === "ask_digital_twin") {
          const question = toolArgs?.question as string;
          if (!question) {
            return {
              jsonrpc: "2.0",
              id,
              error: {
                code: -32602,
                message: "Missing required parameter: question",
              },
            };
          }

          const response = await ragQuery(question);
          return {
            jsonrpc: "2.0",
            id,
            result: {
              content: [
                {
                  type: "text",
                  text: response.answer,
                },
              ],
              metadata: {
                sources: response.sources.map((s) => ({
                  title: s.title,
                  relevance: s.score,
                })),
              },
            },
          };
        }

        if (toolName === "get_profile_info") {
          const info = await getVectorInfo();
          return {
            jsonrpc: "2.0",
            id,
            result: {
              content: [
                {
                  type: "text",
                  text: `Digital Twin Profile Status:\n- Vector Count: ${info.vectorCount}\n- Dimension: ${info.dimension}`,
                },
              ],
            },
          };
        }

        return {
          jsonrpc: "2.0",
          id,
          error: {
            code: -32601,
            message: `Unknown tool: ${toolName}`,
          },
        };

      default:
        return {
          jsonrpc: "2.0",
          id,
          error: {
            code: -32601,
            message: `Method not found: ${method}`,
          },
        };
    }
  } catch (error) {
    return {
      jsonrpc: "2.0",
      id,
      error: {
        code: -32603,
        message: error instanceof Error ? error.message : "Internal error",
      },
    };
  }
}

// POST handler for MCP requests
export async function POST(request: NextRequest) {
  try {
    const body = await request.json() as MCPRequest;
    const response = await handleMCPRequest(body);
    return NextResponse.json(response);
  } catch {
    return NextResponse.json(
      {
        jsonrpc: "2.0",
        id: null,
        error: {
          code: -32700,
          message: "Parse error",
        },
      },
      { status: 400 }
    );
  }
}

// GET handler for health check
export async function GET() {
  return NextResponse.json({
    status: "ok",
    server: "digital-twin-mcp",
    version: "1.0.0",
    tools: TOOLS.map((t) => t.name),
  });
}
