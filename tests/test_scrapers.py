from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from krx_fundamentals_api.models.schemas import DataSource, Market
from krx_fundamentals_api.scrapers.base import BaseScraper
from krx_fundamentals_api.scrapers.dart import DartScraper
from krx_fundamentals_api.scrapers.krx import KrxScraper
from krx_fundamentals_api.scrapers.naver import NaverScraper


async def test_dart_scraper_init():
    scraper = DartScraper()
    assert scraper.source == "dart"
    assert scraper.base_url == "https://opendart.fss.or.kr/api"
    assert scraper._corp_map == {}
    assert scraper._client is None


async def test_dart_check_api_key_empty():
    scraper = DartScraper()
    with patch("krx_fundamentals_api.scrapers.dart.settings") as mock_settings:
        mock_settings.dart_api_key = ""
        assert scraper._check_api_key() is False


async def test_dart_check_api_key_set():
    scraper = DartScraper()
    with patch("krx_fundamentals_api.scrapers.dart.settings") as mock_settings:
        mock_settings.dart_api_key = "test_key_12345"
        assert scraper._check_api_key() is True


async def test_dart_fetch_company_no_api_key():
    scraper = DartScraper()
    with patch("krx_fundamentals_api.scrapers.dart.settings") as mock_settings:
        mock_settings.dart_api_key = ""
        result = await scraper.fetch_company("005930")
    assert result is None


async def test_dart_fetch_company_with_mock():
    scraper = DartScraper()
    scraper._corp_map = {"005930": "00126380"}

    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "status": "000",
        "corp_name": "삼성전자",
        "corp_name_eng": "Samsung Electronics",
        "corp_cls": "Y",
        "ceo_nm": "한종희",
        "adres": "경기도 수원시",
        "hm_url": "www.samsung.com",
        "ir_url": "https://www.samsung.com/ir",
        "est_dt": "19690113",
        "acc_mt": "12",
    }

    with patch("krx_fundamentals_api.scrapers.dart.settings") as mock_settings:
        mock_settings.dart_api_key = "test_key"
        scraper.fetch = AsyncMock(return_value=mock_resp)
        company = await scraper.fetch_company("005930")

    assert company is not None
    assert company.ticker == "005930"
    assert company.name == "삼성전자"
    assert company.market == Market.KOSPI
    assert company.ceo == "한종희"
    assert company.fiscal_month == 12


async def test_krx_scraper_init():
    scraper = KrxScraper()
    assert scraper.source == "krx"
    assert scraper.base_url == "http://data.krx.co.kr"
    assert scraper.timeout == 30.0
    assert scraper.min_delay == 1.0


async def test_naver_scraper_init():
    scraper = NaverScraper()
    assert scraper.source == DataSource.NAVER
    assert scraper.base_url == "https://m.stock.naver.com/api"
    assert scraper._client is None


async def test_base_scraper_make_id_deterministic():
    id1 = BaseScraper.make_id("dart", "005930")
    id2 = BaseScraper.make_id("dart", "005930")
    assert id1 == id2
    assert id1.startswith("dart:")
    assert len(id1) == len("dart:") + 12


async def test_base_scraper_make_id_unique():
    id1 = BaseScraper.make_id("dart", "005930")
    id2 = BaseScraper.make_id("dart", "000660")
    id3 = BaseScraper.make_id("krx", "005930")
    assert id1 != id2
    assert id1 != id3
