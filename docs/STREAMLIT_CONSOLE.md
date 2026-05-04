# GraphMind Streamlit Testing Console

A functional testing UI for the GraphMind multi-tenant RAG system. Build real-world API flows without worrying about UI design.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements-streamlit.txt
```

### 2. Start the Backend (if not already running)

```bash
# From GraphMind root directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Run the Testing Console

```bash
streamlit run streamlit_console.py
```

The UI will open at `http://localhost:8501`

### 4. Configure API URL (if needed)

By default, the console connects to `http://localhost:8000`. You can change this in the **Settings** panel on the sidebar.

---

## Complete Testing Flow

### Step 1: Sign Up
1. Go to **Signup** tab
2. Fill in: email, password, first name, last name
3. Click **Signup**
4. You'll be logged in automatically

### Step 2: Create an Agent
1. Click on **Agents** tab
2. Go to **Create** sub-tab
3. Fill in:
   - **Agent Name**: e.g., "Customer Support Bot"
   - **Description**: e.g., "Answers customer questions"
   - **System Prompt**: e.g., "You are a helpful customer support assistant"
4. Click **Create Agent**

### Step 3: Select the Agent
1. Stay in **Agents** tab
2. Go to **Select** sub-tab
3. Choose your agent from the dropdown
4. Confirm selection

### Step 4: Create & Upload to Knowledge Base
1. Click on **Knowledge Base** tab
2. Go to **Create KB** sub-tab
3. Fill in:
   - **KB Name**: e.g., "Product Documentation"
   - **Description**: e.g., "Contains all product guides"
4. Click **Create KB**
5. Go to **Upload Text** sub-tab
6. Select the KB you just created
7. Paste text/documentation into the text area
8. Click **Upload**

### Step 5: Query the RAG System (Main Test)
1. Click on **Query** tab
2. Enter your question: e.g., "What features does your product have?"
3. Select the KB from dropdown
4. Click **Ask**
5. View results:
   - **Answer**: Generated response from LLM
   - **Sources**: Click to expand and see retrieved chunks
   - **Stats**: Expand to see tokens, latency, LLM info, cost (if billing enabled)

### Step 6: Check Analytics
1. Click on **Analytics** tab
2. View:
   - **Total Queries**: Count of queries made
   - **Avg Latency**: Average response time
   - **Query History**: Last 10 queries

### Step 7: Check Billing (Optional)
1. Click on **Billing** tab
2. If billing is enabled in backend:
   - Shows your tenant cost
   - Shows API call count
   - Shows total tokens used
3. If disabled, shows "Billing system is disabled (MVP mode)"

---

## UI Structure

### Sidebar
- **🔐 Authentication**: Login/Signup/Logout
- **⚙️ Settings**: API URL, Health Check

### Main Tabs (when logged in)
1. **🤖 Agents**: Create agents, select active agent
2. **📚 Knowledge Base**: Create KBs, upload text
3. **🔍 Query**: Main testing - input query, view answer + sources + stats
4. **📈 Analytics**: Query count, latency metrics, history
5. **💳 Billing**: Cost tracking (only if enabled)
6. **🔧 Debug**: Session state inspection

---

## API Endpoints Called

| Panel | Endpoint | Method | Purpose |
|-------|----------|--------|---------|
| Auth | `/api/v1/auth/register` | POST | Signup |
| Auth | `/api/v1/auth/login` | POST | Login |
| Agents | `/api/v1/agents` | POST | Create agent |
| Agents | `/api/v1/agents` | GET | List agents |
| KB | `/api/v1/agents/{id}/knowledge-bases` | GET | List KBs |
| KB | `/api/v1/agents/{id}/knowledge-bases` | POST | Create KB |
| KB | `/api/v1/agents/{id}/knowledge-bases/{id}/upload` | POST | Upload text |
| Query | `/api/v1/rag/query` | POST | Execute query |
| Analytics | `/api/v1/metrics` | GET | Get metrics |
| Billing | `/api/v1/billing/metrics` | GET | Get billing data |

