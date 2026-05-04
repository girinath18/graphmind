# GraphMind Testing Console - Quick Reference

## Quick Commands

```bash
# Install dependencies
pip install -r requirements-streamlit.txt

# Start backend (Terminal 1)
cd v:\graphmind
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start console (Terminal 2)
cd v:\graphmind
streamlit run streamlit_console.py
```

Console opens at: http://localhost:8501

---

## 5-Minute Flow

```
1. Signup (30s)
   Email: test@example.com
   Password: testpass123
   Name: Test User

2. Create Agent (30s)
   Name: Support Bot
   Desc: Customer support
   Prompt: You are helpful

3. Create KB (30s)
   Name: Docs
   Desc: Documentation

4. Upload Text (30s)
   Paste: "Product features: chat, analytics, reports"

5. Query (2min)
   Question: "What features do you offer?"
   View: Answer, Sources, Stats, Cost
```

---

## Key Buttons

| Location | Button | Action |
|----------|--------|--------|
| Sidebar | 🔓 Login | Login with email/password |
| Sidebar | 📝 Signup | Create new account |
| Sidebar | 🚪 Logout | Logout user |
| Agents | ➕ Create Agent | Create new agent |
| Agents | Select dropdown | Choose active agent |
| KB | ➕ Create KB | Create knowledge base |
| KB | 📤 Upload | Upload text to KB |
| Query | 🚀 Ask | Execute query |
| Debug | (Auto display) | View session state |

---

## API Responses (Examples)

### Login Success
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user_id": "550e8400-e29b",
  "email": "test@example.com"
}
```

### Query Success
```json
{
  "answer": "Based on the docs...",
  "sources": [
    {
      "reason": "Chunk about features",
      "score": 0.92,
      "position": 1
    }
  ],
  "stats": {
    "llm_tokens": 124,
    "total_chunks": 3,
    "llm_source": "deepinfra",
    "prompt_version": "v1",
    "llm_cost_estimate": 0.000023
  }
}
```

---

## Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | ✅ Success | Continue |
| 201 | ✅ Created | Item created successfully |
| 400 | ❌ Bad Request | Check input format |
| 401 | ❌ Unauthorized | Login first |
| 404 | ❌ Not Found | Agent/KB not found |
| 500 | ❌ Server Error | Check backend logs |

---

## Common Errors & Fixes

### "API connection failed"
```bash
# Check backend is running
curl http://localhost:8000/health

# If fails, start backend:
uvicorn app.main:app --reload
```

### "Unauthorized" (401)
```
→ You're logged out
→ Click "Login" in sidebar
→ Use your email/password
```

### "Not Found" (404)
```
→ Agent/KB doesn't exist
→ Create one in Agents or KB tabs
→ Refresh list with dropdown
```

### "Bad Request" (400)
```
→ Missing required fields
→ Fill all fields in forms
→ No special characters in names
```

---

## Features Table

| Feature | Status | Location |
|---------|--------|----------|
| Signup | ✅ | Sidebar |
| Login | ✅ | Sidebar |
| Create Agent | ✅ | Agents tab |
| List Agents | ✅ | Agents tab |
| Select Agent | ✅ | Agents tab |
| Create KB | ✅ | KB tab |
| Upload Text | ✅ | KB tab |
| Query RAG | ✅ | Query tab |
| View Answer | ✅ | Query tab |
| View Sources | ✅ | Query tab |
| View Stats | ✅ | Query tab |
| Query History | ✅ | Analytics tab |
| Metrics | ✅ | Analytics tab |
| Billing | ✅ (conditional) | Billing tab |
| Debug | ✅ | Debug tab |

---

## Session State Persistence

Stored across UI refreshes (until browser closed):
- JWT token
- User email
- Selected agent ID
- API URL
- Query history

Cleared on:
- Logout click
- Browser tab close
- Streamlit hot reload

---

## Testing Scenarios

### Basic Authentication
```
1. Signup with new email
2. Verify logged in immediately
3. Logout
4. Login with same credentials
5. Verify token attached to requests
```

### Agent Management
```
1. Create 2 agents with different names
2. List agents - verify both appear
3. Select agent 1
4. Create KB for agent 1
5. Select agent 2
6. Create KB for agent 2 (should be different KBs)
```

### KB & Retrieval
```
1. Create KB "TestDocs"
2. Upload: "Product A has features X, Y, Z"
3. Query: "What features does Product A have?"
4. Verify answer mentions X, Y, Z
5. Check Sources - should show uploaded chunk
```

### Multi-Tenant Isolation
```
1. Signup as User1, create Agent1
2. Logout
3. Signup as User2, create Agent2
4. Logout, login as User1
5. Verify only Agent1 visible
6. Login as User2
7. Verify only Agent2 visible
```

### Billing Tracking
```
1. Ensure ENABLE_BILLING=True in .env
2. Run 5 queries
3. Check Billing tab:
   - Cost should be > $0
   - API calls should = 5
   - Tokens should be > 0
```

---

## Performance Monitoring

### Check Latency
1. Run query
2. Go to **Analytics** tab
3. "Avg Latency" shows average response time
4. Goal: < 2000ms per query

### Check Cache
```bash
# In backend logs, look for:
"Cache hit: True"  → Cache working ✅
"Cache hit: False" → Cache miss (normal first time)
```

### Check Tokens
```
Query tab → Stats expander → "Tokens"
Typical: 100-500 tokens per query
Cost: tokens × $price per token
```

---

## Keyboard Shortcuts (Streamlit)

| Key | Action |
|-----|--------|
| `R` | Rerun script |
| `C` | Clear cache |
| `S` | Settings |

---

## File Locations

```
v:\graphmind\
├── streamlit_console.py          # Main app (THIS FILE)
├── requirements-streamlit.txt    # Dependencies
├── STREAMLIT_CONSOLE.md          # Full documentation
├── .streamlit/
│   └── config.toml              # Streamlit config
└── app/
    ├── main.py                  # FastAPI app
    ├── core/
    │   ├── config.py           # Settings
    │   └── llm/
    │       └── deepinfra_llm.py # LLM service
    ├── modules/
    │   ├── auth/               # Auth endpoints
    │   └── rag/                # RAG endpoints
    └── ...
```

---

## Pro Tips

1. **Multi-Query Testing**: Keep Analytics tab open while querying to watch latency trend
2. **Debug Session**: Click Debug tab to see exact token in use
3. **API Inspection**: Network tab in browser shows all requests/responses
4. **Copy/Paste**: Use test data from previous queries
5. **Long Uploads**: For large KB, you can paste multiple times to same KB
6. **Error Details**: When test fails, check backend logs + console error message

---

## Integration Test Checklist

- [ ] Signup works
- [ ] Login works
- [ ] Create agent works
- [ ] Select agent persists
- [ ] Create KB works
- [ ] Upload text works
- [ ] Query returns answer
- [ ] Sources show chunks
- [ ] Stats show metrics
- [ ] Latency is reasonable (<2s)
- [ ] Query history tracks
- [ ] Billing shows (if enabled)
- [ ] Logout clears token
- [ ] Re-login works

---

## Port Configuration

| Service | Port | URL |
|---------|------|-----|
| FastAPI Backend | 8000 | http://localhost:8000 |
| Streamlit UI | 8501 | http://localhost:8501 |
| Postgres | 5432 | localhost:5432 |
| Neo4j | 7687 | localhost:7687 |

---

**Last Updated**: April 2026
**Version**: 1.0.0
**Status**: Production Ready ✅
