from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timedelta

from krx_fundamentals_api.models.schemas import (
    InvestmentRatio,
    Market,
    SectorOverview,
)
from krx_fundamentals_api.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

OTP_URL = "http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd"
DOWNLOAD_URL = "http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd"
REFERER = "http://data.krx.co.kr/contents/MDC/MDI/mdiLoader"

MARKET_CODE = {
    Market.KOSPI: "STK",
    Market.KOSDAQ: "KSQ",
}


def _recent_business_day() -> str:
    """Return the most recent likely business day as YYYYMMDD."""
    today = datetime.now()
    weekday = today.weekday()
    if weekday == 5:  # Saturday
        today -= timedelta(days=1)
    elif weekday == 6:  # Sunday
        today -= timedelta(days=2)
    return today.strftime("%Y%m%d")


def _parse_float(value: str) -> float | None:
    if not value or value.strip() in ("", "-", "N/A"):
        return None
    try:
        return float(value.strip().replace(",", ""))
    except (ValueError, TypeError):
        return None


def _parse_int(value: str) -> int | None:
    if not value or value.strip() in ("", "-", "N/A"):
        return None
    try:
        return int(value.strip().replace(",", ""))
    except (ValueError, TypeError):
        return None


def _decode_csv(content: bytes) -> str:
    """Decode KRX CSV content, trying UTF-8 with BOM first, then cp949."""
    for encoding in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            return content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return content.decode("utf-8", errors="replace")


def _parse_csv_rows(text: str) -> tuple[list[str], list[list[str]]]:
    """Parse CSV text into (headers, rows). Returns empty lists on failure."""
    reader = csv.reader(io.StringIO(text.strip()))
    rows = list(reader)
    if len(rows) < 2:
        return [], []
    return rows[0], rows[1:]


