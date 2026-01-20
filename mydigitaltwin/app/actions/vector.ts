"use server";

import { Index } from "@upstash/vector";

// Types for vector query results
interface VectorMetadata {
  title: string;
  type: string;
  content: string;
  category: string;
  tags: string[];
}

interface QueryResult {
  id: string;
  score: number;
  metadata?: VectorMetadata;
}

// Initialize Upstash Vector client
function getVectorIndex(): Index {
  const url = process.env.UPSTASH_VECTOR_REST_URL;
  const token = process.env.UPSTASH_VECTOR_REST_TOKEN;

  if (!url || !token) {
    throw new Error("Upstash Vector credentials not configured");
  }

  return new Index({
    url,
    token,
  });
}

/**
 * Query vectors from Upstash Vector database
 * Matches the Python implementation exactly
 */
export async function queryVectors(
  queryText: string,
  topK: number = 3
): Promise<QueryResult[]> {
  try {
    const index = getVectorIndex();

    const results = await index.query({
      data: queryText,
      topK,
      includeMetadata: true,
    });

    return results.map((result) => ({
      id: String(result.id),
      score: result.score,
      metadata: result.metadata as VectorMetadata | undefined,
    }));
  } catch (error) {
    console.error("Error querying vectors:", error);
    throw new Error(`Failed to query vectors: ${error instanceof Error ? error.message : "Unknown error"}`);
  }
}

/**
 * Get relevant context for RAG from vector database
 */
export async function getRelevantContext(
  question: string,
  topK: number = 3
): Promise<{ title: string; content: string; score: number }[]> {
  const results = await queryVectors(question, topK);

  return results
    .filter((result) => result.metadata?.content)
    .map((result) => ({
      title: result.metadata?.title || "Information",
      content: result.metadata?.content || "",
      score: result.score,
    }));
}

/**
 * Get vector database info
 */
export async function getVectorInfo(): Promise<{
  vectorCount: number;
  dimension: number;
}> {
  try {
    const index = getVectorIndex();
    const info = await index.info();
    
    return {
      vectorCount: info.vectorCount || 0,
      dimension: info.dimension || 0,
    };
  } catch (error) {
    console.error("Error getting vector info:", error);
    throw new Error(`Failed to get vector info: ${error instanceof Error ? error.message : "Unknown error"}`);
  }
}
