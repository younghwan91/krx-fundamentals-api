from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from redis.exceptions import RedisError

from krx_fundamentals_api.models.schemas import (
    PaginatedResponse,
    RankingMetric,
)
from krx_fundamentals_api.services.cache import (
    get_all_crawler_status,
    get_ranking,
    get_sectors,
    screen_stocks,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")


@router.get("/market/overview")
async def market_overview():
    """시장 개요 (섹터 현황 + 크롤러 상태)."""
    try:
        sectors = await get_sectors()
        statuses = await get_all_crawler_status()
        return {"sectors": sectors, "crawler_status": statuses}
    except RedisError:
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    except Exception:
        logger.exception("Unexpected error in market_overview")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/market/sectors")
async def list_sectors():
    """섹터별 현황."""
    try:
        sectors = await get_sectors()
        return {"sectors": sectors, "total": len(sectors)}
    except RedisError:
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    except Exception:
        logger.exception("Unexpected error in list_sectors")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/ranking/{metric}")
async def stock_ranking(
    metric: RankingMetric,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ascending: bool = Query(False, description="오름차순 정렬"),
):
    """랭킹 조회. metric: market_cap, per, pbr, roe, dividend_yield, revenue, net_income"""
    try:
        items, total = await get_ranking(
            metric=metric.value, page=page, page_size=page_size, ascending=ascending,
        )
        return PaginatedResponse(
            items=items, total=total, page=page,
            page_size=page_size, has_next=(page * page_size) < total,
        )
    except RedisError:
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    except Exception:
        logger.exception("Unexpected error in stock_ranking")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/screening")
async def screening(
    market: str | None = Query(None, description="시장 (kospi, kosdaq)"),
    sector: str | None = Query(None, description="섹터/업종"),
    per_min: float | None = Query(None, description="PER 최소"),
    per_max: float | None = Query(None, description="PER 최대"),
    pbr_min: float | None = Query(None, description="PBR 최소"),
    pbr_max: float | None = Query(None, description="PBR 최대"),
    roe_min: float | None = Query(None, description="ROE 최소 (%)"),
    dividend_yield_min: float | None = Query(None, description="배당수익률 최소 (%)"),
    market_cap_min: float | None = Query(None, description="시가총액 최소 (억원)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """종목 스크리닝 — 다중 조건 필터링."""
    try:
        items, total = await screen_stocks(
            market=market, sector=sector,
            per_min=per_min, per_max=per_max,
            pbr_min=pbr_min, pbr_max=pbr_max,
            roe_min=roe_min,
            dividend_yield_min=dividend_yield_min,
            market_cap_min=market_cap_min,
            page=page, page_size=page_size,
        )
        return PaginatedResponse(
            items=items, total=total, page=page,
            page_size=page_size, has_next=(page * page_size) < total,
        )
    except RedisError:
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    except Exception:
        logger.exception("Unexpected error in screening")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status")
async def crawler_status():
    """크롤러 상태 확인."""
    try:
        return await get_all_crawler_status()
    except RedisError:
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    except Exception:
        logger.exception("Unexpected error in crawler_status")
        raise HTTPException(status_code=500, detail="Internal server error")
