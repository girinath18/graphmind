"""
Analytics Repository - Database abstraction for analytics entities.
"""

from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, func, update, delete, case
from sqlalchemy.ext.asyncio import AsyncSession
from .models import AnalyticsSummary, AnalyticsQueryLog, ResponseStatus

class AnalyticsRepository:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def create_summary(self, summary_data: dict) -> AnalyticsSummary:
        summary = AnalyticsSummary(**summary_data, tenant_id=self.tenant_id)
        self.db.add(summary)
        await self.db.flush()
        return summary

    async def get_summary_by_id(self, summary_id: UUID) -> Optional[AnalyticsSummary]:
        stmt = select(AnalyticsSummary).where(
            AnalyticsSummary.id == summary_id,
            AnalyticsSummary.tenant_id == self.tenant_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_summaries(self, skip: int = 0, limit: int = 100) -> List[AnalyticsSummary]:
        stmt = select(AnalyticsSummary).where(
            AnalyticsSummary.tenant_id == self.tenant_id
        ).offset(skip).limit(limit).order_by(AnalyticsSummary.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update_summary(self, summary_id: UUID, update_data: dict) -> Optional[AnalyticsSummary]:
        stmt = update(AnalyticsSummary).where(
            AnalyticsSummary.id == summary_id,
            AnalyticsSummary.tenant_id == self.tenant_id
        ).values(**update_data).returning(AnalyticsSummary)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_summary(self, summary_id: UUID) -> bool:
        stmt = delete(AnalyticsSummary).where(
            AnalyticsSummary.id == summary_id,
            AnalyticsSummary.tenant_id == self.tenant_id
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def create_query_log(self, log_data: dict) -> AnalyticsQueryLog:
        log = AnalyticsQueryLog(**log_data, tenant_id=self.tenant_id)
        self.db.add(log)
        await self.db.flush()
        return log

    async def get_query_logs(self, skip: int = 0, limit: int = 100) -> List[AnalyticsQueryLog]:
        stmt = select(AnalyticsQueryLog).where(
            AnalyticsQueryLog.tenant_id == self.tenant_id
        ).offset(skip).limit(limit).order_by(AnalyticsQueryLog.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_aggregated_metrics(self) -> dict:
        """Fetch high-level metrics for dashboard directly from logs."""
        stmt = select(
            func.count(AnalyticsQueryLog.id).label("total"),
            func.count(AnalyticsQueryLog.id).filter(
                AnalyticsQueryLog.response_status == ResponseStatus.SUCCESS
            ).label("answered"),
            func.count(AnalyticsQueryLog.id).filter(
                AnalyticsQueryLog.response_status == ResponseStatus.UNANSWERED
            ).label("unanswered"),
            func.avg(AnalyticsQueryLog.confidence_score).label("avg_conf")
        ).where(AnalyticsQueryLog.tenant_id == self.tenant_id)
        
        result = await self.db.execute(stmt)
        row = result.first()
        
        return {
            "total_queries": row.total or 0,
            "answered_queries": int(row.answered or 0),
            "unanswered_queries": int(row.unanswered or 0),
            "avg_confidence": float(row.avg_conf or 0.0)
        }

    async def get_query_trends(self) -> List[Tuple[str, int]]:
        """Get daily query volume trends."""
        stmt = select(
            func.to_char(AnalyticsQueryLog.created_at, 'YYYY-MM-DD').label("date"),
            func.count(AnalyticsQueryLog.id).label("count")
        ).where(
            AnalyticsQueryLog.tenant_id == self.tenant_id
        ).group_by("date").order_by("date").limit(30)
        
        result = await self.db.execute(stmt)
        return result.all()

    async def get_unanswered_logs(self, limit: int = 50) -> List[AnalyticsQueryLog]:
        stmt = select(AnalyticsQueryLog).where(
            AnalyticsQueryLog.tenant_id == self.tenant_id,
            AnalyticsQueryLog.response_status == ResponseStatus.UNANSWERED
        ).limit(limit).order_by(AnalyticsQueryLog.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_confidence_distribution(self) -> List[dict]:
        """Get distribution of confidence scores in 0.2 buckets."""
        bucket = func.floor(AnalyticsQueryLog.confidence_score * 5) / 5.0
        stmt = select(
            bucket,
            func.count(AnalyticsQueryLog.id)
        ).where(
            AnalyticsQueryLog.tenant_id == self.tenant_id
        ).group_by(bucket).order_by(bucket)
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        # Initialize buckets
        distribution = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0
        }
        
        for floor_val, count in rows:
            if floor_val < 0.2: distribution["0.0-0.2"] += count
            elif floor_val < 0.4: distribution["0.2-0.4"] += count
            elif floor_val < 0.6: distribution["0.4-0.6"] += count
            elif floor_val < 0.8: distribution["0.6-0.8"] += count
            else: distribution["0.8-1.0"] += count
            
        return [{"bucket": k, "count": v} for k, v in distribution.items()]
