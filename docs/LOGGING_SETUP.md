# LOGGING IMPROVEMENTS - DETAILED BACKEND LOGS

## 📋 What Was Fixed

### 1. **Logging Configuration (app/core/logging.py)**
   - ✅ Added proper StreamHandler to output to console
   - ✅ Configured root logger to capture ALL loggers
   - ✅ Set up formatters with timestamps
   - ✅ Ensured all app loggers (sqlalchemy, fastapi, uvicorn) are configured

### 2. **Main Application Startup (app/main.py)**
   - ✅ Added detailed startup banner with configuration
   - ✅ Logs: DB host, port, log level, debug mode
   - ✅ Added separators (====) for easy log scanning
   - ✅ Shows where API is available (/docs for Swagger)

### 3. **Database Initialization (app/core/database.py)**
   - ✅ Logs table creation with count
   - ✅ Shows registered models
   - ✅ Logs RLS policy activation for each table
   - ✅ Detailed RLS verification messages
   - ✅ Clear separation between init steps

### 4. **Authentication Logging (app/modules/auth/services.py)**
   - ✅ Logs every signup attempt with email
   - ✅ Shows tenant creation details
   - ✅ Shows user creation with ID
   - ✅ Logs token generation
   - ✅ Logs every login attempt with email
   - ✅ Shows password verification steps
   - ✅ Shows tenant lookup
   - ✅ Detailed error messages for each failure point

## 🚀 How to Use Enhanced Logging

### Option 1: Run with PowerShell Script (Recommended)
```powershell
cd v:\graphmind
.\start_backend.ps1
```

### Option 2: Manual uvicorn Command
```powershell
cd v:\graphmind
uvicorn app.main:app --reload --port 8001 --log-level debug
```

### Option 3: Python with Logging
```python
# Python will use settings from .env (LOG_LEVEL=DEBUG)
cd v:\graphmind
uvicorn app.main:app --reload --port 8001
```

## 📊 What You'll See in Logs

### Startup Logs:
```
================================================================================
🚀 Starting GraphMind v1.0.0
📍 Environment: DEVELOPMENT
🐛 Debug mode: true
📝 Log level: DEBUG
🔧 Database: localhost:5432/graphmind
🔐 Multi-tenancy: ENABLED (RLS ENFORCED)
================================================================================

📦 Initializing PostgreSQL...
📝 Creating database tables...
✅ Database tables created/verified (6 tables)
🔒 Enabling Row-Level Security (RLS)...
  ✓ RLS enabled on tenants
  ✓ RLS policy created on tenants
  ✓ RLS enabled on users
  ...
✅ RLS policies enabled on all tables
================================================================================
```

### Signup Logs:
```
📝 Signup attempt: user@example.com
  Checking if tenant 'My Company' exists...
  ✅ Created tenant: 550e8400-e29b-41d4-a716-446655440000 (My Company)
  Creating user: user@example.com...
  ✓ User registered: 660e8400-e29b-41d4-a716-446655440001
  Generating tokens...
✅ Signup successful: user@example.com
```

### Login Logs:
```
🔓 Login attempt: user@example.com
  Looking up user: user@example.com...
  Verifying password...
  ✅ Password verified for user@example.com
  Fetching tenant: 550e8400...
  ✅ Tenant verified: My Company
  Generating tokens...
✅ Login successful: user@example.com in tenant: My Company
```

### Error Logs:
```
❌ STARTUP FAILED: Connection to database failed
❌ APPLICATION CANNOT START - RLS enforcement is CRITICAL

❌ Login failed: user nonexistent@example.com not found
❌ Login failed: wrong password for user@example.com
```

## 🔍 Key Environment Variables

Make sure these are set in `.env`:
```
LOG_LEVEL=DEBUG              # Set to DEBUG for detailed logs
POSTGRES_ECHO=true           # Log all SQL queries
DEBUG=true                   # Enable debug mode
APP_ENV=development          # Set to development
```

## 🛠️ Troubleshooting

If you still don't see logs:

1. **Check .env file**
   - Verify `LOG_LEVEL=DEBUG`
   - Verify `POSTGRES_ECHO=true`

2. **Restart backend completely**
   - Kill any existing uvicorn process
   - Clear Python cache: `Remove-Item -Recurse __pycache__`
   - Start fresh

3. **Check terminal encoding**
   - PowerShell should show UTF-8 emoji/special characters
   - If not visible, output is still working, just not displaying fancy chars

4. **Verify port 8001 is free**
   - `netstat -ano | findstr :8001`
   - Kill if needed: `taskkill /PID <PID> /F`

## 📈 Log Levels

- **ERROR** (RED) - Critical failures that stop execution
- **WARNING** (YELLOW) - Issues that don't stop execution but should be noticed
- **INFO** (BLUE) - Important events and state changes
- **DEBUG** (GREEN) - Detailed diagnostic information

## ✅ Next Steps

1. Run: `.\start_backend.ps1`
2. Try signup/login in Streamlit
3. Check console for detailed logs
4. Share any error logs if issues occur
