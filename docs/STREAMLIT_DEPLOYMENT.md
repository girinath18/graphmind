# Streamlit Console - Deployment Guide

This guide covers running the Streamlit testing console in development, staging, and production environments.

---

## Local Development (Recommended for Testing)

### 1. Install Dependencies
```bash
pip install -r requirements-streamlit.txt
```

### 2. Start Backend (Terminal 1)
```bash
cd v:\graphmind
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start Streamlit (Terminal 2)
```bash
cd v:\graphmind
streamlit run streamlit_console.py
```

**Access**: http://localhost:8501

**Features:**
- Hot reload on code changes
- Full error details
- Interactive debugging
- Session persistence

---

## Docker Deployment

### 1. Create Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements-streamlit.txt

COPY streamlit_console.py ./
COPY .streamlit/ ./.streamlit/

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_console.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 2. Build Image
```bash
docker build -t graphmind-console:latest .
```

### 3. Run Container
```bash
docker run -d \
  --name graphmind-console \
  -p 8501:8501 \
  -e API_BASE_URL=http://backend:8000 \
  graphmind-console:latest
```

**Access**: http://localhost:8501

---

## Docker Compose Deployment (Recommended)

### docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    image: graphmind:latest
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:pass@db:5432/graphmind
      ENABLE_BILLING: "false"
    depends_on:
      - db
      - neo4j

  console:
    image: graphmind-console:latest
    ports:
      - "8501:8501"
    environment:
      API_BASE_URL: http://backend:8000
    depends_on:
      - backend

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: graphmind
    volumes:
      - postgres_data:/var/lib/postgresql/data

  neo4j:
    image: neo4j:latest
    environment:
      NEO4J_AUTH: neo4j/password
    ports:
      - "7687:7687"
    volumes:
      - neo4j_data:/data

volumes:
  postgres_data:
  neo4j_data:
```

### Run Everything
```bash
docker-compose up -d

# View logs
docker-compose logs console -f

# Stop
docker-compose down
```

**Backend**: http://localhost:8000
**Console**: http://localhost:8501

---

## Kubernetes Deployment

### 1. Create Namespace
```bash
kubectl create namespace graphmind
```

### 2. Deployment Manifest
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: graphmind-console
  namespace: graphmind
spec:
  replicas: 1
  selector:
    matchLabels:
      app: graphmind-console
  template:
    metadata:
      labels:
        app: graphmind-console
    spec:
      containers:
      - name: console
        image: graphmind-console:latest
        ports:
        - containerPort: 8501
        env:
        - name: API_BASE_URL
          value: "http://graphmind-backend:8000"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: graphmind-console
  namespace: graphmind
spec:
  type: LoadBalancer
  selector:
    app: graphmind-console
  ports:
  - port: 8501
    targetPort: 8501
```

### Deploy
```bash
kubectl apply -f console-deployment.yaml

# Check status
kubectl get pods -n graphmind

# Port forward
kubectl port-forward svc/graphmind-console 8501:8501 -n graphmind
```

**Access**: http://localhost:8501

---

## Systemd Service (Linux Production)

### 1. Create Service File
```bash
sudo nano /etc/systemd/system/graphmind-console.service
```

### 2. Service Configuration
```ini
[Unit]
Description=GraphMind Testing Console
After=network.target

[Service]
Type=simple
User=graphmind
WorkingDirectory=/home/graphmind/graphmind
Environment="PATH=/home/graphmind/graphmind/venv/bin"
Environment="API_BASE_URL=http://localhost:8000"
ExecStart=/home/graphmind/graphmind/venv/bin/streamlit run streamlit_console.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --logger.level=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Enable & Start
```bash
sudo systemctl daemon-reload
sudo systemctl enable graphmind-console
sudo systemctl start graphmind-console

# View logs
sudo journalctl -u graphmind-console -f

# Stop
sudo systemctl stop graphmind-console
```

**Access**: http://your-server:8501

---

## Nginx Reverse Proxy

### nginx.conf
```nginx
upstream streamlit {
    server localhost:8501;
}

server {
    listen 80;
    server_name console.graphmind.com;

    location / {
        proxy_pass http://streamlit;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Streamlit WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Enable
```bash
sudo nginx -t
sudo systemctl restart nginx
```

**Access**: http://console.graphmind.com

---

## Environment Variables

### Configuration via Environment
```bash
export API_BASE_URL=http://backend:8000
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_LOGGER_LEVEL=info

streamlit run streamlit_console.py
```

### All Supported Variables
| Variable | Default | Purpose |
|----------|---------|---------|
| API_BASE_URL | http://localhost:8000 | Backend API URL |
| STREAMLIT_SERVER_PORT | 8501 | Streamlit port |
| STREAMLIT_SERVER_ADDRESS | localhost | Bind address |
| STREAMLIT_LOGGER_LEVEL | info | Log level |
| STREAMLIT_CLIENT_SHOW_ERROR_DETAILS | true | Show error details |

---

## Performance Tuning

### Streamlit Config Optimization
```toml
# .streamlit/config.toml

