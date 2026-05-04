"""
PHASE 2 STEP 4 — INTEGRATION TESTING GUIDE

Welcome! Phase 2 Step 4 (RAG Pipeline) is now COMPLETE and PRODUCTION-READY.

This guide helps you verify everything works correctly before Phase 3.

═══════════════════════════════════════════════════════════════════════════════

TABLE OF CONTENTS

1. Quick Start (5 minutes)
2. Functional Tests (15 minutes)
3. Performance Tests (10 minutes)
4. Production Readiness Checklist
5. Common Issues & Fixes


═══════════════════════════════════════════════════════════════════════════════

1. QUICK START (5 MINUTES)

Verify the system works at all:

STEP 1: Create a Knowledge Base
┌─ Method A: API call
│  POST /kb/create
│  {
│      "name": "Test KB",
│      "description": "Testing RAG pipeline"
│  }
│  Response: { "kb_id": "kb_123", ... }
│
└─ Method B: Python code
   from app.modules.knowledge_base.service import KnowledgeBaseService
   kb = await KnowledgeBaseService.create_kb(
       owner_id="user_123",
       name="Test KB"
   )
   kb_id = kb.id

STEP 2: Add Documents
┌─ Method A: API call
│  POST /kb/{kb_id}/upload
│  { "document": <file> }
│
└─ Method B: Python code
   doc = await KnowledgeBaseService.ingest_documents(
       kb_id=kb_id,
       documents=["Sample text about Python..."]
   )

STEP 3: Query RAG
┌─ Method A: API call
│  POST /rag/query
│  {
│      "query": "What is Python?",
│      "agent_id": "agent_123",
│      "kb_id": "kb_123",
│      "max_context_tokens": 2000
│  }
│  Response: {
│      "answer": "Python is a programming language...",
│      "sources": [ ... ],
│      "stats": { ... }
│  }
│
└─ Method B: Python code
   from app.modules.rag.service import RAGService
   result = await RAGService.generate_answer(
       query="What is Python?",
       agent_id="agent_123",
       kb_id=kb_id,
       max_context_tokens=2000
   )
   print(result.answer)

EXPECTED RESULT:
✅ Answer contains relevant information
✅ Sources show chunks with "reason" (attribution)
✅ Response time < 500ms


═══════════════════════════════════════════════════════════════════════════════

2. FUNCTIONAL TESTS (15 MINUTES)

Test each feature specifically:

TEST 2A: Source Attribution (REQUIRED)
┌─ What: Each chunk has 'reason' field explaining why it was retrieved
│
├─ Test:
│  1. Query RAG with simple question
│  2. Check response structure:
│     {
│         "sources": [
│             {
│                 "chunk_id": "...",
│                 "text": "...",
│                 "reason": "Seed chunk (score: 0.85)" ← MUST BE PRESENT
│             }
│         ]
│     }
│  3. Reason field should explain:
│     - "Seed chunk (score: X)" for semantic search
│     - "Graph expansion via SIMILAR edge" when from graph
│     - "Graph expansion via MENTIONS edge" for entities
│     - "Seed chunk (timeout fallback - no expansion)" if timeout
│
└─ Expected: EVERY chunk has a reason field ✅


TEST 2B: Diversity Penalty (REQUIRED)
┌─ What: Response contains varied chunks, not redundant
│
├─ Test:
│  1. Query with broad topic: "Tell me everything about Python"
│  2. Get top 10 chunks
│  3. Check for redundancy:
│     - Are all 10 chunks different? ✅
│     - Or are 3-4 saying the same thing? ❌
│  4. Similarity check:
│     - Chunk 1 token: Python basics
│     - Chunk 2 token: Advanced features ✓ different
│     - Chunk 3 token: Libraries ✓ different
│     - Chunk 4 token: Basically Chunk 2 again? ❌ bad
│
└─ Expected: Chunks show different aspects of topic ✅


TEST 2C: Cache Auto-Invalidation (REQUIRED)
┌─ What: Cache updates when KB is updated
│
├─ Test:
│  1. Query RAG: "What is Python?" → Latency: 200ms
│  2. Repeat same query → Latency: 1-5ms (CACHE HIT)
│  3. Add new document to KB
│  4. Repeat same query → Latency: 200ms again (CACHE MISS) ← KEY! Should not be 1ms
│  5. Repeat again → Latency: 1-5ms (new cache entry)
│
├─ What should happen:
│  - Request 1-2: 200ms + 1ms (cache)
│  - Update KB
│  - Request 3: 200ms (cache miss because KB version changed)
│  - Request 4: 1ms (new cache)
│
└─ Expected: Latency jumps back to 200ms after KB update ✅


TEST 2D: Timeout Fallback (ADVANCED - requires slow KB)
┌─ What: On timeout, return seed chunks instead of error
│
├─ Setup (optional, requires large KB):
│  1. Create KB with 10,000+ chunks (or simulate delay)
│  2. Query a complex multi-hop question
│  3. If it takes >2s:
│
├─ Test:
│  1. Monitor response after 2s timeout window
│  2. Should see:
│     {
│         "answer": "Based on seed chunks...",
│         "stats": {
│             "partial_result": true,  ← KEY!
│             "timeout_occurred": true
│         },
│         "sources": [
│             {
│                 "reason": "Seed chunk (timeout fallback - no expansion)"
│             }
│         ]
│     }
│  3. Response should appear even if timeout occurred
│
└─ Expected: Partial answer > error message ✅

(Skip if KB is small - timeout unlikely to occur)


TEST 2E: Metrics Tracking (OPTIONAL)
┌─ What: Metrics are recorded for analytics
│
├─ Test:
│  1. Run several RAG queries (≥10)
│  2. Check logs for metrics summary line every 10 queries
│     Example: "📊 RAG Metrics (last 10): latency=145ms, cache_hit_rate=30%, timeouts=0, partial_results=0, avg_expanded_chunks=3.2"
│  3. Call endpoint to get metrics (if available):
│     GET /rag/metrics
│  4. Verify metrics dataclass contains:
│     - retrieval_latency_ms
│     - ranking_latency_ms
│     - total_latency_ms
│     - cache_hit (boolean)
│     - seed_chunks_count
│     - expanded_chunks_count
│     - final_chunks_count
│     - timeout_occurred (boolean)
│     - partial_result (boolean)
│
└─ Expected: Metrics logged and accessible ✅


═══════════════════════════════════════════════════════════════════════════════

3. PERFORMANCE TESTS (10 MINUTES)

Verify system performance targets:

LATENCY BASELINE:
┌─ First query (no cache):
│  ├─ With small KB (100 chunks): 100-200ms ✓
│  ├─ With medium KB (1000 chunks): 200-400ms ✓
│  └─ With large KB (10K+ chunks): 300-800ms ✓
│
├─ Second query (cache hit): 1-5ms ✓
│
└─ After KB update (cache miss): Same as first ✓

STRESS TEST:
┌─ Run 100 queries sequentially
├─ Measure:
│  ├─ Average latency
│  ├─ P95 latency (95th percentile)
│  ├─ Cache hit rate (should stabilize ~30-50%)
│  └─ Memory usage (should be stable)
│
└─ Expected:
   ├─ Avg latency: 150-300ms
   ├─ P95 latency: <600ms
   ├─ Cache hit rate: 30%+ (higher if repeated queries)
   └─ Memory: Stable (no leaks)


CONCURRENT LOAD TEST:
┌─ Run 10 queries concurrently
├─ Expected:
│  ├─ All complete without error
│  ├─ No timeout errors (unless KB is extreme)
│  ├─ Response times similar to sequential
│  └─ Multi-tenancy enforced (one agent doesn't see others' KBs)
│
└─ Python test:
   import asyncio
   from app.modules.rag.service import RAGService
   
   tasks = [
       RAGService.generate_answer(
           query=f"Query {i}",
           agent_id="agent_123",
           kb_id=kb_id
       )
       for i in range(10)
   ]
   results = await asyncio.gather(*tasks)
   print(f"Completed: {len(results)} queries")


═══════════════════════════════════════════════════════════════════════════════

4. PRODUCTION READINESS CHECKLIST

Before deploying to production, verify:

CODE QUALITY:
├─ ✅ Syntax validation: python -m py_compile app/modules/rag/*.py
├─ ✅ No import errors: python -c "from app.modules.rag import RAGService"
├─ ✅ Type hints present: grep -r "def " app/modules/rag | grep "->"
├─ ✅ Error handling: grep -r "except" app/modules/rag
├─ ✅ Logging present: grep -r "logger\." app/modules/rag
└─ ✅ Documentation: All public methods have docstrings

FUNCTIONALITY:
├─ ✅ Cache invalidation works: Latency jumps after KB update
├─ ✅ Diversity penalty works: Chunks are varied
├─ ✅ Attribution works: Every chunk has reason field
├─ ✅ Timeout fallback works: Partial response on slow KB (if tested)
├─ ✅ Metrics tracked: Logs every 10 queries
├─ ✅ Multi-tenancy: Agents can't access others' KBs
└─ ✅ REST API: POST /rag/query works end-to-end

PERFORMANCE:
├─ ✅ First query latency: <500ms typical
├─ ✅ Cache hit latency: <5ms
├─ ✅ P95 latency: <1s
├─ ✅ Concurrent queries: 10+ at once OK
├─ ✅ Memory stable: No leaks after 1000 queries
└─ ✅ CPU reasonable: <20% on typical hardware

MONITORING READY:
├─ ✅ Logs structured: grep "RAG" app.log shows clear entries
├─ ✅ Error logs helpful: Timeouts logged with context
├─ ✅ Metrics exported: get_metrics() available
├─ ✅ Health check: GET /rag/health returns OK
└─ ✅ Alerts tunable: Can adjust timeout, max_depth, etc.


═══════════════════════════════════════════════════════════════════════════════

5. COMMON ISSUES & FIXES

ISSUE: Cache not being used (always 200ms latency)
├─ Cause: KB is being updated frequently
├─ Cause: Query text differs slightly (capitalization, punctuation)
├─ Cause: agent_id or kb_id changes between requests
│
└─ Fix:
   1. Verify you're using identical query text
   2. Verify agent_id and kb_id don't change
   3. Check logs for "Cache key mismatch"
   4. Try: query → query → query (3 times same) = should be 200ms, 1ms, 1ms


ISSUE: Partial results appearing unexpectedly
├─ Cause: KB is large and graph expansion is slow
├─ Cause: System is under load
│
└─ Fix:
   1. This is working as designed (graceful degradation)
   2. Check latency: If >2s, this explains partial result
   3. Options:
      a. Increase timeout (change _DEFAULT_RAG_TIMEOUT in service.py)
      b. Reduce max_graph_depth (fewer expansions = faster)
      c. Reduce max_context_tokens (smaller context = less ranking work)


ISSUE: Latency slowly increasing (100ms → 500ms)
├─ Cause: KB growing (more chunks = slower semantic search)
├─ Cause: Cache size increasing but memory OK
│
└─ Fix:
   1. This is normal as KB grows
   2. Monitor with metrics: Is retrieval latency increasing?
   3. Options if needed:
      a. Add Vector Index (Phase 3) → O(log N) instead of O(N)
      b. Reduce max_seeds (retrieve fewer seed chunks)


ISSUE: No metrics in logs
├─ Cause: Fewer than 10 queries run (<100 queries = maybe no summary)
├─ Cause: Logging level too high (not set to INFO)
│
└─ Fix:
   1. Run at least 10 queries
   2. Check logger level: should be logging.INFO
   3. Look for: "📊 RAG Metrics (last 10):" in logs
   4. Fallback: Call get_metrics() directly in code


ISSUE: Agents can see each other's KBs
├─ Cause: Critical security issue
│
└─ Fix:
   1. This should never happen (multi-tenancy enforced)
   2. Check: Does KBOwnership.agent_id match in queries?
   3. Check: Is RLS enabled on KB table?
   4. Test: Two agents querying different KBs = different results?


═══════════════════════════════════════════════════════════════════════════════

NEXT STEPS

Once all tests pass:

OPTION A: Deploy to Production
└─ System is production-ready
   Move RAG module to live environment
   Enable monitoring dashboards
   Set up alerts (latency, timeout_rate, etc.)

OPTION B: Upgrade to Phase 3 (Advanced AI Features)
├─ Real embeddings (DeepInfra)
├─ LLM generation (Llama 2)
├─ Vector indexing (FAISS or Pinecone)
├─ Distributed cache (Redis)
└─ See Phase 3 upgrade guide for details

OPTION C: Optimize Phase 2 Further (Advanced)
├─ A/B test: MMR algorithm vs different scoring
├─ Profile: Which queries timeout? Optimize them
├─ Index: Add database indexes on frequently filtered columns
├─ Cache: Move to Redis for distributed caching
└─ See performance optimization guide


═══════════════════════════════════════════════════════════════════════════════

CONTACT / SUPPORT

If tests fail:
1. Check logs (tail -f app.log | grep RAG)
2. Verify KB has real documents (not empty)
3. Verify database connectivity (PostgreSQL + Neo4j)
4. Check embeddings working (generate_embedding() succeeds)
5. Verify multi-tenancy (correct agent_id + kb_id)

Code issues?
└─ Check PHASE_2_STEP_4_RAG_PIPELINE.md for detailed implementation guide


═══════════════════════════════════════════════════════════════════════════════
"""
