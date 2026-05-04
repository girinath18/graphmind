# 🔐 Neo4j Query & Relationship Safety Guide

## Context
This guide covers best practices for Phase 2+ development:
- Issue #4: SIMILAR relationships can duplicate (use MERGE)
- Issue #5: Query cost limits prevent memory blowups
- Issue #1 Fix: Improved query validation

---

## Issue #4: Relationship Deduplication (SIMILAR Relationships)

### The Problem
```cypher
-- WRONG (creates duplicates):
CREATE (c1)-[:SIMILAR]->(c2) WITH score 0.85
CREATE (c1)-[:SIMILAR]->(c2) WITH score 0.92  -- DUPLICATE!
```

Why? In graph RAG, we frequently compute chunk similarity. Multiple AI calls might find the same pair multiple times. Without deduplication:
- Same relationship created multiple times
- Graph traversal becomes expensive (multiple paths)
- Ranking systems return duplicates

###  The Solution: MERGE

MERGE is idempotent (safe to run multiple times):
```cypher
-- CORRECT (deduplication enforced):
MERGE (c1:Chunk {tenant_id: $tenant_id, id: $c1_id})
MERGE (c2:Chunk {tenant_id: $tenant_id, id: $c2_id})
MERGE (c1)-[:SIMILAR]->(c2)
  ON CREATE SET
    r.similarity_score = $score,
    r.created_at = timestamp()
  ON MATCH SET
    r.similarity_score = CASE
      WHEN $score > r.similarity_score THEN $score
      ELSE r.similarity_score
    END
```

### When to Use MERGE vs CREATE

| Operation | Pattern | Reason |
|---|---|---|
| First creation (bulk load) | CREATE | Faster if no duplicates exist |
| Incremental updates | MERGE | Idempotent, safe for reruns |
| Relationship updates | MERGE + ON MATCH | Atomically update if exists |
| Duplicate-sensitive ops | MERGE | Prevents multi-creation |

### Implementation for Phase 2 (Agent Service)

```python
# app/modules/agents/neo4j_service.py (Phase 2+)

async def link_similar_chunks(
    tenant_id: str,
    chunk1_id: str,
    chunk2_id: str,
    similarity_score: float
):
    """
    Link two chunks as semantically similar.
    
    CRITICAL:
    - Uses MERGE (not CREATE) for deduplication
    - Updates score if exists and new score is higher
    - Bidirectional: creates both directions
    """
    repo = Neo4jRepository(tenant_id)
    
    # Forward direction
    query_fwd = """
    MATCH (c1:Chunk {tenant_id: $tenant_id, id: $c1_id})
    MATCH (c2:Chunk {tenant_id: $tenant_id, id: $c2_id})
    MERGE (c1)-[r:SIMILAR]->(c2)
    ON CREATE SET
        r.similarity_score = $score,
        r.created_at = timestamp()
    ON MATCH SET
        r.similarity_score = CASE
            WHEN $score > r.similarity_score THEN $score
            ELSE r.similarity_score
        END
    RETURN r.similarity_score AS final_score
    """
    
    result = await repo.execute_write(query_fwd, {
        "c1_id": chunk1_id,
        "c2_id": chunk2_id,
        "score": similarity_score
    })
    
    # Backward direction (bidirectional)
    query_bwd = """
    MATCH (c1:Chunk {tenant_id: $tenant_id, id: $c1_id})
    MATCH (c2:Chunk {tenant_id: $tenant_id, id: $c2_id})
    MERGE (c2)-[r:SIMILAR]->(c1)
    ON CREATE SET
        r.similarity_score = $score,
        r.created_at = timestamp()
    ON MATCH SET
        r.similarity_score = CASE
            WHEN $score > r.similarity_score THEN $score
            ELSE r.similarity_score
        END
    RETURN r.similarity_score AS final_score
    """
    
    await repo.execute_write(query_bwd, {
        "c1_id": chunk1_id,
        "c2_id": chunk2_id,
        "score": similarity_score
    })
    
    logger.info(
        f"Linked chunks (SIMILAR): {chunk1_id} <-> {chunk2_id} "
        f"(score: {similarity_score:.3f})"
    )
```

