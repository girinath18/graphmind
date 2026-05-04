#!/bin/bash
# Startup script for GraphMind backend with detailed logging

echo "=========================================="
echo "🚀 Starting GraphMind Backend"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  LOG_LEVEL: DEBUG"
echo "  POSTGRES_ECHO: true"
echo "  Environment: development"
echo ""
echo "Starting uvicorn with detailed output..."
echo "=========================================="
echo ""

# Start with coverage and detailed output
cd v:\graphmind
uvicorn app.main:app --reload --port 8001 --log-level debug
