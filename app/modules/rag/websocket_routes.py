"""
WebSocket RAG routes - Streaming chat interface for GraphRAG
Phase 3: Real-time Conversational Retrieval
"""

import logging
import json
import asyncio
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status

from .service import RAGService
from ...core.database import AsyncSessionLocal
from ...core.security import verify_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket RAG"])


@router.websocket("/{agent_id}")
async def rag_websocket(
    websocket: WebSocket,
    agent_id: str,
    token: str = Query(...),
):
    """
    WebSocket endpoint for real-time RAG chat.
    
    SECURITY:
    1. Authenticates via token in query params (standard for WS)
    2. Enforces tenant isolation from JWT payload
    3. Validates agent ownership in every request
    
    PROTOCOL:
    - Client sends: {"query": "message"}
    - Server sends (metadata): {"type": "metadata", "sources": [...]}
    - Server sends (chunk): "text chunk"
    - Server sends (done): {"type": "done"}
    """
    # 1. AUTHENTICATION
    payload = await verify_access_token(token)
    if not payload:
        logger.warning(f"WebSocket auth failed for agent {agent_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    tenant_id = payload.tenant_id
    user_id = payload.user_id
    
    await websocket.accept()
    logger.info(f"✅ WebSocket connected: Agent={agent_id}, Tenant={tenant_id}")

    try:
        while True:
            # 2. WAIT FOR MESSAGE
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                query = msg.get("query")
            except:
                await websocket.send_text(json.dumps({"error": "Invalid JSON format"}))
                continue

            if not query:
                continue

            logger.info(f"💬 WS Query: {query[:50]}...")

            # 3. INITIALIZE SERVICE
            from ...core.database import get_db_with_tenant
            async with get_db_with_tenant(tenant_id) as db:
                rag_service = RAGService(db=db, tenant_id=tenant_id)
                
                # AUTO-RESOLVE KB (Agent owns 1 KB by default in this architecture)
                from ..knowledge_bases.repository import KnowledgeBaseRepository
                kb_repo = KnowledgeBaseRepository(db, tenant_id)
                kb = await kb_repo.get_one_by_agent(agent_id)
                
                if not kb:
                    await websocket.send_text(json.dumps({"error": "Knowledge Base not found"}))
                    continue

                # 4. STREAM RESPONSE
                async for chunk in rag_service.stream_rag_answer(
                    query=query,
                    agent_id=agent_id,
                    kb_id=str(kb.id)
                ):
                    # Check if chunk is JSON metadata or raw text
                    await websocket.send_text(chunk)

                # 5. SIGNAL COMPLETION
                await websocket.send_text(json.dumps({"type": "done"}))

    except WebSocketDisconnect:
        logger.info(f"❌ WebSocket disconnected: Agent={agent_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_text(json.dumps({"error": str(e)}))
        except:
            pass
