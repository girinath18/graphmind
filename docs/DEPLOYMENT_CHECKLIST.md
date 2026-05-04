# GraphMind MVP Deployment Checklist

**Date:** April 6, 2026  
**Version:** 1.0.0  
**Billing Status:** 🔴 DISABLED (MVP)  

---

## 📋 Pre-Deployment Checklist

### Code Quality
- [ ] All modules compile: `python -m py_compile app/**/*.py`
- [ ] Unit tests pass: `pytest tests/ -v`
- [ ] No linting errors: `pylint app/`
- [ ] Type hints valid: `mypy app/`
- [ ] Security scan: `bandit -r app/`

### Environment & Configuration
- [ ] `.env.production` created and filled
- [ ] All required environment variables set
- [ ] JWT_SECRET_KEY is 32+ characters
- [ ] CORS_ORIGINS set to specific domains (NOT "*")
- [ ] DATABASE_URL points to production database
- [ ] NEO4J_URI points to production graph database
- [ ] DEEPINFRA_API_KEY obtained and tested

### Database Setup
- [ ] PostgreSQL database created
- [ ] PostgreSQL user created with privileges
- [ ] Neo4j database running and accessible
- [ ] Database migrations applied: `alembic upgrade head`
- [ ] Tables created (check PostgreSQL schema)
- [ ] Neo4j constraints created (check graph schema)

### Infrastructure
- [ ] Production server deployed (cloud/on-prem)
- [ ] SSL/TLS certificates installed
- [ ] Firewall rules configured
- [ ] Load balancer configured (if needed)
- [ ] Reverse proxy configured (nginx/Apache)
- [ ] Error monitoring enabled (Sentry/similar)
- [ ] Log aggregation configured (ELK/similar)

### API Endpoints
- [ ] `GET /health` responds with 200 OK
- [ ] `POST /api/v1/rag/query` works end-to-end
- [ ] `POST /api/v1/auth/register` works
- [ ] `POST /api/v1/auth/login` works
- [ ] All error handlers return proper JSON
- [ ] Rate limiting works (test with many requests)
- [ ] CORS headers present in responses

### Security
- [ ] API keys not logged anywhere
- [ ] Sensitive data encrypted (connection strings, etc.)
- [ ] HTTPS enforced (redirect HTTP → HTTPS)
- [ ] CORS properly restricted
- [ ] JWT secret stored securely (not in code)
- [ ] Database passwords in environment variables only
- [ ] SSH keys configured for deployment server
- [ ] Firewall blocks unnecessary ports

### Performance
- [ ] Response latency < 2 seconds for queries
- [ ] Database queries use proper indexes
- [ ] Caching working (Redis or in-memory)
- [ ] Embedding cache operational
- [ ] Vector search taking < 100ms for seed retrieval
- [ ] LLM API calls completing < 15 seconds

### Monitoring & Logging
- [ ] Log rotation configured
- [ ] Logs written to persistent storage
- [ ] Error rate monitored
- [ ] Latency metrics collected
- [ ] Alert thresholds configured
- [ ] Dashboard created for metrics
- [ ] Backup system configured

### Feature Flags Status
- [ ] `USE_REAL_EMBEDDINGS = False` ✅
- [ ] `USE_LLM_ENTITY_EXTRACTION = False` ✅
- [ ] `ENABLE_BILLING = False` ✅ (MVP: No billing)

---

## 🚀 Deployment Steps

### Step 1: Final Verification
```bash
# Compile all Python modules
python -m py_compile app/core/*.py app/modules/**/*.py

# Run functional tests
pytest tests/integration/test_rag_pipeline.py -v

# Check configuration
python app/core/config.py  # Verify settings load
```

### Step 2: Database Migration
```bash
# Apply all pending migrations
alembic upgrade head

# Verify tables created
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB \
  -c "\dt"  # List tables

# Verify Neo4j constraints
cypher "CALL db.constraints()"
```

### Step 3: Deploy Application
```bash
# Option A: Docker
docker build -t graphmind:1.0.0 .
docker run -d \
  --name graphmind-api \
  --env-file .env.production \
  -p 8000:8000 \
  graphmind:1.0.0

# Option B: Direct deployment
source venv/bin/activate
pip install -r requirements.txt
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /var/log/graphmind/access.log \
  --error-logfile /var/log/graphmind/error.log
```

### Step 4: Health Checks
```bash
# Check API is running
curl -X GET http://localhost:8000/health

# Expected response:
# {"status": "ok", "timestamp": "2026-04-06T12:00:00Z"}

# Test authentication
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "secure123!"}'

# Test RAG query
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is GraphMind?",
    "kb_id": "<KNOWLEDGE_BASE_ID>",
    "agent_id": "<AGENT_ID>"
  }'
```

### Step 5: Monitor First Hour
```bash
# Watch logs in real-time
tail -f /var/log/graphmind/error.log

# Check for errors
grep ERROR /var/log/graphmind/error.log

# Monitor performance
curl -X GET http://localhost:8000/metrics
```

---

## 📊 Success Criteria

### Health Checks
- ✅ `/health` endpoint responds 200 OK
- ✅ All database connections successful
- ✅ Graph database accessible
- ✅ DeepInfra API integration working

### Query Performance
- ✅ First query: < 3 seconds (cold cache)
- ✅ Subsequent queries: < 1 second (cached)
- ✅ Cache hit rate: > 70% for repeated queries
- ✅ Error rate: < 0.1%

### Coverage
- ✅ Embeddings: Seed retrieval working
- ✅ Graph expansion: Entity linking working
- ✅ LLM fallback: Template answer generation working
- ✅ Multi-tenancy: Proper tenant isolation

---

## 🔴 Rollback Plan

If issues occur:

```bash
# Emergency: Disable new LLM feature
ENABLE_LLM_GENERATION=False (not implemented yet)

# Emergency: Disable graph expansion
USE_GRAPH_EXPANSION=False (fall back to seed chunks only)

# Emergency: Disable real embeddings
USE_REAL_EMBEDDINGS=False (use hash-based fallback)

# Last resort: Revert to previous version
git checkout main~1
# ... redeploy
```

---

## 💡 Post-Launch Monitoring (First Week)

### Daily Checklist
- [ ] Error rate stable (< 0.5%)
- [ ] Latency stable (avg < 2 seconds)
- [ ] No database connection errors
- [ ] Cache hit rate healthy
- [ ] No security warnings in logs

### Weekly Review
- [ ] Aggregate metrics dashboard
- [ ] Customer feedback collected
- [ ] Performance trends analyzed
- [ ] Plan any fixes/improvements

---

## 🎯 Next: Enable Billing (When Ready)

After MVP runs successfully for 1-2 weeks:

```bash
# Change in .env.production
ENABLE_BILLING=True

# Redeploy
# Now tracking per-tenant costs
# Can start invoicing
```

---

## 📞 Support Resources

- **Documentation:** Check [README.md](../README.md)
- **Troubleshooting:** Check logs in `/var/log/graphmind/`
- **Emergency:** Contact DevOps team
- **Metrics:** Check production dashboard
- **Alerts:** Set up monitoring thresholds

---

**Status:** 🟢 Ready for MVP Deployment  
**Last Updated:** April 6, 2026  
**Version:** 1.0.0
