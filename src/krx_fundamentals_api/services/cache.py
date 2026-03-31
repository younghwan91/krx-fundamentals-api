from __future__ import annotations

import json
import logging
from datetime import datetime

import redis.asyncio as redis

from krx_fundamentals_api.config import settings
from krx_fundamentals_api.models.schemas import (
    Company,
    CrawlerStatus,
    DataSource,
    Dividend,
    Executive,
    FinancialStatement,
    InvestmentRatio,
    SectorOverview,
    Shareholder,
)

logger = logging.getLogger(__name__)

_redis: redis.Redis | None = None

COMPANY_TTL = 86400  # 24h
FINANCIAL_TTL = 86400  # 24h
RATIO_TTL = 3600  # 1h
DIVIDEND_TTL = 86400  # 24h
SHAREHOLDER_TTL = 86400  # 24h
SECTOR_TTL = 3600  # 1h
SCREENING_TTL = 300  # 5min


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None


# --- Company ---


async def cache_companies(companies: list[Company]) -> int:
    r = await get_redis()
    pipe = r.pipeline()
    for c in companies:
        pipe.hset("company:all", c.ticker, c.model_dump_json())
    pipe.expire("company:all", COMPANY_TTL)
    await pipe.execute()
    logger.info("Cached %d companies", len(companies))
    return len(companies)


async def get_company(ticker: str) -> Company | None:
    r = await get_redis()
    raw = await r.hget("company:all", ticker)
    if raw:
        return Company.model_validate_json(raw)
    return None


async def get_all_companies() -> list[Company]:
    r = await get_redis()
    raw_map = await r.hgetall("company:all")
    return [Company.model_validate_json(v) for v in raw_map.values()]


async def search_companies(query: str) -> list[Company]:
    companies = await get_all_companies()
    q = query.lower()
    return [c for c in companies if q in c.name.lower() or q in c.ticker]


# --- Financials ---


async def cache_financials(ticker: str, statements: list[FinancialStatement]) -> int:
    r = await get_redis()
    key = f"financial:{ticker}"
    data = json.dumps(
        [s.model_dump(mode="json") for s in statements], ensure_ascii=False, default=str
    )
    await r.set(key, data, ex=FINANCIAL_TTL)
    return len(statements)


async def get_financials(ticker: str) -> list[FinancialStatement]:
    r = await get_redis()
    raw = await r.get(f"financial:{ticker}")
    if raw:
        return [FinancialStatement.model_validate(item) for item in json.loads(raw)]
    return []


# --- Investment Ratios ---


async def cache_ratios(ratios: list[InvestmentRatio]) -> int:
    r = await get_redis()
    pipe = r.pipeline()
    for ratio in ratios:
        pipe.hset("ratio:all", ratio.ticker, ratio.model_dump_json())
    pipe.expire("ratio:all", RATIO_TTL)
    await pipe.execute()
    logger.info("Cached %d investment ratios", len(ratios))
    return len(ratios)


async def get_ratio(ticker: str) -> InvestmentRatio | None:
    r = await get_redis()
    raw = await r.hget("ratio:all", ticker)
    if raw:
        return InvestmentRatio.model_validate_json(raw)
    return None


async def get_all_ratios() -> list[InvestmentRatio]:
    r = await get_redis()
    raw_map = await r.hgetall("ratio:all")
    return [InvestmentRatio.model_validate_json(v) for v in raw_map.values()]


# --- Dividends ---


async def cache_dividends(ticker: str, dividends: list[Dividend]) -> int:
    r = await get_redis()
    data = json.dumps(
        [d.model_dump(mode="json") for d in dividends], ensure_ascii=False, default=str
    )
    await r.set(f"dividend:{ticker}", data, ex=DIVIDEND_TTL)
    return len(dividends)


async def get_dividends(ticker: str) -> list[Dividend]:
    r = await get_redis()
    raw = await r.get(f"dividend:{ticker}")
    if raw:
        return [Dividend.model_validate(item) for item in json.loads(raw)]
    return []


# --- Shareholders ---


async def cache_shareholders(ticker: str, shareholders: list[Shareholder]) -> int:
    r = await get_redis()
    data = json.dumps(
        [s.model_dump(mode="json") for s in shareholders], ensure_ascii=False, default=str
    )
    await r.set(f"shareholder:{ticker}", data, ex=SHAREHOLDER_TTL)
    return len(shareholders)


