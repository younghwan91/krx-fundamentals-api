from __future__ import annotations

import logging

from krx_fundamentals_api.models.schemas import DataSource, InvestmentRatio, Market
from krx_fundamentals_api.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


def _parse_float(value: object) -> float | None:
    """문자열·숫자·None 을 float | None 으로 변환. 쉼표 제거 포함."""
    if value is None:
        return None
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return None


def _parse_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(float(str(value).replace(",", "")))
    except (ValueError, TypeError):
        return None


def _detect_market(market_name: str | None) -> Market | None:
    if not market_name:
        return None
    name = market_name.upper()
    if "KOSPI" in name:
        return Market.KOSPI
    if "KOSDAQ" in name:
        return Market.KOSDAQ
    if "KONEX" in name:
        return Market.KONEX
    return None


class NaverScraper(BaseScraper):
    """네이버 금융 모바일 JSON API 기반 투자지표 수집 스크래퍼."""

    source = DataSource.NAVER
    base_url = "https://m.stock.naver.com/api"
    min_delay = 0.3
    max_delay = 1.0

    async def fetch_stock_info(self, ticker: str) -> InvestmentRatio | None:
        """단일 종목의 기본 투자지표를 모바일 JSON API에서 수집한다."""
        url = f"{self.base_url}/stock/{ticker}/basic"
        try:
            resp = await self.fetch(url)
            data = resp.json()
        except Exception:
            logger.warning("[%s] Failed to fetch ticker %s", self.source, ticker)
            return None

        try:
            return InvestmentRatio(
                ticker=ticker,
                name=data.get("stockName", ""),
                market=_detect_market(data.get("marketName")),
                market_cap=_parse_float(data.get("marketCap")),
                per=_parse_float(data.get("per")),
                pbr=_parse_float(data.get("pbr")),
                eps=_parse_float(data.get("eps")),
                bps=_parse_float(data.get("bps")),
                dividend_yield=_parse_float(data.get("dividendYield")),
                price=_parse_float(data.get("closePrice")),
                volume=_parse_int(data.get("accumulatedTradingVolume")),
                high_52w=_parse_float(data.get("high52wPrice")),
                low_52w=_parse_float(data.get("low52wPrice")),
                foreign_ratio=_parse_float(data.get("foreignRatio")),
            )
        except Exception:
            logger.warning(
                "[%s] Failed to parse response for ticker %s",
                self.source,
                ticker,
                exc_info=True,
            )
            return None

    async def fetch_batch(
        self, tickers: list[str]
    ) -> list[InvestmentRatio]:
        """여러 종목의 투자지표를 순차적으로 수집한다 (rate-limit 준수)."""
        results: list[InvestmentRatio] = []
        total = len(tickers)

        for idx, ticker in enumerate(tickers, 1):
            ratio = await self.fetch_stock_info(ticker)
            if ratio is not None:
                results.append(ratio)

            if idx % 100 == 0:
                logger.info(
                    "[%s] Progress: %d / %d tickers fetched (%d collected)",
                    self.source,
                    idx,
                    total,
                    len(results),
                )

        logger.info(
            "[%s] Batch complete: %d / %d tickers collected",
            self.source,
            len(results),
            total,
        )
        return results

    async def scrape(self) -> dict:
        """메인 수집 메서드. 외부에서 tickers를 주입받아 호출하는 구조.

        단독 호출 시 빈 결과를 반환한다. tickers를 설정하려면
        ``scrape_tickers``를 사용하라.
        """
        return {"ratios": []}

    async def scrape_tickers(self, tickers: list[str]) -> dict:
        """주어진 ticker 목록에 대해 투자지표를 수집하여 반환한다."""
        ratios = await self.fetch_batch(tickers)
        return {"ratios": [r.model_dump() for r in ratios]}
