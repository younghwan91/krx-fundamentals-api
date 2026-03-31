"""KRX Fundamentals API 포트폴리오 분석 예제.

여러 종목으로 구성된 포트폴리오를 비동기 병렬 요청으로 분석하는 예제입니다.
투자 지표 평균(PER, PBR, ROE), 배당 정보, 시장 평균 대비 비교를
수행하고 포맷된 요약 테이블을 출력합니다.

사용법:
    pip install httpx
    python examples/portfolio_analysis.py
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass

import httpx

BASE_URL = "http://localhost:8010/api/v1"
TIMEOUT = 15.0

# 분석할 포트폴리오
PORTFOLIO: list[tuple[str, str]] = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("035420", "NAVER"),
    ("035720", "카카오"),
    ("005380", "현대차"),
]


@dataclass
class StockData:
    """종목별 수집 데이터."""

    ticker: str
    name: str
    ratio: dict | None = None
    dividends: list[dict] | None = None
    error: str | None = None


def print_header(title: str) -> None:
    print(f"\n{'=' * 76}")
    print(f"  {title}")
    print(f"{'=' * 76}")


def print_table(headers: list[str], rows: list[list[str]], widths: list[int]) -> None:
    """테이블 포맷 출력."""
    header_line = " | ".join(h.center(w) for h, w in zip(headers, widths))
    separator = "-+-".join("-" * w for w in widths)

    print(f"  {header_line}")
    print(f"  {separator}")
    for row in rows:
        line = " | ".join(
            str(v).rjust(w) if i > 0 else str(v).ljust(w)
            for i, (v, w) in enumerate(zip(row, widths))
        )
        print(f"  {line}")


def fmt(value: float | None, suffix: str = "", decimal: int = 2) -> str:
    if value is None:
        return "-"
    return f"{value:,.{decimal}f}{suffix}"


async def fetch_stock_data(
    client: httpx.AsyncClient,
    ticker: str,
    name: str,
) -> StockData:
    """종목의 투자 지표와 배당 정보를 병렬로 수집."""
    stock = StockData(ticker=ticker, name=name)

    try:
        ratio_resp, div_resp = await asyncio.gather(
            client.get(f"{BASE_URL}/companies/{ticker}/ratios"),
            client.get(f"{BASE_URL}/companies/{ticker}/dividends"),
        )

        if ratio_resp.status_code == 200:
            stock.ratio = ratio_resp.json()
        else:
            stock.error = f"지표 조회 실패 ({ratio_resp.status_code})"

        if div_resp.status_code == 200:
            stock.dividends = div_resp.json().get("dividends", [])

    except httpx.HTTPError as e:
        stock.error = str(e)

    return stock


async def fetch_market_averages(client: httpx.AsyncClient) -> dict | None:
    """시장 섹터 평균 데이터 조회."""
    try:
        resp = await client.get(f"{BASE_URL}/market/sectors")
        if resp.status_code == 200:
            return resp.json()
    except httpx.HTTPError:
        pass
    return None


def display_ratio_table(stocks: list[StockData]) -> None:
    """투자 지표 요약 테이블."""
    print_header("📊 포트폴리오 투자 지표")

    headers = ["종목명", "현재가", "시가총액", "PER", "PBR", "ROE", "배당률", "외국인"]
    widths = [10, 10, 10, 8, 8, 8, 8, 8]
    rows = []

    for s in stocks:
        r = s.ratio or {}
        rows.append([
            s.name[:10],
            fmt(r.get("price"), "원", 0),
            fmt(r.get("market_cap"), "억", 0),
            fmt(r.get("per"), ""),
            fmt(r.get("pbr"), ""),
            fmt(r.get("roe"), "%"),
            fmt(r.get("dividend_yield"), "%"),
            fmt(r.get("foreign_ratio"), "%"),
        ])

    print_table(headers, rows, widths)


def display_valuation_detail(stocks: list[StockData]) -> None:
    """밸류에이션 상세 테이블."""
    print_header("💡 밸류에이션 상세")

    headers = ["종목명", "EPS", "BPS", "영업이익률", "순이익률", "부채비율"]
    widths = [10, 10, 12, 10, 10, 10]
    rows = []

    for s in stocks:
        r = s.ratio or {}
        rows.append([
            s.name[:10],
            fmt(r.get("eps"), "원", 0),
            fmt(r.get("bps"), "원", 0),
            fmt(r.get("operating_margin"), "%"),
            fmt(r.get("net_margin"), "%"),
            fmt(r.get("debt_ratio"), "%"),
        ])

    print_table(headers, rows, widths)


def display_price_range(stocks: list[StockData]) -> None:
    """52주 가격 범위."""
    print_header("📈 52주 가격 범위")

    headers = ["종목명", "현재가", "52주 최저", "52주 최고", "위치"]
    widths = [10, 12, 12, 12, 10]
    rows = []

    for s in stocks:
        r = s.ratio or {}
        price = r.get("price")
        low = r.get("low_52w")
        high = r.get("high_52w")

        if price and low and high and high > low:
            position_pct = (price - low) / (high - low) * 100
            position_str = f"{position_pct:.1f}%"
        else:
            position_str = "-"

        rows.append([
            s.name[:10],
            fmt(price, "원", 0),
            fmt(low, "원", 0),
            fmt(high, "원", 0),
            position_str,
        ])

    print_table(headers, rows, widths)


def display_dividend_history(stocks: list[StockData]) -> None:
    """배당 이력."""
    print_header("💰 배당 이력")

    for s in stocks:
        if not s.dividends:
            print(f"\n  {s.name} ({s.ticker}): 배당 데이터 없음")
            continue

        print(f"\n  {s.name} ({s.ticker}):")
        for div in s.dividends[:3]:
            dps = fmt(div.get("dividend_per_share"), "원", 0)
            dy = fmt(div.get("dividend_yield"), "%")
            pr = fmt(div.get("payout_ratio"), "%")
            print(f"    {div.get('year', '-')}년: 주당 {dps} | 수익률 {dy} | 배당성향 {pr}")


def calculate_portfolio_averages(stocks: list[StockData]) -> dict[str, float | None]:
    """포트폴리오 평균 지표 계산."""
    metrics = [
        "per", "pbr", "roe", "roa",
        "dividend_yield", "debt_ratio", "operating_margin", "net_margin",
    ]
    averages: dict[str, float | None] = {}

    for metric in metrics:
        values = [
            s.ratio[metric]
            for s in stocks
            if s.ratio and s.ratio.get(metric) is not None
        ]
        averages[metric] = sum(values) / len(values) if values else None

    # 포트폴리오 전체 시가총액
    caps = [
        s.ratio["market_cap"]
        for s in stocks
        if s.ratio and s.ratio.get("market_cap") is not None
    ]
    averages["total_market_cap"] = sum(caps) if caps else None

    return averages


def display_portfolio_summary(
    stocks: list[StockData],
    averages: dict[str, float | None],
    market_data: dict | None,
) -> None:
    """포트폴리오 요약 및 시장 비교."""
    print_header("📋 포트폴리오 요약")

    valid = [s for s in stocks if s.ratio]
    failed = [s for s in stocks if s.error]

    print(f"  구성 종목: {len(PORTFOLIO)}개 (조회 성공: {len(valid)}개)")
    if averages.get("total_market_cap") is not None:
        print(f"  총 시가총액: {averages['total_market_cap']:,.0f}억원")

    print(f"\n  {'지표':>12}  {'포트폴리오':>12}  {'시장 평균':>12}  {'비교':>8}")
    print(f"  {'-' * 12}  {'-' * 12}  {'-' * 12}  {'-' * 8}")

    # 시장 평균 계산
    sector_avgs: dict[str, float | None] = {}
    if market_data and market_data.get("sectors"):
        sectors = market_data["sectors"]
        for key in ["avg_per", "avg_pbr", "avg_dividend_yield"]:
            values = [s[key] for s in sectors if s.get(key) is not None]
            sector_avgs[key] = sum(values) / len(values) if values else None

    comparisons = [
        ("PER", averages.get("per"), sector_avgs.get("avg_per"), "배", True),
        ("PBR", averages.get("pbr"), sector_avgs.get("avg_pbr"), "배", True),
        ("ROE", averages.get("roe"), None, "%", False),
        ("ROA", averages.get("roa"), None, "%", False),
        (
            "배당수익률", averages.get("dividend_yield"),
            sector_avgs.get("avg_dividend_yield"), "%", False,
        ),
        ("부채비율", averages.get("debt_ratio"), None, "%", True),
        ("영업이익률", averages.get("operating_margin"), None, "%", False),
        ("순이익률", averages.get("net_margin"), None, "%", False),
    ]

    for label, port_val, mkt_val, unit, lower_is_better in comparisons:
        p_str = f"{port_val:.2f}{unit}" if port_val is not None else "-"
        m_str = f"{mkt_val:.2f}{unit}" if mkt_val is not None else "-"

        if port_val is not None and mkt_val is not None:
            diff = port_val - mkt_val
            if lower_is_better:
                indicator = "✅" if diff < 0 else "⚠️"
            else:
                indicator = "✅" if diff > 0 else "⚠️"
        else:
            indicator = "  "

        print(f"  {label:>12}  {p_str:>12}  {m_str:>12}  {indicator:>8}")

    if failed:
        print("\n  ⚠️ 조회 실패 종목:")
        for s in failed:
            print(f"    {s.ticker} {s.name}: {s.error}")


async def main() -> None:
    print("🇰🇷 KRX Fundamentals API - 포트폴리오 분석 예제")
    print(f"   서버: {BASE_URL}")
    print(f"   종목: {', '.join(name for _, name in PORTFOLIO)}")

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # 모든 종목 데이터와 시장 데이터를 병렬로 수집
            tasks = [
                fetch_stock_data(client, ticker, name)
                for ticker, name in PORTFOLIO
            ]
            tasks.append(fetch_market_averages(client))  # type: ignore[arg-type]

            results = await asyncio.gather(*tasks)

            stocks: list[StockData] = list(results[:-1])  # type: ignore[arg-type]
            market_data: dict | None = results[-1]  # type: ignore[assignment]

            # 투자 지표 테이블
            display_ratio_table(stocks)

            # 밸류에이션 상세
            display_valuation_detail(stocks)

            # 52주 가격 범위
            display_price_range(stocks)

            # 배당 이력
            display_dividend_history(stocks)

            # 포트폴리오 평균 계산
            averages = calculate_portfolio_averages(stocks)

            # 포트폴리오 요약 및 시장 비교
            display_portfolio_summary(stocks, averages, market_data)

    except httpx.ConnectError:
        print("\n❌ 서버에 연결할 수 없습니다.")
        print("   docker-compose up 으로 서버를 먼저 실행하세요.")
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP 오류: {e.response.status_code}")
        print(f"   {e.response.text}")
        sys.exit(1)

    print(f"\n{'=' * 76}")
    print("  ✅ 포트폴리오 분석 완료!")
    print(f"{'=' * 76}")


if __name__ == "__main__":
    asyncio.run(main())