async def get_shareholders(ticker: str) -> list[Shareholder]:
    r = await get_redis()
    raw = await r.get(f"shareholder:{ticker}")
    if raw:
        return [Shareholder.model_validate(item) for item in json.loads(raw)]
    return []


# --- Executives ---


async def cache_executives(ticker: str, executives: list[Executive]) -> int:
    r = await get_redis()
    data = json.dumps(
        [e.model_dump(mode="json") for e in executives], ensure_ascii=False, default=str
    )
    await r.set(f"executive:{ticker}", data, ex=SHAREHOLDER_TTL)
    return len(executives)


async def get_executives(ticker: str) -> list[Executive]:
    r = await get_redis()
    raw = await r.get(f"executive:{ticker}")
    if raw:
        return [Executive.model_validate(item) for item in json.loads(raw)]
    return []


# --- Sectors ---


async def cache_sectors(sectors: list[SectorOverview]) -> int:
    r = await get_redis()
    data = json.dumps(
        [s.model_dump(mode="json") for s in sectors], ensure_ascii=False, default=str
    )
    await r.set("sector:all", data, ex=SECTOR_TTL)
    return len(sectors)


async def get_sectors() -> list[SectorOverview]:
    r = await get_redis()
    raw = await r.get("sector:all")
    if raw:
        return [SectorOverview.model_validate(item) for item in json.loads(raw)]
    return []


# --- Screening ---


async def screen_stocks(
    market: str | None = None,
    sector: str | None = None,
    per_min: float | None = None,
    per_max: float | None = None,
    pbr_min: float | None = None,
    pbr_max: float | None = None,
    roe_min: float | None = None,
    roe_max: float | None = None,
    dividend_yield_min: float | None = None,
    market_cap_min: float | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[InvestmentRatio], int]:
    ratios = await get_all_ratios()

    filtered = []
    for r in ratios:
        if market and r.market and r.market.value != market:
            continue
        if per_min is not None and (r.per is None or r.per < per_min):
            continue
        if per_max is not None and (r.per is None or r.per > per_max):
            continue
        if pbr_min is not None and (r.pbr is None or r.pbr < pbr_min):
            continue
        if pbr_max is not None and (r.pbr is None or r.pbr > pbr_max):
            continue
        if roe_min is not None and (r.roe is None or r.roe < roe_min):
            continue
        if dividend_yield_min is not None and (
            r.dividend_yield is None or r.dividend_yield < dividend_yield_min
        ):
            continue
        if market_cap_min is not None and (
            r.market_cap is None or r.market_cap < market_cap_min
        ):
            continue
        filtered.append(r)

    # Sector filter (need company info)
    if sector:
        companies = await get_all_companies()
        sector_tickers = {c.ticker for c in companies if sector.lower() in c.sector.lower()}
        filtered = [r for r in filtered if r.ticker in sector_tickers]

    total = len(filtered)
    start = (page - 1) * page_size
    return filtered[start : start + page_size], total


# --- Ranking ---


async def get_ranking(
    metric: str, page: int = 1, page_size: int = 20, ascending: bool = False
) -> tuple[list[InvestmentRatio], int]:
    ratios = await get_all_ratios()

    attr_map = {
        "market_cap": "market_cap",
        "per": "per",
        "pbr": "pbr",
        "roe": "roe",
        "dividend_yield": "dividend_yield",
    }
    attr = attr_map.get(metric, "market_cap")
    valid = [r for r in ratios if getattr(r, attr, None) is not None]
    valid.sort(key=lambda r: getattr(r, attr, 0) or 0, reverse=not ascending)

    total = len(valid)
    start = (page - 1) * page_size
    return valid[start : start + page_size], total


# --- Crawler Status ---

STATUS_KEY = "crawler:status:{source}:{job}"


async def update_crawler_status(
    source: DataSource, job_name: str, items_count: int = 0, error: str | None = None
) -> None:
    r = await get_redis()
    status = CrawlerStatus(
        source=source,
        job_name=job_name,
        last_crawled_at=datetime.now(),
        items_count=items_count,
        is_healthy=error is None,
        error=error,
    )
    await r.set(STATUS_KEY.format(source=source.value, job=job_name), status.model_dump_json())


async def get_all_crawler_status() -> list[CrawlerStatus]:
    r = await get_redis()
    keys = []
    async for key in r.scan_iter("crawler:status:*"):
        keys.append(key)
    statuses = []
    for key in keys:
        raw = await r.get(key)
        if raw:
            statuses.append(CrawlerStatus.model_validate_json(raw))
    return statuses
