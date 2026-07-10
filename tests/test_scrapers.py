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


_MDCSTAT01501_CSV = (
    '"종목코드","종목명","시장구분","소속부","종가","대비","등락률",'
    '"시가","고가","저가","거래량","거래대금","시가총액","상장주식수"\n'
    '"005930","삼성전자","KOSPI","-","70000","0","0.00",'
    '"70000","70000","70000","1000","70000000","417000000000000","5969782550"\n'
    '"000660","SK하이닉스","KOSPI","-","150000","0","0.00",'
    '"150000","150000","150000","500","75000000","109000000000000","728002365"\n'
)


async def test_krx_fetch_listed_shares_parses_shares():
    scraper = KrxScraper()
    scraper._get_otp = AsyncMock(return_value="otp-token")
    scraper._download_csv = AsyncMock(return_value=_MDCSTAT01501_CSV)

    shares = await scraper.fetch_listed_shares(Market.KOSPI, trd_dd="20260703")

    assert shares["005930"] == 5969782550
    assert shares["000660"] == 728002365


async def test_krx_fetch_listed_shares_empty_on_no_rows():
    scraper = KrxScraper()
    scraper._get_otp = AsyncMock(return_value="otp-token")
    scraper._download_csv = AsyncMock(return_value="")

    assert await scraper.fetch_listed_shares(Market.KOSPI) == {}


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
