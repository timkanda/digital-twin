"use client";

import { useState } from "react";
import { chatWithDigitalTwin, getVectorInfo } from "./actions";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [vectorInfo, setVectorInfo] = useState<{ vectorCount: number; dimension: number } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await chatWithDigitalTwin(userMessage);
      setMessages((prev) => [...prev, { role: "assistant", content: response }]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${error instanceof Error ? error.message : "Something went wrong"}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const checkVectorDB = async () => {
    try {
      const info = await getVectorInfo();
      setVectorInfo(info);
    } catch (error) {
      console.error("Error checking vector DB:", error);
    }
  };

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">🤖 Digital Twin MCP Server</h1>
          <p className="text-gray-400">AI-powered interview assistant using RAG</p>
          <div className="mt-4 flex justify-center gap-4 text-sm">
            <span className="px-3 py-1 bg-blue-900/50 rounded-full">Upstash Vector</span>
            <span className="px-3 py-1 bg-green-900/50 rounded-full">Groq LLM</span>
            <span className="px-3 py-1 bg-purple-900/50 rounded-full">MCP Protocol</span>
          </div>
        </div>

        {/* Vector DB Status */}
        <div className="card mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="font-semibold mb-1">Vector Database Status</h2>
              {vectorInfo ? (
                <p className="text-sm text-gray-400">
                  ✅ Connected - {vectorInfo.vectorCount} vectors loaded
                </p>
              ) : (
                <p className="text-sm text-gray-400">Click to check connection</p>
              )}
            </div>
            <button onClick={checkVectorDB} className="btn-primary text-sm">
              Check Status
            </button>
          </div>
        </div>

        {/* MCP Endpoint Info */}
        <div className="card mb-6">
          <h2 className="font-semibold mb-2">MCP Endpoint</h2>
          <code className="text-sm text-blue-400 bg-black/50 px-3 py-2 rounded block">
            POST http://localhost:3000/api/mcp
          </code>
          <p className="text-sm text-gray-400 mt-2">
            Available tools: <code>ask_digital_twin</code>, <code>get_profile_info</code>
          </p>
        </div>

        {/* Chat Interface */}
        <div className="card">
          <h2 className="font-semibold mb-4">Chat with Digital Twin</h2>
          
          {/* Messages */}
          <div className="space-y-4 mb-4 max-h-96 overflow-y-auto">
            {messages.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <p>Ask me about my experience, skills, projects, or career goals!</p>
                <div className="mt-4 space-y-2 text-sm">
                  <p className="text-gray-600">💡 Try asking:</p>
                  <p>&quot;What are your technical skills?&quot;</p>
                  <p>&quot;Tell me about your work experience&quot;</p>
                  <p>&quot;What projects have you worked on?&quot;</p>
                </div>
              </div>
            )}
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={msg.role === "user" ? "message-user" : "message-assistant"}
              >
                <p className="text-sm font-medium mb-1 text-gray-400">
                  {msg.role === "user" ? "You" : "🤖 Digital Twin"}
                </p>
                <p className="whitespace-pre-wrap">{msg.content}</p>
              </div>
            ))}
            {isLoading && (
              <div className="message-assistant">
                <p className="text-sm font-medium mb-1 text-gray-400">🤖 Digital Twin</p>
                <p className="loading-dots">Thinking</p>
              </div>
            )}
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me anything..."
              className="input flex-1"
              disabled={isLoading}
            />
            <button type="submit" className="btn-primary" disabled={isLoading || !input.trim()}>
              Send
            </button>
          </form>
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-sm text-gray-500">
          <p>Timothy Kipchirchir Kanda - Digital Twin MCP Server</p>
        </div>
      </div>
    </div>
  );
}
