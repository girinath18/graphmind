# GraphMind MVP Deployment - Quick Start Guide

**Status:** 🟢 Ready for Production  
**Billing:** 🔴 Disabled (MVP)  
**Date:** April 6, 2026  

---

## 5-Minute Deployment Overview

```
┌─────────────────────────────────────────────────────┐
│  GraphMind MVP Architecture (Billing Disabled)     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Client/Frontend                                   │
│         ↓                                           │
│  API Server (Port 8000)                           │
│    ├─ Auth (JWT)                                  │
│    ├─ RAG Pipeline                                │
│    │  ├─ Vector Search (embeddings)               │
│    │  ├─ Graph Expansion (Neo4j)                  │
│    │  └─ LLM Generation (DeepInfra)               │
│    └─ Cache (5-min TTL)                           │
│         ↓                                           │
│  Database Tier                                     │
│    ├─ PostgreSQL (knowledge bases, chunks)        │
│    └─ Neo4j (entity graph)                        │
│                                                     │
│  External Services                                 │
│    ├─ DeepInfra (LLM)                            │
│    └─ (Billing: DISABLED for MVP)                │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## System Requirements

| Component | Requirement | Notes |
|-----------|-------------|-------|
| **Python** | 3.9+ | Tested on 3.11 |
| **PostgreSQL** | 13+ | For KB storage |
| **Neo4j** | 5.0+ | For entity graph |
| **Memory** | 4GB+ | 8GB recommended |
| **CPU** | 2+ cores | 4+ cores recommended |
| **Disk** | 10GB+ | For databases |
| **Network** | 50Mbps+ | For DeepInfra API calls |

---

## Pre-Deployment Checklist (5 minutes)

```bash
# ✅ 1. Verify all code compiles
python -m py_compile app/core/*.py app/modules/**/*.py
# Expected: No errors

# ✅ 2. Check environment variables
cat .env.production | grep -E "^[^#]" | wc -l
# Expected: 25+ variables

# ✅ 3. Verify database access
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1"
# Expected: Returns 1

# ✅ 4. Verify Neo4j access
cypher "CALL db.constraints()" @ http://$NEO4J_URI
# Expected: Returns constraints list

# ✅ 5. Test DeepInfra API
curl -s -H "Authorization: Bearer $DEEPINFRA_API_KEY" \
  https://api.deepinfra.com/v1/openai/embeddings \
  -d '{"model":"qwen3-embedd-0.4B","input":"test"}' | jq .data[0].embedding | head -1
# Expected: Number (first embedding value)
```

---

## Deployment (Docker Recommended)

### Option A: Docker (Recommended for Production)

```bash
# 1. Build image
docker build -t graphmind:1.0.0 \
  --build-arg PYTHON_VERSION=3.11 \
  .

# 2. Create .env.production from template
cp .env.production.example .env.production
# Edit .env.production with your values

# 3. Start container
docker run -d \
  --name graphmind-api \
  --restart always \
  --env-file .env.production \
  -p 8000:8000 \
  -v /var/log/graphmind:/app/logs \
  graphmind:1.0.0

# 4. Verify startup
docker logs -f graphmind-api
# Wait for: "Uvicorn running on 0.0.0.0:8000"

# 5. Health check
curl -X GET http://localhost:8000/health
# Expected: {"status": "ok"}
```

### Option B: Direct Deployment (Linux/macOS)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/graphmind.git
cd graphmind

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
cp .env.production.example .env.production
# Edit .env.production with your values

# 5. Run migrations
alembic upgrade head

# 6. Start server
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /var/log/graphmind/access.log \
  --error-logfile /var/log/graphmind/error.log \
  --log-level info

# 7. In another terminal, verify:
curl -X GET http://localhost:8000/health
```

---

## Post-Deployment Verification (5 minutes)