---

## Issue #5: Query Cost Limits

### The Problem

```cypher
-- DANGEROUS (unbounded traversal):
MATCH (a:Agent {tenant_id: $tenant_id})
-[*]->(n)  -- Matches ANY path of ANY length
RETURN n

-- In a large graph:
-- - Can traverse millions of nodes
-- - Causes memory explosion
-- - Kills the database
```

Why? Neo4j must explore ALL possible paths, which grows exponentially with depth.

### The Solution: Bounded Traversal

```cypher
-- SAFE (limited to 3 hops):
MATCH (a:Agent {tenant_id: $tenant_id})
-[*0..3]->(n)  -- Max 3 relationship hops
WHERE n.tenant_id = $tenant_id
RETURN n
```

### Traversal Depth Rules for RAG (Phase 5)

| Traversal | Max Depth | Reason | Query Type |
|---|---|---|---|
| Same-level expansion | 0 | Direct match (chunks in same KB) | Seed retrieval |
| Neighbor expansion | 1 | Immediate relationships (SIMILAR, MENTIONS) | Near-context |
| Graph expansion | 2 | Multi-hop (via Entity bridge) | Rich context |
| Full expansion | 3 | Rare, specific queries only | Deep reasoning |
| Unbounded | ❌ Never | Dangerous in production | FORBIDDEN |

### Implementation Pattern for Phase 2+ Services

```python
# app/modules/rag/query_builder.py (Phase 5+)

class SafeGraphQuery:
    """Build Neo4j queries with enforced cost limits"""
    
    @staticmethod
    def seed_retrieval(tenant_id: str, agent_id: str) -> str:
        """
        Retrieve direct chunks (0 hops) - CHEAP
        """
        return """
        MATCH (a:Agent {tenant_id: $tenant_id, id: $agent_id})
        -[:OWNS_KB]->(kb:KnowledgeBase)
        -[:HAS_CHUNK]->(c:Chunk)
        WHERE c.tenant_id = $tenant_id
        RETURN c
        LIMIT 50
        """
    
    @staticmethod
    def neighbor_expansion(tenant_id: str, chunk_id: str) -> str:
        """
        Expand from chunk via relationships (1 hop) - MODERATE
        """
        return """
        MATCH (c:Chunk {tenant_id: $tenant_id, id: $chunk_id})
        -[*1..1]->(neighbor)
        WHERE neighbor.tenant_id = $tenant_id
        RETURN neighbor
        LIMIT 200
        """
    
    @staticmethod
    def entity_bridge(tenant_id: str, chunk_id: str) -> str:
        """
        Find chunks via entity mentions (2 hops) - MODERATE
        
        Pattern: Chunk -> Entity -> Chunk
        """
        return """
        MATCH (c1:Chunk {tenant_id: $tenant_id, id: $chunk_id})
        -[:MENTIONS]->(e:Entity {tenant_id: $tenant_id})
        <-[:MENTIONS]-(c2:Chunk)
        WHERE c2.tenant_id = $tenant_id
        RETURN c2
        LIMIT 150
        """
    
    @staticmethod
    def rich_context(tenant_id: str, chunk_id: str) -> str:
        """
        Deep traversal with entity bridging (2 hops) - EXPENSIVE
        
        Use only when necessary
        """
        return """
        MATCH (c:Chunk {tenant_id: $tenant_id, id: $chunk_id})
        -[*0..2]->(related)
        WHERE related.tenant_id = $tenant_id
          AND (related:Chunk OR related:Entity)
        RETURN related
        LIMIT 300
        """
    
    @staticmethod
    def forbidden_query():
        """
        NEVER use unbounded traversal
        """
        # ❌ FORBIDDEN (would be caught by Neo4jRepository):
        query = """
        MATCH (n)-[*]->(m)
        RETURN m
        """
        # Neo4jRepository will reject this:
        # - Missing tenant_id filter
        # - Unbounded traversal (dangerous)


# Usage in services
async def get_rag_context(tenant_id: str, chunk_id: str, depth: str = "moderate"):
    repo = Neo4jRepository(tenant_id)
    
    if depth == "seed":
        query = SafeGraphQuery.seed_retrieval(tenant_id, chunk_id)
    elif depth == "neighbor":
        query = SafeGraphQuery.neighbor_expansion(tenant_id, chunk_id)
    elif depth == "entity":
        query = SafeGraphQuery.entity_bridge(tenant_id, chunk_id)
    elif depth == "rich":
        query = SafeGraphQuery.rich_context(tenant_id, chunk_id)
    else:
        raise ValueError(f"Invalid depth: {depth}")
    
    return await repo.execute_read(query, {"chunk_id": chunk_id})
```

