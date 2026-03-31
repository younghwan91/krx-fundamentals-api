from __future__ import annotations

from krx_fundamentals_api.models.schemas import (
    Company,
    Dividend,
    Executive,
    FinancialStatement,
    InvestmentRatio,
    Market,
    ReportType,
    SectorOverview,
    Shareholder,
)
from krx_fundamentals_api.services.cache import (
    cache_companies,
    cache_dividends,
    cache_executives,
    cache_financials,
    cache_ratios,
    cache_sectors,
    cache_shareholders,
)

# --- Health ---


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# --- Companies ---


async def test_list_companies_empty(client):
    resp = await client.get("/api/v1/companies")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["has_next"] is False


async def test_list_companies_with_data(client):
    company = Company(ticker="005930", name="삼성전자", market=Market.KOSPI, sector="반도체")
    await cache_companies([company])

    resp = await client.get("/api/v1/companies")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["ticker"] == "005930"


async def test_list_companies_search(client):
    c1 = Company(ticker="005930", name="삼성전자", market=Market.KOSPI)
    c2 = Company(ticker="000660", name="SK하이닉스", market=Market.KOSPI)
    await cache_companies([c1, c2])

    resp = await client.get("/api/v1/companies", params={"q": "삼성"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "삼성전자"


async def test_list_companies_pagination(client):
    companies = [Company(ticker=f"{i:06d}", name=f"Company{i}") for i in range(5)]
    await cache_companies(companies)

    resp = await client.get("/api/v1/companies", params={"page": 1, "page_size": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["has_next"] is True


async def test_get_company_not_found(client):
    resp = await client.get("/api/v1/companies/999999")
    assert resp.status_code == 404


async def test_get_company_found(client):
    company = Company(ticker="005930", name="삼성전자", market=Market.KOSPI, sector="반도체")
    await cache_companies([company])

    resp = await client.get("/api/v1/companies/005930")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "005930"
    assert data["name"] == "삼성전자"


# --- Financials ---


async def test_get_financials_empty(client):
    resp = await client.get("/api/v1/companies/005930/financials")
    assert resp.status_code == 200
    data = resp.json()
    assert data["statements"] == []
    assert data["total"] == 0


async def test_get_financials_with_data(client):
    fs = FinancialStatement(
        ticker="005930",
        year=2024,
        report_type=ReportType.ANNUAL,
        revenue=302231000.0,
    )
    await cache_financials("005930", [fs])

    resp = await client.get("/api/v1/companies/005930/financials")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["statements"][0]["revenue"] == 302231000.0


# --- Ratios ---


async def test_get_ratios_not_found(client):
    resp = await client.get("/api/v1/companies/999999/ratios")
    assert resp.status_code == 404


async def test_get_ratios_found(client):
    ratio = InvestmentRatio(
        ticker="005930", name="삼성전자", market=Market.KOSPI, per=12.5, pbr=1.3
    )
    await cache_ratios([ratio])

    resp = await client.get("/api/v1/companies/005930/ratios")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "005930"
    assert data["per"] == 12.5


# --- Dividends ---


async def test_get_dividends_empty(client):
    resp = await client.get("/api/v1/companies/005930/dividends")
    assert resp.status_code == 200
    data = resp.json()
    assert data["dividends"] == []


async def test_get_dividends_with_data(client):
    div = Dividend(ticker="005930", year=2024, dividend_per_share=1444.0)
    await cache_dividends("005930", [div])

    resp = await client.get("/api/v1/companies/005930/dividends")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


# --- Shareholders ---


async def test_get_shareholders_empty(client):
    resp = await client.get("/api/v1/companies/005930/shareholders")
    assert resp.status_code == 200
    assert resp.json()["shareholders"] == []


async def test_get_shareholders_with_data(client):
    sh = Shareholder(ticker="005930", name="이재용", shares=969420, ownership_pct=0.58)
    await cache_shareholders("005930", [sh])

    resp = await client.get("/api/v1/companies/005930/shareholders")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


# --- Executives ---


async def test_get_executives_empty(client):
    resp = await client.get("/api/v1/companies/005930/executives")
    assert resp.status_code == 200
    assert resp.json()["executives"] == []


async def test_get_executives_with_data(client):
    ex = Executive(ticker="005930", name="한종희", position="대표이사", is_registered=True)
    await cache_executives("005930", [ex])

    resp = await client.get("/api/v1/companies/005930/executives")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


# --- Market ---


async def test_market_overview(client):
    resp = await client.get("/api/v1/market/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert "sectors" in data
    assert "crawler_status" in data


async def test_market_sectors_empty(client):
    resp = await client.get("/api/v1/market/sectors")
    assert resp.status_code == 200
    data = resp.json()
    assert data["sectors"] == []
    assert data["total"] == 0


async def test_market_sectors_with_data(client):
    sectors = [SectorOverview(sector="반도체", company_count=15)]
    await cache_sectors(sectors)

    resp = await client.get("/api/v1/market/sectors")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


# --- Ranking ---


async def test_ranking_empty(client):
    resp = await client.get("/api/v1/ranking/market_cap")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


async def test_ranking_with_data(client):
    r1 = InvestmentRatio(ticker="005930", name="삼성전자", market_cap=5000000)
    r2 = InvestmentRatio(ticker="000660", name="SK하이닉스", market_cap=1500000)
    await cache_ratios([r1, r2])

    resp = await client.get("/api/v1/ranking/market_cap")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert data["items"][0]["ticker"] == "005930"


async def test_ranking_invalid_metric(client):
    resp = await client.get("/api/v1/ranking/invalid_metric")
    assert resp.status_code == 422


# --- Screening ---


async def test_screening_empty(client):
    resp = await client.get("/api/v1/screening")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []


async def test_screening_with_filters(client):
    r1 = InvestmentRatio(ticker="005930", per=12.5, pbr=1.3, market=Market.KOSPI)
    r2 = InvestmentRatio(ticker="000660", per=25.0, pbr=3.0, market=Market.KOSPI)
    await cache_ratios([r1, r2])

    resp = await client.get("/api/v1/screening", params={"per_max": 15.0})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["ticker"] == "005930"


# --- Status ---


async def test_status(client):
    resp = await client.get("/api/v1/status")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