```bash
# ✅ Step 1: Health Check
curl -X GET http://localhost:8000/health
# Expected: {"status": "ok", "timestamp": "2026-04-06T12:00:00Z"}

# ✅ Step 2: Auth Test
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "first_name": "Test",
    "last_name": "User"
  }')
echo $RESPONSE | jq .

TOKEN=$(echo $RESPONSE | jq -r .access_token)
echo "Token: $TOKEN"

# ✅ Step 3: Query Test (requires KB setup)
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is this knowledge base about?",
    "kb_id": "<YOUR_KB_ID>",
    "agent_id": "<YOUR_AGENT_ID>"
  }' | jq .

# ✅ Step 4: Check Logs
tail -100 /var/log/graphmind/error.log
# Expected: No ERROR or CRITICAL messages

# ✅ Step 5: Monitor Performance
curl -X GET http://localhost:8000/metrics | jq .
# Expected: API latency, error rate, cache hit rate
```

---

## First Day Operations

### Morning Checklist
```bash
# 1. Check API is online
curl http://localhost:8000/health

# 2. Monitor error logs (no critical errors expected)
grep CRITICAL /var/log/graphmind/error.log | wc -l
# Expected: 0

# 3. Check database connections
curl http://localhost:8000/metrics | jq '.database.connections'

# 4. Monitor latency (should be < 2 seconds)
curl http://localhost:8000/metrics | jq '.api.response_time_ms | average'
```

### Throughout the Day
- Monitor error rate (target: < 0.1%)
- Watch latency trends (target: avg < 2s)
- Check cache hit rate (target: > 70%)
- Verify all tenant queries working

### End of Day Report
- Total queries processed
- Error count (target: < 5 errors)
- Average response time
- Cache effectiveness
- No security warnings

---

## Troubleshooting

### API won't start
```bash
# Check error log
docker logs graphmind-api

# Common issues:
# 1. DATABASE_URL not set: Check .env.production
# 2. Port 8000 in use: Use different port or kill process
# 3. Memory too low: Increase container memory
```

### Slow queries (> 2 seconds)
```bash
# Check database indexing
psql -d graphmind_prod -c "\d+ chunks" # View indexes

# Check cache stats
curl http://localhost:8000/metrics | jq '.cache'

# Check graph expansion depth
# See rag/service.py line ~85: max_depth default is 2
```

### High error rate
```bash
# Check recent errors
grep ERROR /var/log/graphmind/error.log | tail -20

# Common issues:
# 1. DeepInfra API key invalid
# 2. Neo4j connection lost
# 3. PostgreSQL connection pool exhausted
```

### Database connection fails
```bash
# Test PostgreSQL
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1"

# Test Neo4j
cypher "RETURN 1" @ $NEO4J_URI

# Restart connections
# Set: POSTGRES_POOL_SIZE = 50 in .env
```

---

## Scaling (If Needed)

### When to scale
- Response time > 2 seconds consistently
- Error rate > 1%
- Database CPU > 80%

### How to scale
```bash
# Horizontal: Add more API servers behind load balancer
# Update health check: GET /health should return 200 OK

# Vertical: Increase resources
docker run -d \
  --memory 8gb \
  --cpus 4 \
  # ... other args
  graphmind:1.0.0

# Database: Increase pool sizes
POSTGRES_POOL_SIZE=50
NEO4J_POOL_SIZE=50
```

---

## Feature Flags Status

| Feature | Status | Change To Enable |
|---------|--------|-----------------|
| Real Embeddings | 🔴 OFF | `USE_REAL_EMBEDDINGS=True` |
| LLM Entity Extraction | 🔴 OFF | `USE_LLM_ENTITY_EXTRACTION=True` |
| **Billing** | 🔴 OFF | `ENABLE_BILLING=True` (later) |

---

## Next: Enable Billing (1-2 Weeks Later)

When MVP is stable:

```bash
# Edit .env.production
ENABLE_BILLING=True

# Redeploy
docker pull graphmind:1.0.0
docker stop graphmind-api
docker run -d \
  --name graphmind-api \
  --restart always \
  --env-file .env.production \
  -p 8000:8000 \
  graphmind:1.0.0

# Now tracking costs per tenant
# Use: GET /admin/billing/metrics
```

---

## Support

- **Logs:** `/var/log/graphmind/`
- **Metrics:** `GET http://localhost:8000/metrics`
- **Health:** `GET http://localhost:8000/health`
- **Documentation:** See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)

---

**🟢 Ready to Deploy!**
