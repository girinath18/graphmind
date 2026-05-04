# PHASE 3+ ENHANCEMENTS: STRIPE-LEVEL IDEMPOTENCY & ERROR CLASSIFICATION

**Status:** Architectural planning — implement after Phase 2 complete  
**Target Phase:** Phase 3 (Knowledge Base module)  
**Maturity Level:** Senior backend / Distributed systems  
**Date:** April 5, 2026  

---

## 🚀 ENHANCEMENT #1: Request-Level Idempotency Key

### Current State (Phase 2)

**Database-level idempotency:**
```python
# Agent model
UNIQUE(tenant_id, name) WHERE is_active = True

# Problem: Handles agent duplication, but not:
# - Multiple requests creating different agents
# - Network retries causing duplicate processing
# - Async operations with unknown state
```

### The Problem

```
Scenario: User creates 3 agents rapidly
├─ POST /agents {"name": "Agent1"} → ✅ Created
├─ Network timeout (user doesn't see response)
├─ User retries → Creates Agent1 again? ❌ (UNIQUE constraint prevents)
│  
└─ But creates Agent2 instead:
   POST /agents {"name": "Agent2"} → ✅ Created
   Network timeout (user doesn't see response)
   User retries → Creates Agent2 again? ❌ (UNIQUE constraint prevents)

❌ Result: 
   Server: [Agent1, Agent2]
   User: "Did my agent get created?"
   → Confusing UX
```

### The Stripe Solution: Idempotency-Key Header

**API Design:**
```http
POST /agents HTTP/1.1
Idempotency-Key: abc-123-def-456
Content-Type: application/json

{
  "name": "Research Agent",
  "system_prompt": "You are a researcher..."
}
```

**How It Works:**
```python
# Step 1: Check if we've seen this key before
idempotency_key = request.headers.get("Idempotency-Key")
cached_response = await idempotency_cache.get(
    f"{tenant_id}:{idempotency_key}"
)

if cached_response:
    # We've seen this before! Return cached response
    logger.info(f"Idempotent retry detected key: {idempotency_key}")
    return cached_response

# Step 2: Create agent
agent = await service.create_agent(user_id, request.body)

# Step 3: Store response in cache
await idempotency_cache.set(
    f"{tenant_id}:{idempotency_key}",
    {
        "agent_id": agent.id,
        "created_at": agent.created_at,
        "name": agent.name
    },
    ttl=24*3600  # 24 hours
)

return success(agent)
```

### Database Schema (Phase 3+)

```sql
-- Idempotency cache table
CREATE TABLE idempotency_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    idempotency_key VARCHAR(255) NOT NULL,
    request_path VARCHAR(255) NOT NULL,  -- /agents, /kbs, etc.
    request_method VARCHAR(10) NOT NULL,  -- POST, PUT, etc.
    response_body JSONB NOT NULL,         -- Cached response
    created_at TIMESTAMP DEFAULT now(),
    expires_at TIMESTAMP NOT NULL,
    
    -- Clean up after TTL
    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    UNIQUE(tenant_id, idempotency_key, request_path, request_method)
);

-- Cleanup job (runs hourly)
CREATE OR REPLACE FUNCTION cleanup_expired_idempotency_keys()
RETURNS void AS $$
BEGIN
    DELETE FROM idempotency_cache 
    WHERE expires_at < now();
END;
$$ LANGUAGE plpgsql;
```

### Implementation Pattern (Phase 3+)

**Middleware:**
```python
# app/middleware/idempotency.py

class IdempotencyMiddleware:
    """Detect and handle idempotent requests."""
    
    async def __call__(self, request: Request, call_next):
        # Only handle POST/PUT requests (create/update)
        if request.method not in ["POST", "PUT", "PATCH", "DELETE"]:
            return await call_next(request)
        
        idempotency_key = request.headers.get("Idempotency-Key")
        
        # If no key, allow bypass (backward compatibility)
        if not idempotency_key:
            return await call_next(request)
        
        tenant_id = request.state.tenant_id
        cache_key = f"{tenant_id}:{request.method}:{request.url.path}:{idempotency_key}"
        
        # Check cache
        cached = await redis.get(cache_key)
        if cached:
            logger.info(f"🔄 Idempotent retry: key={idempotency_key}")
            return Response(
                content=cached,
                status_code=200,
                media_type="application/json"
            )
        
        # Process request
        response = await call_next(request)
        
        # Cache successful responses
        if response.status_code in [200, 201]:
            await redis.setex(
                cache_key,
                24*3600,  # 24 hour TTL
                response.body.decode()
            )
        
        return response
```

