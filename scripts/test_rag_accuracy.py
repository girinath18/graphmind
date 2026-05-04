
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.modules.rag.pipeline import RAGPipeline
from app.core.database import init_db
from app.core.neo4j import init_neo4j

# ============================================================================
# Standalone RAG Accuracy Validator
# ============================================================================
# This script tests the RAG logic DIRECTLY, bypassing the API layer.
# It is used for evaluating retrieval precision and answer quality.

async def test_rag_standalone(agent_id: str, kb_id: str, query: str):
    settings = get_settings()
    
    print("\n" + "="*80)
    print("📊 STANDALONE RAG ACCURACY TEST")
    print("="*80)
    print(f"Agent: {agent_id}")
    print(f"KB:    {kb_id}")
    print(f"Query: {query}")
    print("-" * 80)

    # 1. Initialize Pipeline (Tenant ID 'standalone-test')
    # Use a dummy/actual tenant ID depending on your DB state
    tenant_id = "3e216e9a-a8b2-410f-bd53-ba2e3522845e" # From your curl example
    pipeline = RAGPipeline(tenant_id)

    try:
        # 2. Execute Pipeline
        print("🧠 Running RAG Graph Traversal...")
        context = await pipeline.query(
            query=query,
            agent_id=agent_id,
            kb_id=kb_id,
            top_k=5
        )

        # 3. Analyze Retrieval Accuracy
        print("\n🔎 RETRIEVAL ANALYSIS:")
        print(f"   - Chunks Found: {len(context.chunks)}")
        
        if not context.chunks:
            print("   ❌ FAILED: No relevant context was retrieved from the Graph.")
            print("   Check: Is the document ingested? Are the embeddings 1024-dim?")
            return

        for i, chunk in enumerate(context.chunks[:3]):
            print(f"   [{i+1}] Score: {chunk.get('similarity', 0):.4f} | Content: {chunk['text'][:100]}...")

        # 4. Analyze Generation Quality (Prompting LLM)
        print("\n🤖 LLM GENERATION:")
        # In a real scenario, the RAGService calls the LLM with this context.
        # Here we show the final reasoning output.
        
        # Simulating the Service layer logic
        from app.core.llm.deepinfra import DeepInfraClient
        llm = DeepInfraClient()
        
        prompt = f"""
        Use the following CONTEXT to answer the QUERY.
        If the answer isn't in the context, say you don't know based on the knowledge base.
        
        CONTEXT:
        {chr(10).join([c['text'] for c in context.chunks])}
        
        QUERY: {query}
        """
        
        print("   Waiting for AI response...")
        answer = await llm.generate(prompt)
        
        print("\n" + "🏁 FINAL ANSWER:")
        print("-" * 40)
        print(answer)
        print("-" * 40)
        
        print("\n✅ TEST COMPLETE")

    except Exception as e:
        print(f"❌ ERROR DURING TEST: {e}")

if __name__ == "__main__":
    # Parameters from your recent attempts
    AGENT_ID = "1ff998f3-b435-4d77-9bb3-cdd0df1def78"
    KB_ID = "a8c2e8f2-070f-42dc-9089-3bc1d1b9601c"
    QUERY = "What is the employee name used in the document"

    # Ensure Neo4j is up before starting
    async def main():
        await init_neo4j()
        await test_rag_standalone(AGENT_ID, KB_ID, QUERY)

    asyncio.run(main())
