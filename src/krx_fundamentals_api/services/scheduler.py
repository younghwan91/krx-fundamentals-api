from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from krx_fundamentals_api.config import settings
from krx_fundamentals_api.models.schemas import DataSource, Market
from krx_fundamentals_api.scrapers.dart import DartScraper
from krx_fundamentals_api.scrapers.krx import KrxScraper
from krx_fundamentals_api.scrapers.naver import NaverScraper
from krx_fundamentals_api.services.cache import (
    cache_companies,
    cache_dividends,
    cache_financials,
    cache_ratios,
    cache_sectors,
    get_all_companies,
    update_crawler_status,
)

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None
_dart = DartScraper()
_krx = KrxScraper()
_naver = NaverScraper()


async def crawl_corp_codes() -> None:
    """DART 고유번호 매핑 갱신."""
    try:
        corp_map = await _dart.load_corp_codes()
        logger.info("Loaded %d corp code mappings", len(corp_map))
        await update_crawler_status(DataSource.DART, "corp_codes", len(corp_map))
    except Exception as e:
        logger.exception("Failed to load corp codes")
        await update_crawler_status(DataSource.DART, "corp_codes", error=str(e))


async def crawl_companies() -> None:
    """DART 기업개황 수집."""
    try:
        companies = await get_all_companies()
        tickers = [c.ticker for c in companies] if companies else []

        if not tickers:
            corp_map = _dart.get_corp_map()
            if not corp_map:
                # corp_codes 잡이 아직 안 돌았거나(재시작 등) 이 프로세스에서
                # 처음 불리는 경우 — 순서에 기대지 않고 직접 채운다.
                corp_map = await _dart.load_corp_codes()
            tickers = list(corp_map.keys())[:50]

        result = []
        for ticker in tickers[:200]:
            company = await _dart.fetch_company(ticker)
            if company:
                result.append(company)

        if result:
            await cache_companies(result)
        await update_crawler_status(DataSource.DART, "companies", len(result))
    except Exception as e:
        logger.exception("Failed to crawl companies")
        await update_crawler_status(DataSource.DART, "companies", error=str(e))


async def crawl_krx_ratios() -> None:
    """KRX 투자지표 수집."""
    try:
        all_ratios = []
        for market in [Market.KOSPI, Market.KOSDAQ]:
            ratios = await _krx.fetch_investment_ratios(market)
            all_ratios.extend(ratios)

        if all_ratios:
            await cache_ratios(all_ratios)

        sectors = await _krx.fetch_sectors()
        if sectors:
            await cache_sectors(sectors)

        await update_crawler_status(DataSource.KRX, "ratios", len(all_ratios))
    except Exception as e:
        logger.exception("Failed to crawl KRX ratios")
        await update_crawler_status(DataSource.KRX, "ratios", error=str(e))


async def crawl_naver_supplement() -> None:
    """네이버 금융 보조 데이터 수집 (상위 종목만)."""
    try:
        companies = await get_all_companies()
        tickers = [c.ticker for c in companies[:100]] if companies else []

        if tickers:
            ratios = await _naver.fetch_batch(tickers)
            if ratios:
                await cache_ratios(ratios)
            await update_crawler_status(DataSource.NAVER, "supplement", len(ratios))
        else:
            await update_crawler_status(DataSource.NAVER, "supplement", 0)
    except Exception as e:
        logger.exception("Failed to crawl Naver supplement")
        await update_crawler_status(DataSource.NAVER, "supplement", error=str(e))


async def crawl_financials_sample() -> None:
    """주요 종목 재무제표 수집 (샘플)."""
    try:
        from datetime import datetime

        current_year = datetime.now().year
        companies = await get_all_companies()
        tickers = [c.ticker for c in companies[:50]] if companies else []
        count = 0

        for ticker in tickers:
            statements = []
            for year in range(current_year - 2, current_year + 1):
                fs = await _dart.fetch_financials(ticker, year)
                if fs:
                    statements.append(fs)
            if statements:
                await cache_financials(ticker, statements)
                count += len(statements)

        await update_crawler_status(DataSource.DART, "financials", count)
    except Exception as e:
        logger.exception("Failed to crawl financials")
        await update_crawler_status(DataSource.DART, "financials", error=str(e))


async def crawl_dividends_sample() -> None:
    """주요 종목 배당 수집."""
    try:
        from datetime import datetime

        current_year = datetime.now().year
        companies = await get_all_companies()
        tickers = [c.ticker for c in companies[:50]] if companies else []
        count = 0

        for ticker in tickers:
            dividends = []
            for year in range(current_year - 3, current_year + 1):
                d = await _dart.fetch_dividends(ticker, year)
                if d:
                    dividends.append(d)
            if dividends:
                await cache_dividends(ticker, dividends)
                count += len(dividends)

        await update_crawler_status(DataSource.DART, "dividends", count)
    except Exception as e:
        logger.exception("Failed to crawl dividends")
        await update_crawler_status(DataSource.DART, "dividends", error=str(e))


async def bootstrap_dart_chain() -> None:
    """앱 시작 시 최초 1회, 의존성 순서대로 초기 데이터를 채운다.

    companies는 corp_codes(고유번호 매핑)에 의존하고, financials/dividends는
    companies 캐시에 의존한다 — 독립된 "(초기)" 잡으로 따로 스케줄링하면
    실행 순서가 보장 안 돼 첫 실행에서 전부 빈 목록으로 끝난다(실제로 겪은
    문제). 순서를 명시적으로 강제하기 위해 하나의 잡으로 순차 실행한다.
    """
    await crawl_corp_codes()
    await crawl_companies()
    await crawl_financials_sample()
    await crawl_dividends_sample()


def start_scheduler() -> None:
    global _scheduler
    _scheduler = AsyncIOScheduler()

    # 종목 마스터: 시작 시 즉시(체인 전체) + 매일 갱신
    _scheduler.add_job(crawl_corp_codes, "interval", seconds=settings.crawl_interval_master,
                       id="corp_codes", name="DART 고유번호")
    _scheduler.add_job(bootstrap_dart_chain, id="dart_bootstrap_init",
                       name="DART 초기 부트스트랩 (고유번호→기업개황→재무제표→배당)")

    # KRX 투자지표: 1시간마다
    _scheduler.add_job(crawl_krx_ratios, "interval", seconds=settings.crawl_interval_ratios,
                       id="krx_ratios", name="KRX 투자지표")
    _scheduler.add_job(crawl_krx_ratios, id="krx_ratios_init", name="KRX 투자지표 (초기)")

    # 기업개황: 매일
    _scheduler.add_job(crawl_companies, "interval", seconds=settings.crawl_interval_financials,
                       id="companies", name="DART 기업개황")

    # 재무제표: 매일
    _scheduler.add_job(crawl_financials_sample, "interval",
                       seconds=settings.crawl_interval_financials,
                       id="financials", name="DART 재무제표")

    # 배당: 매일
    _scheduler.add_job(crawl_dividends_sample, "interval",
                       seconds=settings.crawl_interval_financials,
                       id="dividends", name="DART 배당")

    # 네이버 보조: 1시간마다
    _scheduler.add_job(crawl_naver_supplement, "interval",
                       seconds=settings.crawl_interval_ratios,
                       id="naver_supplement", name="네이버 보조")

    _scheduler.start()
    logger.info("Scheduler started with %d jobs", len(_scheduler.get_jobs()))


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown()
        _scheduler = None
        logger.info("Scheduler stopped")