### Benefits

```
WITHOUT Idempotency-Key:
├─ User: "Did my request go through?"
├─ Creates retries
├─ Network duplication possible
└─ Poor UX

WITH Idempotency-Key (Stripe-level):
├─ User: "Safe to retry, same result guaranteed"
├─ Client libraries auto-generate keys
├─ Network resilience maxed
└─ Professional SaaS UX
```

### Usage Example (Frontend)

```javascript
// Client side - auto-generates idempotency key
import { v4 as uuidv4 } from 'uuid';

async function createAgent(agentData) {
    const idempotencyKey = uuidv4();
    
    // Retry-safe: same key = same result
    while (retries < MAX_RETRIES) {
        try {
            const response = await fetch('/api/agents', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Idempotency-Key': idempotencyKey  // ⭐
                },
                body: JSON.stringify(agentData)
            });
            
            if (response.ok) {
                return response.json();
            }
        } catch (error) {
            retries++;
            await sleep(2 ** retries * 100);  // Exponential backoff
        }
    }
}
```

### Timeline

- **Phase 3:** Add idempotency middleware
- **Phase 3:** Create idempotency_cache table
- **Phase 3:** Implement Redis caching layer
- **Phase 4:** Client SDK with built-in idempotency-key generation

---

## 🎯 ENHANCEMENT #2: Error Classification & Retry Policy

### Current State (Phase 2)

```python
# app/core/neo4j_retry.py

try:
    return await operation()
except (TransientError, ServiceUnavailable):
    # ✅ Retry
    retry()
except Exception:
    # ❌ Fail fast
    raise
```

**Problem:** All non-transient errors treated the same way.

### The Problem

```
Scenario: Neo4j returns various errors

TransientError (network hiccup):
✅ Retry: Likely recovers on 2nd attempt

ServiceUnavailable (cluster rebalancing):
✅ Retry: Will come back online

ClientError (bad query syntax):
❌ Retrying wastes time (will always fail)
❌ Hides actual bug (should surface to developer)

AuthenticationError (wrong credentials):
❌ Retrying wastes time
❌ Hides security issue immediately

ConstraintError (duplicate key):
❌ Retrying pointless (constraint violation won't change)
❌ Should fail fast to alert developer
```

### The Better Way: Error Classification

**Enhanced Retry Handler (Phase 3+):**

```python
# app/core/error_classification.py

from enum import Enum

class RetryStrategy(str, Enum):
    """How to handle different error types."""
    
    RETRY = "retry"              # Attempt exponential backoff
    FAIL_FAST = "fail_fast"      # Immediately return error
    CIRCUIT_BREAK = "circuit_break"  # Track failures, stop retrying

class ErrorClassification(Enum):
    """Categorize errors for smart retry logic."""
    
    # ✅ TRANSIENT: Recoverable, safe to retry
    TRANSIENT = {
        "codes": [
            "ServiceUnavailable",
            "TransientError",
            "RequestTimedOut",
            "ConnectionLost",
        ],
        "strategy": RetryStrategy.RETRY,
        "max_retries": 3,
        "backoff": "exponential",
    }
    
    # ⚠️ DEGRADED: Service partially available, retry with caution
    DEGRADED = {
        "codes": [
            "SlowQuery",
            "HighLoad",
            "CacheDisabled",
        ],
        "strategy": RetryStrategy.RETRY,
        "max_retries": 1,  # Only retry once
        "backoff": "exponential",
    }
    
    # ❌ PERMANENT: Will never recover, fail immediately
    PERMANENT = {
        "codes": [
            "ValidationError",
            "AuthenticationError",
            "AuthorizationError",
            "ResourceNotFound",
            "SyntaxError",
            "ConstraintViolation",
        ],
        "strategy": RetryStrategy.FAIL_FAST,
        "max_retries": 0,
        "backoff": None,
    }
    
    # 🛑 CRITICAL: Retry with extreme caution (circuit breaker pattern)
    CRITICAL = {
        "codes": [
            "DatabaseDown",
            "ClusterUnreachable",
            "OutOfMemory",
        ],
        "strategy": RetryStrategy.CIRCUIT_BREAK,
        "max_retries": 2,
        "backoff": "exponential",
    }

def classify_error(error: Exception) -> ErrorClassification:
    """
    Classify neo4j error to determine retry strategy.
    
    Args:
        error: Neo4j exception
    
    Returns:
        ErrorClassification with retry strategy
    """
    error_type = type(error).__name__
    
    for classification in ErrorClassification:
        if error_type in classification.value["codes"]:
            return classification
    
    # Default: treat unknown as transient (safe default)
    return ErrorClassification.TRANSIENT
```

