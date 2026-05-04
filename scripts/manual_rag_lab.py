
import asyncio
import os
import sys
import uuid
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.modules.knowledge_bases.service import TextChunker
from app.core.embeddings import EmbeddingGenerator
from app.core.entity_extraction import EntityExtractor
from app.core.neo4j_repository import Neo4jRepository
from app.core.neo4j import init_neo4j

# ============================================================================
# MANUAL RAG LABORATORY - STEP-BY-STEP AUDIT
# ============================================================================

async def manual_rag_audit(file_path: str):
    settings = get_settings()
    tenant_id = "3e216e9a-a8b2-410f-bd53-ba2e3522845e" # Using your example tenant
    agent_id = str(uuid.uuid4())
    kb_id = str(uuid.uuid4())
    
    print("\n" + "="*80)
    print("🔬 MANUAL RAG PIPELINE LABORATORY")
    print("="*80)

    # --- STEP 1: TEXT EXTRACTION ---
    print("\n[STEP 1] Extracting Text from PDF...")
    # For this manual lab, we'll simulate the text extraction to ensure we have content
    # In production, this uses ingest_document route with file upload.
    raw_text = """
    EMPLOYEE PAYSLIP - OCTOBER 2025
    Employee Name: Girinath Pant
    Designation: Senior AI Engineer
    Department: Advanced Research
    Base Salary: $12,500
    Tax Deductions: $2,100
    Net Pay: $10,400
    
    This document is a confidential payslip for Girinath Pant.
    The primary topics are financial compensation and tax compliance.
    """
    print(f"✅ Text Extracted. Length: {len(raw_text)} chars.")

    # --- STEP 2: CHUNKING ---
    print("\n[STEP 2] Chunking Text...")
    chunks = TextChunker.split_into_chunks(raw_text, chunk_size=500, overlap_size=50)
    for i, chunk in enumerate(chunks):
        print(f"   Chunk {i+1}: {chunk[:60]}...")
    print(f"✅ Created {len(chunks)} chunks.")

    # --- STEP 3: EMBEDDING GENERATION ---
    print(f"\n[STEP 3] Generating {settings.embedding_dimension}-dim Embeddings...")
    embeddings = await EmbeddingGenerator.generate_embeddings_batch(chunks)
    print(f"✅ Generated {len(embeddings)} embeddings. Size: {len(embeddings[0])} each.")

    # --- STEP 4: ENTITY EXTRACTION ---
    print("\n[STEP 4] Extracting Entities & Relationships...")
    entities = []
    for chunk in chunks:
        extracted = await EntityExtractor.extract_entities(chunk)
        entities.extend(extracted)
    
    print(f"✅ Found {len(entities)} entities (e.g., {[e.text for e in entities[:3]]})")

    # --- STEP 5: MANUAL GRAPH INGESTION ---
    print("\n[STEP 5] Syncing to Neo4j Graph...")
    repo = Neo4jRepository(tenant_id)
    
    # Create KB node
    await repo.execute_write(
        "CREATE (kb:KnowledgeBase {id: $kb_id, tenant_id: $tenant_id, name: $name})",
        {"kb_id": kb_id, "tenant_id": tenant_id, "name": "MANUAL_LAB_TEST"}
    )
    
    # Create Chunks
    for i, (text, emb) in enumerate(zip(chunks, embeddings)):
        unique_chunk_id = str(uuid.uuid4())
        await repo.execute_write(
            "CREATE (c:Chunk {id: $id, text: $text, embedding: $emb, tenant_id: $tenant_id, kb_id: $kb_id})",
            {"id": unique_chunk_id, "text": text, "emb": emb, "tenant_id": tenant_id, "kb_id": kb_id}
        )
        await repo.execute_write(
            "MATCH (kb:KnowledgeBase {id: $kb_id, tenant_id: $tenant_id}), (c:Chunk {id: $id, tenant_id: $tenant_id}) CREATE (kb)-[:HAS_CHUNK]->(c)",
            {"kb_id": kb_id, "id": unique_chunk_id, "tenant_id": tenant_id}
        )
    print(f"✅ Graph Ingested Successfully.")

    # --- STEP 6: RETRIEVAL TEST ---
    print("\n[STEP 6] Testing Retrieval Accuracy...")
    query = "Who is the employee recorded in this payslip?"
    query_emb = await EmbeddingGenerator.generate_embedding(query)
    
    # Simple semantic retrieval
    search_query = """
    MATCH (kb:KnowledgeBase {id: $kb_id, tenant_id: $tenant_id})-[:HAS_CHUNK]->(c)
    RETURN c.text as text, c.embedding as embedding
    """
    results = await repo.execute_read(search_query, {"kb_id": kb_id, "tenant_id": tenant_id})
    
    print(f"   Searching through {len(results)} chunks in the Graph...")
    scored = []
    for res in results:
        score = EmbeddingGenerator.cosine_similarity(query_emb, res['embedding'])
        scored.append((score, res['text']))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    
    print("\n🏆 RETRIEVAL RESULTS (Ranked by Semantic Score):")
    for score, text in scored[:2]:
        print(f"   [{score:.4f}] {text[:150]}...")

    print("\n🏁 LAB TEST COMPLETE")

if __name__ == "__main__":
    async def main():
        await init_neo4j()
        await manual_rag_audit("Payslip_Girinath_Oct_2025.pdf")
    
    asyncio.run(main())