All requests include `Authorization: Bearer <token>` header.

---

## Features

### ✅ Implemented
- **Auth Flow**: Signup → Login with JWT token storage in session
- **Agent Management**: Create agents, list and select for operations
- **KB Management**: Create KBs, upload text to specific KB
- **RAG Query**: Full query with answer, sources, and detailed stats
- **Analytics**: Query count, latency tracking, query history (last 10)
- **Billing**: Conditional display (only if enabled in backend)
- **Robust Errors**: Clear error messages with status codes
- **Session State**: Persistent token, selected agent, API URL

### 🎯 Design Principles
- **Simple & Functional**: No fancy styling, focus on testing
- **Minimal Clicks**: One-click operations where possible
- **Real-World Flow**: Signup → Agent → KB → Query
- **Expandable Sections**: Details hidden by default (Sources, Stats)
- **Status Indicators**: ✅ ❌ 🔴 🟢 for quick feedback

---

## Troubleshooting

### Connection Error: "API connection failed"
- Ensure backend is running: `uvicorn app.main:app --reload`
- Check API URL in Settings (default: http://localhost:8000)
- Check backend logs for errors

### Login/Signup fails
- Verify credentials (email should be unique)
- Check backend logs for auth errors
- Ensure JWT secret is configured in backend

### Upload fails
- Ensure KB exists
- Ensure text is not empty
- Check backend logs for chunk creation errors

### Query returns no answer
- Ensure KB has content uploaded
- Wait a moment for embeddings to process
- Check backend logs for embedding errors
- Verify Neo4j is running for graph operations

### Billing shows as disabled when it should be enabled
- Set `ENABLE_BILLING=True` in backend `.env`
- Restart backend: `uvicorn app.main:app --reload`
- Refresh console

---

## Tips for Effective Testing

### Performance Testing
1. Go to **Analytics** tab
2. Run multiple queries
3. Watch "Avg Latency" for performance trends
4. Check cache hit rate in backend logs

### Cost Estimation Testing
1. Enable billing in backend (`.env`)
2. Run queries
3. Check **Billing** tab
4. Verify cost calculation matches tokens

### Multi-Tenant Testing
1. Create multiple user accounts
2. Create different agents per user
3. Upload different KBs
4. Run queries - verify isolation in Debug tab

### Graph RAG Testing
1. Upload structured data (e.g., "Product A has Feature B")
2. Ask graph-oriented questions (e.g., "What features does Product A have?")
3. Check Sources to see graph expansion results
4. Verify answer includes graph-derived information

---

## Next Steps

Once testing is complete:
1. Note any bugs in backend
2. Fix backend issues
3. Re-run test flows
4. When confident, deploy to production
5. Switch `ENABLE_BILLING=True` for real tracking

---

## Architecture Diagram

```
Streamlit UI (you are here)
    ↓
requests library (HTTP client)
    ↓
FastAPI Backend (Your API)
    ├── Auth Service → JWT tokens
    ├── Agent Service → Create/list agents
    ├── KB Service → Upload documents
    ├── RAG Service → Query logic
    │   ├── Embedding (DeepInfra)
    │   ├── Retrieval (Vector DB)
    │   ├── Graph Expansion (Neo4j)
    │   └── Answer Generation (DeepInfra LLM)
    └── Billing Service (optional)
```

---

## Session State Tracking

The console maintains Streamlit session state for:
- **token**: JWT token (persists across UI interactions)
- **user_email**: Logged-in user
- **user_id**: User ID
- **selected_agent_id**: Active agent for KB/Query operations
- **api_url**: Backend URL
- **query_history**: List of recent queries + latencies
- **billing_enabled**: Whether billing is active

All state resets when you close the browser tab.

---

**Happy Testing! 🚀**