class KrxScraper(BaseScraper):
    source = "krx"
    base_url = "http://data.krx.co.kr"
    min_delay = 1.0
    max_delay = 3.0
    timeout = 30.0

    # ------------------------------------------------------------------ #
    #  OTP two-step download
    # ------------------------------------------------------------------ #

    async def _get_otp(self, params: dict) -> str:
        """Step 1: request a one-time password token from KRX."""
        resp = await self.fetch_post(
            OTP_URL,
            data=params,
            headers={"Referer": REFERER},
        )
        otp = resp.text.strip()
        if not otp or len(otp) > 500:
            raise ValueError(f"Unexpected OTP response (len={len(otp)})")
        return otp

    async def _download_csv(self, otp: str) -> str:
        """Step 2: exchange the OTP for CSV data."""
        resp = await self.fetch_post(
            DOWNLOAD_URL,
            data={"code": otp},
            headers={"Referer": REFERER},
        )
        return _decode_csv(resp.content)

    # ------------------------------------------------------------------ #
    #  PER / PBR / 배당수익률
    # ------------------------------------------------------------------ #

    async def fetch_investment_ratios(
        self, market: Market, trd_dd: str | None = None,
    ) -> list[InvestmentRatio]:
        """PER/PBR/배당수익률 전종목 데이터를 수집한다."""
        date = trd_dd or _recent_business_day()
        mkt_id = MARKET_CODE.get(market)
        if mkt_id is None:
            logger.warning("[krx] Unsupported market for ratios: %s", market)
            return []

        params = {
            "locale": "ko_KR",
            "mktId": mkt_id,
            "trdDd": date,
            "share": "1",
            "money": "1",
            "csvxls_isNo": "false",
            "name": "fileDown",
            "url": "dbms/MDC/STAT/standard/MDCSTAT03501",
        }
        otp = await self._get_otp(params)
        text = await self._download_csv(otp)
        headers, rows = _parse_csv_rows(text)
        if not rows:
            logger.warning("[krx] No ratio data for %s on %s", market, date)
            return []

        col = {name: idx for idx, name in enumerate(headers)}
        results: list[InvestmentRatio] = []

        for row in rows:
            try:
                ticker = row[col["종목코드"]].strip()
                name = row[col["종목명"]].strip()
                results.append(
                    InvestmentRatio(
                        ticker=ticker,
                        name=name,
                        market=market,
                        price=_parse_float(row[col["종가"]]) if "종가" in col else None,
                        eps=_parse_float(row[col["EPS"]]) if "EPS" in col else None,
                        per=_parse_float(row[col["PER"]]) if "PER" in col else None,
                        bps=_parse_float(row[col["BPS"]]) if "BPS" in col else None,
                        pbr=_parse_float(row[col["PBR"]]) if "PBR" in col else None,
                        dividend_yield=(
                            _parse_float(row[col["배당수익률"]])
                            if "배당수익률" in col
                            else None
                        ),
                    ),
                )
            except (KeyError, IndexError) as e:
                logger.debug("[krx] Skipping malformed ratio row: %s", e)

        logger.info(
            "[krx] Fetched %d investment ratios for %s (%s)",
            len(results), market.value, date,
        )
        return results

    # ------------------------------------------------------------------ #
    #  시가총액
    # ------------------------------------------------------------------ #

    async def fetch_market_cap(
        self, market: Market, trd_dd: str | None = None,
    ) -> dict[str, float]:
        """전종목 시세에서 ticker → 시가총액(억원) 매핑을 반환한다."""
        date = trd_dd or _recent_business_day()
        mkt_id = MARKET_CODE.get(market)
        if mkt_id is None:
            logger.warning("[krx] Unsupported market for market-cap: %s", market)
            return {}

        params = {
            "locale": "ko_KR",
            "mktId": mkt_id,
            "trdDd": date,
            "share": "1",
            "money": "1",
            "csvxls_isNo": "false",
            "name": "fileDown",
            "url": "dbms/MDC/STAT/standard/MDCSTAT01501",
        }
        otp = await self._get_otp(params)
        text = await self._download_csv(otp)
        headers, rows = _parse_csv_rows(text)
        if not rows:
            logger.warning("[krx] No market-cap data for %s on %s", market, date)
            return {}

        col = {name: idx for idx, name in enumerate(headers)}
        cap_col = next(
            (c for c in ("시가총액", "시가총액(원)") if c in col),
            None,
        )
        if cap_col is None:
            logger.warning("[krx] 시가총액 column not found in headers: %s", headers)
            return {}

        mapping: dict[str, float] = {}
        for row in rows:
            try:
                ticker = row[col["종목코드"]].strip()
                raw = _parse_float(row[col[cap_col]])
                if raw is not None:
                    # KRX reports in 원; convert to 억원
                    mapping[ticker] = raw / 1_0000_0000
            except (KeyError, IndexError):
                continue

        logger.info(
            "[krx] Fetched market-cap for %d tickers in %s (%s)",
            len(mapping), market.value, date,
        )
        return mapping

    # ------------------------------------------------------------------ #
    #  업종별 시세 (Sector Overview)
    # ------------------------------------------------------------------ #

    async def fetch_sectors(
        self, trd_dd: str | None = None,
    ) -> list[SectorOverview]:
        """KSE 업종별 시세를 수집한다."""
        date = trd_dd or _recent_business_day()

        params = {
            "locale": "ko_KR",
            "indTpCd": "1",
            "trdDd": date,
            "csvxls_isNo": "false",
            "name": "fileDown",
            "url": "dbms/MDC/STAT/standard/MDCSTAT03901",
        }
        otp = await self._get_otp(params)
        text = await self._download_csv(otp)
        headers, rows = _parse_csv_rows(text)
        if not rows:
            logger.warning("[krx] No sector data for %s", date)
            return []

        col = {name: idx for idx, name in enumerate(headers)}
        results: list[SectorOverview] = []

        for row in rows:
            try:
                sector_name = row[col.get("업종명", 0)].strip()  # type: ignore[arg-type]
                if not sector_name:
                    continue
                results.append(
                    SectorOverview(
                        sector=sector_name,
                        total_market_cap=(
                            _parse_float(row[col["시가총액"]])
                            if "시가총액" in col
                            else None
                        ),
                    ),
                )
            except (KeyError, IndexError) as e:
                logger.debug("[krx] Skipping malformed sector row: %s", e)

        logger.info("[krx] Fetched %d sectors (%s)", len(results), date)
        return results

    # ------------------------------------------------------------------ #
    #  Merge market-cap into ratios
    # ------------------------------------------------------------------ #

    async def _enrich_ratios(
        self, ratios: list[InvestmentRatio], market: Market, trd_dd: str | None = None,
    ) -> list[InvestmentRatio]:
        """Attach market_cap values to ratio entries."""
        cap_map = await self.fetch_market_cap(market, trd_dd=trd_dd)
        for r in ratios:
            if r.ticker in cap_map:
                r.market_cap = cap_map[r.ticker]
        return ratios

    # ------------------------------------------------------------------ #
    #  Main entry point
    # ------------------------------------------------------------------ #

    async def scrape(self) -> dict:
        """Collect PER/PBR/시가총액 for KOSPI+KOSDAQ and sector data."""
        trd_dd = _recent_business_day()
        all_ratios: list[InvestmentRatio] = []

        for market in (Market.KOSPI, Market.KOSDAQ):
            ratios = await self.fetch_investment_ratios(market, trd_dd=trd_dd)
            ratios = await self._enrich_ratios(ratios, market, trd_dd=trd_dd)
            all_ratios.extend(ratios)

        sectors = await self.fetch_sectors(trd_dd=trd_dd)

        logger.info(
            "[krx] Scrape complete: %d ratios, %d sectors",
            len(all_ratios), len(sectors),
        )
        return {"ratios": all_ratios, "sectors": sectors}
