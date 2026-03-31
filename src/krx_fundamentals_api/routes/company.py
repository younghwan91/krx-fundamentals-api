from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from redis.exceptions import RedisError

from krx_fundamentals_api.models.schemas import (
    PaginatedResponse,
)
from krx_fundamentals_api.services.cache import (
    get_all_companies,
    get_company,
    get_dividends,
    get_executives,
    get_financials,
    get_ratio,
    get_shareholders,
    search_companies,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")


@router.get("/companies")
async def list_companies(
    q: str | None = Query(None, description="검색어 (회사명 또는 종목코드)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """전종목 목록. 검색어로 필터 가능."""
    try:
        if q:
            companies = await search_companies(q)
        else:
            companies = await get_all_companies()
        total = len(companies)
        start = (page - 1) * page_size
        items = companies[start : start + page_size]
        return PaginatedResponse(
            items=items, total=total, page=page,
            page_size=page_size, has_next=(page * page_size) < total,
        )
    except RedisError:
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    except Exception:
        logger.exception("Unexpected error in list_companies")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/companies/{ticker}")
async def get_company_info(ticker: str):
    """기업 개황 조회."""
    try:
        company = await get_company(ticker)
        if not company:
            raise HTTPException(status_code=404, detail=f"Company {ticker} not found")
        return company
    except HTTPException:
        raise
    except RedisError:
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    except Exception:
        logger.exception("Unexpected error in get_company_info")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/companies/{ticker}/financials")
async def get_company_financials(ticker: str):
    """재무제표 조회 (연간/분기)."""
    try:
        statements = await get_financials(ticker)
        return {"ticker": ticker, "statements": statements, "total": len(statements)}
    except RedisError:
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    except Exception:
        logger.exception("Unexpected error in get_company_financials")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/companies/{ticker}/ratios")
async def get_company_ratios(ticker: str):
    """투자지표 조회 (PER, PBR, ROE 등)."""
    try:
        ratio = await get_ratio(ticker)
        if not ratio:
            raise HTTPException(status_code=404, detail=f"Ratios for {ticker} not found")
        return ratio
    except HTTPException:
        raise
    except RedisError:
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    except Exception:
        logger.exception("Unexpected error in get_company_ratios")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/companies/{ticker}/dividends")
async def get_company_dividends(ticker: str):
    """배당 정보 조회."""
    try:
        dividends = await get_dividends(ticker)
        return {"ticker": ticker, "dividends": dividends, "total": len(dividends)}
    except RedisError:
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    except Exception:
        logger.exception("Unexpected error in get_company_dividends")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/companies/{ticker}/shareholders")
async def get_company_shareholders(ticker: str):
    """대주주 현황 조회."""
    try:
        shareholders = await get_shareholders(ticker)
        return {"ticker": ticker, "shareholders": shareholders, "total": len(shareholders)}
    except RedisError:
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    except Exception:
        logger.exception("Unexpected error in get_company_shareholders")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/companies/{ticker}/executives")
async def get_company_executives(ticker: str):
    """임원 현황 조회."""
    try:
        executives = await get_executives(ticker)
        return {"ticker": ticker, "executives": executives, "total": len(executives)}
    except RedisError:
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    except Exception:
        logger.exception("Unexpected error in get_company_executives")
        raise HTTPException(status_code=500, detail="Internal server error")