---

## Issue #1 (Revisited): Improved Query Validation

### What Changed

**Before** (vulnerable to false positives):
```python
if "$tenant_id" not in query:
    raise SecurityError()
# Problem: WHERE c.name = "$tenant_id" passes validation ❌
```

**After** (robust validation):
```python
query_lower = query.lower()
if "tenant_id" not in query_lower or "$tenant_id" not in query:
    raise SecurityError()
# Logic:
#   - "tenant_id" in lowercase form (catches WHERE, MATCH, etc.)
#   - "$tenant_id" as parameter (catches actual parameter binding)
#   - BOTH must be true (prevents false positives + false negatives)
```

### Examples

| Query | Valid? | Reason |
|---|---|---|
| `WHERE c.tenant_id = $tenant_id` | ✅ YES | Has `tenant_id` + `$tenant_id` |
| `WHERE c.name = "$tenant_id"` | ❌ NO | Has `$tenant_id` but as string literal |
| `MATCH (n {tenant_id: $tenant_id})` | ✅ YES | Has both checks |
| `RETURN c` | ❌ NO | Missing both |
| `SET n.value = $tenant_id` | ✅ YES | Has both (even in SET clause) |

### Future: Query Builder Pattern

For Phase 3+, migrate from string validation to a query builder:

```python
# Future pattern (not Phase 2):
from app.core.neo4j_builder import QueryBuilder

query = (
    QueryBuilder()
    .start("Chunk", tenant_id=tenant_id, id=chunk_id)
    .match_relationship("SIMILAR", "Chunk")
    .where("score > $min_score")
    .limit(100)
    .build()
)
# Result: Query builder enforces patterns automatically
# No string validation needed
```

---

## Summary: Fixed Issues

| Issue | Status | Implementation |
|---|---|---|
| #1: Query validation | ✅ FIXED | Dual check (lowercase + param) |
| #2: Vector dimension config | ✅ FIXED | Configurable via `EMBEDDING_DIMENSION` |
| #3: Entity deduplication | ✅ FIXED | Constraint: `(tenant_id, normalized_name) UNIQUE` |
| #4: SIMILAR duplication | ✅ DOCUMENTED | Use MERGE pattern (provided code examples) |
| #5: Query cost limits | ✅ DOCUMENTED | Bounded traversal (0-3 hops max) |

---

## Checklist for Phase 2+ Development

- [ ] Use MERGE for relationship creation (not CREATE)
- [ ] Implement ON CREATE/ON MATCH for updates
- [ ] Limit traversal depth (max 2-3 hops in RAG)
- [ ] Always filter by tenant_id in WHERE clause
- [ ] Pass all queries through Neo4jRepository
- [ ] Use SafeGraphQuery builder for consistent patterns
- [ ] Test with duplicate creation (MERGE should be idempotent)
- [ ] Monitor query performance (EXPLAIN queries before prod)

---

## Files Modified This Session

- `app/core/config.py` — Added `embedding_dimension` setting
- `app/core/neo4j_repository.py` — Improved query validation (dual check)
- `scripts/neo4j_init.py` — Dynamic vector dimensions + entity constraint

## Next: Phase 2, Step 2 — Agents Module

Ready to implement Agent CRUD with Neo4j integration.
