"""Scheduler bootstrap ordering.

2026-07-06: crawl_companies/financials/dividends were only wired to a 24h
interval with no immediate trigger (unlike corp_codes/krx_ratios, which had
a "(초기)" one-shot job). On a fresh deploy this meant zero company/financial
data for a full day, and even a manual trigger produced 0 items because
crawl_companies falls back to a corp_map that's only populated once
crawl_corp_codes has run. These tests lock in the fix: a single
bootstrap_dart_chain() that runs the chain in dependency order, and a
defensive fallback in crawl_companies() so it's not order-dependent either.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from krx_fundamentals_api.services import scheduler


async def test_bootstrap_dart_chain_runs_in_dependency_order():
    calls: list[str] = []

    with (
        patch.object(
            scheduler,
            "crawl_corp_codes",
            AsyncMock(side_effect=lambda: calls.append("corp_codes")),
        ),
        patch.object(
            scheduler,
            "crawl_companies",
            AsyncMock(side_effect=lambda: calls.append("companies")),
        ),
        patch.object(
            scheduler,
            "crawl_financials_sample",
            AsyncMock(side_effect=lambda: calls.append("financials")),
        ),
        patch.object(
            scheduler,
            "crawl_dividends_sample",
            AsyncMock(side_effect=lambda: calls.append("dividends")),
        ),
    ):
        await scheduler.bootstrap_dart_chain()

    assert calls == ["corp_codes", "companies", "financials", "dividends"]


async def test_crawl_companies_loads_corp_codes_when_map_empty():
    """Must not silently produce 0 tickers just because corp_codes hasn't run yet."""
    with (
        patch.object(scheduler, "get_all_companies", AsyncMock(return_value=[])),
        patch.object(scheduler._dart, "get_corp_map", return_value={}),
        patch.object(
            scheduler._dart, "load_corp_codes", AsyncMock(return_value={"005930": "00126380"})
        ) as mock_load,
        patch.object(scheduler._dart, "fetch_company", AsyncMock(return_value=None)),
        patch.object(scheduler, "update_crawler_status", AsyncMock()),
    ):
        await scheduler.crawl_companies()

    mock_load.assert_called_once()
