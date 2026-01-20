"use server";

import Groq from "groq-sdk";
import { getRelevantContext } from "./vector";

// Types
interface RAGResponse {
  answer: string;
  sources: { title: string; content: string; score: number }[];
}

// Default model - matching Python implementation
const DEFAULT_MODEL = "llama-3.1-8b-instant";

// Initialize Groq client
function getGroqClient(): Groq {
  const apiKey = process.env.GROQ_API_KEY;

  if (!apiKey) {
    throw new Error("GROQ_API_KEY not configured");
  }

  return new Groq({ apiKey });
}

/**
 * Generate response using Groq LLM
 * Matches the Python implementation
 */
export async function generateResponse(
  prompt: string,
  model: string = DEFAULT_MODEL
): Promise<string> {
  try {
    const client = getGroqClient();

    const completion = await client.chat.completions.create({
      model,
      messages: [
        {
          role: "system",
          content:
            "You are an AI digital twin. Answer questions as if you are the person, speaking in first person about your background, skills, and experience.",
        },
        {
          role: "user",
          content: prompt,
        },
      ],
      temperature: 0.7,
      max_tokens: 500,
    });

    return completion.choices[0]?.message?.content?.trim() || "No response generated";
  } catch (error) {
    console.error("Error generating response:", error);
    throw new Error(`Failed to generate response: ${error instanceof Error ? error.message : "Unknown error"}`);
  }
}

/**
 * Perform RAG query - combines vector search with LLM generation
 * This is the main function that matches the Python rag_query implementation
 */
export async function ragQuery(question: string): Promise<RAGResponse> {
  try {
    // Step 1: Get relevant context from vector database
    const sources = await getRelevantContext(question, 3);

    if (sources.length === 0) {
      return {
        answer: "I don't have specific information about that topic.",
        sources: [],
      };
    }

    // Step 2: Build context from sources
    const context = sources
      .map((source) => `${source.title}: ${source.content}`)
      .join("\n\n");

    // Step 3: Create prompt with context
    const prompt = `Based on the following information about yourself, answer the question.
Speak in first person as if you are describing your own background.

Your Information:
${context}

Question: ${question}

Provide a helpful, professional response:`;

    // Step 4: Generate response using Groq
    const answer = await generateResponse(prompt);

    return {
      answer,
      sources,
    };
  } catch (error) {
    console.error("Error in RAG query:", error);
    throw new Error(`RAG query failed: ${error instanceof Error ? error.message : "Unknown error"}`);
  }
}

/**
 * Chat with digital twin - simplified interface
 */
export async function chatWithDigitalTwin(message: string): Promise<string> {
  const response = await ragQuery(message);
  return response.answer;
}