### Usage in Retry Handler

```python
# Enhanced app/core/neo4j_retry.py

async def retry_neo4j_operation(
    operation: Callable[[], Any],
    operation_name: str = "Neo4j operation",
) -> Any:
    """
    Execute Neo4j operation with smart error classification.
    
    Args:
        operation: Async callable to execute
        operation_name: Human description (for logging)
    
    Returns:
        Result of operation if successful
    
    Raises:
        Exception: If non-retryable or max retries exceeded
    """
    attempt = 0
    
    while True:
        try:
            result = await operation()
            if attempt > 0:
                logger.info(f"✅ {operation_name} succeeded after {attempt} retries")
            return result
            
        except Exception as error:
            # Classify the error
            classification = classify_error(error)
            strategy = classification.value["strategy"]
            max_retries = classification.value["max_retries"]
            backoff = classification.value["backoff"]
            
            logger.warning(
                f"⚠️ {operation_name} failed (attempt {attempt + 1}): "
                f"{type(error).__name__} - Classification: {classification.name}"
            )
            
            # Strategy 1: FAIL_FAST
            if strategy == RetryStrategy.FAIL_FAST:
                logger.error(f"❌ {operation_name} failed (non-retryable): {error}")
                raise
            
            # Strategy 2: RETRY with backoff
            if strategy == RetryStrategy.RETRY:
                if attempt < max_retries:
                    delay = calculate_delay(attempt, backoff_type=backoff)
                    logger.info(f"⏳ Retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                    attempt += 1
                    continue
                else:
                    logger.error(f"❌ {operation_name} failed after {max_retries} retries")
                    raise
            
            # Strategy 3: CIRCUIT_BREAK
            if strategy == RetryStrategy.CIRCUIT_BREAK:
                await circuit_breaker.record_failure(operation_name)
                if attempt < max_retries and not circuit_breaker.is_open(operation_name):
                    delay = calculate_delay(attempt, backoff_type=backoff)
                    await asyncio.sleep(delay)
                    attempt += 1
                    continue
                else:
                    logger.error(f"❌ {operation_name} circuit breaker OPEN")
                    raise CircuitBreakerOpenError(operation_name)
```

### Circuit Breaker Pattern (Phase 3+)

```python
# app/core/circuit_breaker.py

class CircuitBreaker:
    """
    Track failures and stop retrying when service is clearly down.
    
    States:
    - CLOSED: Normal operation (allow requests)
    - OPEN: Service down (fail fast, don't retry)
    - HALF_OPEN: Testing if service recovered
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold  # Open after 5 failures
        self.timeout = timeout  # Try again after 60 seconds
        self.failures = {}  # {operation_name: count}
        self.last_check_time = {}  # {operation_name: timestamp}
    
    def record_failure(self, operation_name: str):
        """Record a failure for an operation."""
        self.failures[operation_name] = self.failures.get(operation_name, 0) + 1
        logger.warning(
            f"Circuit breaker recorded failure: {operation_name} "
            f"({self.failures[operation_name]}/{self.failure_threshold})"
        )
    
    def record_success(self, operation_name: str):
        """Record a success, reset failure count."""
        if operation_name in self.failures:
            del self.failures[operation_name]
            logger.info(f"Circuit breaker RESET for: {operation_name}")
    
    def is_open(self, operation_name: str) -> bool:
        """Check if circuit is open (blocking requests)."""
        if self.failures.get(operation_name, 0) >= self.failure_threshold:
            # Check if timeout has passed (transition to HALF_OPEN)
            elapsed = time.time() - self.last_check_time.get(operation_name, 0)
            if elapsed < self.timeout:
                return True  # Still open
            else:
                # Timeout passed, try again (HALF_OPEN state)
                return False
        return False

circuit_breaker = CircuitBreaker()
```