[client]
showErrorDetails = false  # Disable in prod

[logger]
level = "warning"  # Use warning in prod

[server]
maxUploadSize = 200  # MB
enableXsrfProtection = true
headless = true
runOnSave = false  # Disable auto reload in prod
```

### Backend Connection Pool
Streamlit reuses HTTP connections. Most queries should complete in < 2 seconds.

### Cache Strategy
- Streamlit caches API responses in session state
- No separate caching needed (requests are fast)
- Queries < 500ms = Good
- Queries < 2000ms = Acceptable
- Queries > 3000ms = Investigate backend

---

## Monitoring

### Health Check Endpoint
```bash
curl http://localhost:8501/healthz
```

### Log Levels
```bash
INFO    - Normal operation
WARNING - Configuration issues
ERROR   - API connection failures
DEBUG   - Detailed debugging (dev only)
```

### Common Issues & Fixes

**Issue**: Port 8501 already in use
```bash
# Find process
lsof -i :8501

# Kill it
kill -9 <PID>

# Or use different port
streamlit run streamlit_console.py --server.port=8502
```

**Issue**: Backend connection refused
```bash
# Check backend is running
curl http://localhost:8000/health

# Verify API_BASE_URL
echo $API_BASE_URL

# Update in Settings tab of console
```

**Issue**: Long load times
```bash
# Check backend performance
curl -w "%{time_total}" http://localhost:8000/health

# Check network latency
ping localhost

# Increase timeout in code (advanced)
```

**Issue**: WebSocket connection failed
```bash
# Ensure reverse proxy supports WebSockets
# (see Nginx config above)

# Verify CORS headers if cross-origin
```

---

## Backup & Recovery

### State Backup
```bash
# Session state is in-memory only
# NOT persisted to disk

# To preserve state:
# 1. Export query history manually
# 2. Take screenshots of results
# 3. Save API responses to files
```

### Docker Volume Backup
```bash
docker inspect graphmind-console
# No volumes - state is ephemeral
```

### Configuration Backup
```bash
# Backup these files
cp .streamlit/config.toml config.toml.backup
cp .streamlit/secrets.toml secrets.toml.backup
```

---

## Scaling

### Single Instance (Current)
- 1 Streamlit process
- Handles ~100 concurrent users
- Memory: 256MB base + 10MB per active user
- Suitable for: Development, testing, small teams

### Load Balanced (Multi-Instance)
```yaml
# Multiple console instances behind load balancer
# Each independent
# Scaling: Add/remove instances as needed
```

### Requirements
```
1 instance:   1 CPU, 512MB RAM
5 instances:  2 CPUs, 3GB RAM
10 instances: 4 CPUs, 5GB RAM
```

---

## Security

### Production Checklist
- [ ] Use HTTPS (add SSL cert to Nginx)
- [ ] Enable `showErrorDetails = false` in .streamlit/config.toml
- [ ] Use strong JWT secret in backend
- [ ] Use database credentials from secrets manager
- [ ] Enable firewall rules (only allow from office IPs)
- [ ] Enable audit logging in backend
- [ ] Set `ENABLE_BILLING=True` only when ready
- [ ] Use restricted database user (read-only queries only)
- [ ] Enable rate limiting on API

### CORS Configuration (Backend)
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "https://console.graphmind.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Troubleshooting Checklist

- [ ] Backend running? `curl http://localhost:8000/health`
- [ ] Streamlit running? Check logs for errors
- [ ] API credentials correct? Check JWT token in Debug tab
- [ ] Network latency? Check backend response time
- [ ] Port conflicts? `lsof -i :8501`
- [ ] Out of memory? Check system resources
- [ ] Docker build error? Verify requirements.txt
- [ ] Pytest failures? Check test data exists

---

## Upgrade & Rollback

### Upgrade Streamlit
```bash
pip install --upgrade streamlit
pip freeze > requirements-streamlit.txt
docker build -t graphmind-console:v2 .
docker run -d -p 8501:8501 graphmind-console:v2
```

### Rollback
```bash
pip install streamlit==1.28.0  # Previous version
docker run -d -p 8501:8501 graphmind-console:v1
```

---

## Integration Tests (Post-Deployment)

```bash
#!/bin/bash

# Test 1: Console loads
curl http://localhost:8501 > /dev/null && echo "✅ Console loads"

# Test 2: Backend reachable
curl http://localhost:8000/health | grep -q "ok" && echo "✅ Backend available"

# Test 3: Signup flow
# (Manual - too interactive for bash)

# Test 4: Query latency
time curl -X GET http://localhost:8000/health
```

---

## Success Criteria

✅ **Development**: Works locally, <500ms queries
✅ **Staging**: Runs in Docker, <1000ms queries
✅ **Production**: Runs via systemd/K8s, <2000ms queries

---

**Last Updated**: April 2026
**Status**: Production Ready ✅
