from __future__ import annotations

from datetime import datetime

from krx_fundamentals_api.models.schemas import (
    Company,
    CrawlerStatus,
    DataSource,
    Dividend,
    Executive,
    FinancialStatement,
    InvestmentRatio,
    Market,
    PaginatedResponse,
    RankingMetric,
    ReportType,
    SectorOverview,
    Shareholder,
)


async def test_company_all_fields():
    company = Company(
        ticker="005930",
        corp_code="00126380",
        name="삼성전자",
        name_en="Samsung Electronics",
        market=Market.KOSPI,
        sector="반도체",
        industry="전자부품",
        ceo="한종희",
        address="경기도 수원시",
        phone="031-200-1114",
        website="www.samsung.com",
        ir_url="https://www.samsung.com/ir",
        established_date="19690113",
        listing_date="19750611",
        fiscal_month=12,
    )
    assert company.ticker == "005930"
    assert company.name == "삼성전자"
    assert company.market == Market.KOSPI
    assert company.fiscal_month == 12
    assert company.corp_code == "00126380"


async def test_company_minimal():
    company = Company(ticker="005930", name="삼성전자")
    assert company.corp_code == ""
    assert company.market is None
    assert company.sector == ""
    assert company.fiscal_month == 12
    assert isinstance(company.updated_at, datetime)


async def test_financial_statement_optional_fields():
    fs = FinancialStatement(ticker="005930", year=2024, report_type=ReportType.ANNUAL)
    assert fs.revenue is None
    assert fs.operating_income is None
    assert fs.total_assets is None
    assert fs.currency == "KRW"
    assert isinstance(fs.collected_at, datetime)


async def test_financial_statement_with_values():
    fs = FinancialStatement(
        ticker="005930",
        year=2024,
        report_type=ReportType.ANNUAL,
        revenue=302231000.0,
        operating_income=36835300.0,
        net_income=23451800.0,
        total_assets=426000000.0,
        total_liabilities=121000000.0,
        total_equity=305000000.0,
    )
    assert fs.revenue == 302231000.0
    assert fs.total_equity == 305000000.0


async def test_investment_ratio_none_values():
    ratio = InvestmentRatio(ticker="005930")
    assert ratio.per is None
    assert ratio.pbr is None
    assert ratio.roe is None
    assert ratio.market_cap is None
    assert ratio.price is None
    assert ratio.volume is None
    assert ratio.name == ""


async def test_investment_ratio_with_values():
    ratio = InvestmentRatio(
        ticker="005930",
        name="삼성전자",
        market=Market.KOSPI,
        per=12.5,
        pbr=1.3,
        roe=15.0,
        market_cap=5000000.0,
        dividend_yield=2.1,
    )
    assert ratio.per == 12.5
    assert ratio.market == Market.KOSPI
    assert ratio.dividend_yield == 2.1


async def test_dividend_creation():
    div = Dividend(
        ticker="005930",
        year=2024,
        dividend_per_share=1444.0,
        dividend_yield=2.1,
        payout_ratio=25.0,
    )
    assert div.ticker == "005930"
    assert div.dividend_per_share == 1444.0
    assert div.year == 2024
    assert div.ex_dividend_date == ""


async def test_shareholder_creation():
    sh = Shareholder(ticker="005930", name="이재용", shares=969420, ownership_pct=0.58)
    assert sh.name == "이재용"
    assert sh.shares == 969420
    assert sh.ownership_pct == 0.58
    assert sh.change_shares == 0


async def test_executive_creation():
    ex = Executive(
        ticker="005930",
        name="한종희",
        position="대표이사",
        role="경영총괄",
        is_registered=True,
    )
    assert ex.name == "한종희"
    assert ex.is_registered is True
    assert ex.birth_year == ""
    assert ex.gender == ""


async def test_paginated_response():
    resp = PaginatedResponse(items=["a", "b", "c"], total=10, page=1, page_size=3, has_next=True)
    assert len(resp.items) == 3
    assert resp.total == 10
    assert resp.has_next is True
    assert resp.page == 1


async def test_data_source_enum():
    assert DataSource.DART == "dart"
    assert DataSource.KRX == "krx"
    assert DataSource.NAVER == "naver"
    assert len(DataSource) == 3


async def test_market_enum():
    assert Market.KOSPI == "kospi"
    assert Market.KOSDAQ == "kosdaq"
    assert Market.KONEX == "konex"


async def test_report_type_enum():
    assert ReportType.ANNUAL == "annual"
    assert ReportType.HALF == "half"
    assert ReportType.Q1 == "q1"
    assert ReportType.Q3 == "q3"


async def test_ranking_metric_enum():
    assert RankingMetric.MARKET_CAP == "market_cap"
    assert RankingMetric.PER == "per"
    assert RankingMetric.PBR == "pbr"
    assert RankingMetric.ROE == "roe"
    assert RankingMetric.DIVIDEND_YIELD == "dividend_yield"
    assert RankingMetric.REVENUE == "revenue"
    assert RankingMetric.NET_INCOME == "net_income"


async def test_sector_overview():
    sector = SectorOverview(
        sector="반도체",
        company_count=15,
        total_market_cap=500000.0,
        avg_per=12.5,
    )
    assert sector.sector == "반도체"
    assert sector.company_count == 15
    assert sector.avg_pbr is None
    assert sector.avg_dividend_yield is None


async def test_crawler_status_defaults():
    status = CrawlerStatus(source=DataSource.DART)
    assert status.source == DataSource.DART
    assert status.job_name == ""
    assert status.items_count == 0
    assert status.is_healthy is True
    assert status.error is None
    assert status.last_crawled_at is None