### Error Classification in Service Layer

```python
# app/modules/agents/service.py

async def delete_agent(self, agent_id: str) -> dict:
    """Delete agent with smart error handling."""
    try:
        neo4j_repo = Neo4jRepository(str(self.tenant_id))
        
        # Delete with classification-aware retry
        try:
            await retry_neo4j_operation(
                lambda: neo4j_repo.execute_write(delete_query, {...}),
                operation_name=f"delete_agent({agent_id})"
            )
            circuit_breaker.record_success(f"delete_agent({agent_id})")
            logger.info(f"✅ Neo4j: Deleted agent {agent_id}")
            
        except CircuitBreakerOpenError:
            logger.error(f"❌ Circuit breaker OPEN - Neo4j appears to be down")
            # Alert operations team
            await send_alert(
                level="CRITICAL",
                service="neo4j",
                message="Circuit breaker opened - cluster may be down"
            )
            return error("Neo4j cluster unavailable")
        
        except Exception as error:
            classification = classify_error(error)
            logger.error(f"❌ Delete failed ({classification.name}): {error}")
            return error(f"Failed to delete agent: {error}")
        
        # Continue with PostgreSQL soft-delete...
        deleted = await self.repository.soft_delete(agent_id)
        if not deleted:
            return error(f"Agent not found: {agent_id}", status=404)
        
        await self.db.commit()
        return success({"id": agent_id})
```

### Benefits

```
WITHOUT Error Classification:
├─ All errors cause retries (wasted time/resources)
├─ Bugs hidden by retries (query syntax errors still pass)
└─ Hard to debug (when did it actually fail?)

WITH Error Classification + Circuit Breaker:
├─ ✅ Transient errors: Retry (recovers)
├─ ❌ Permanent errors: Fail fast (surfaces bugs)
├─ 🛑 Critical errors: Circuit break (prevents cascade failure)
└─ Professional-grade reliability
```

### Timeline

- **Phase 3:** Implement error classification
- **Phase 3:** Integrate into retry handler
- **Phase 3+:** Add circuit breaker pattern
- **Phase 4:** Add observability (track error rates by classification)

---

## 🎓 SYSTEM MATURITY PROGRESSION

### Current State (Phase 2)

```
Idempotency      : Database-level ✅
Retry Strategy   : Transient-aware ✅
Error Handling   : Basic (transient vs. other) ✅
Circuit Breaker  : Not needed yet ⏳
Request Keys     : Not needed yet ⏳
```

**Reliability:** 95% (good for startup phase)

### After Phase 3+ (With Both Enhancements)

```
Idempotency      : Request-level (Stripe-grade) ✅
Retry Strategy   : Error-classified ✅
Error Handling   : Permanent/transient/critical ✅
Circuit Breaker  : Prevents cascade failure ✅
Request Keys     : Full retryability ✅
```

**Reliability:** 99.5%+ (enterprise-grade)

---

## 📊 MATURITY ASSESSMENT

| Dimension | Current | Phase 3+ | Assessment |
|-----------|---------|----------|------------|
| **Backend Design** | Senior | Expert | Distributed systems patterns |
| **Distributed Systems** | Mid | Mid-Senior | Transaction safety, retry logic |
| **Multi-tenant SaaS** | Strong | Expert | Idempotency, error classification |
| **Graph RAG Readiness** | Strong | Strong | Neo4j integration solid |

---

## 🔄 DECISION MATRIX

| Enhancement | Complexity | Value | When | Priority |
|-------------|-----------|-------|------|----------|
| Idempotency-Key | Medium | High | Phase 3 | P1 |
| Error Classification | Medium | High | Phase 3 | P1 |
| Circuit Breaker | Medium | Medium | Phase 3+ | P2 |

**Decision:** Implement both in Phase 3 after KB module complete.

---

**Status:** Architecture designed, ready to implement ✅  
**Next Step:** Complete Phase 2 Step 3 (Knowledge Base module), then apply these patterns
