"""KRX Fundamentals API 종목 스크리닝 예제.

다양한 투자 전략별 종목 스크리닝을 수행하는 고급 예제입니다.
가치주, 배당주, 성장주 필터링을 비동기 병렬 요청으로 실행하고
결과를 비교·분석하여 테이블 형태로 출력합니다.

사용법:
    pip install httpx
    python examples/screening.py
"""

from __future__ import annotations

import asyncio
import sys

import httpx

BASE_URL = "http://localhost:8010/api/v1"
TIMEOUT = 15.0


def print_header(title: str) -> None:
    print(f"\n{'=' * 72}")
    print(f"  {title}")
    print(f"{'=' * 72}")


def print_table(headers: list[str], rows: list[list[str]], widths: list[int]) -> None:
    """간단한 테이블 포맷으로 출력."""
    header_line = " | ".join(h.center(w) for h, w in zip(headers, widths))
    separator = "-+-".join("-" * w for w in widths)

    print(f"  {header_line}")
    print(f"  {separator}")
    for row in rows:
        cells = (
            str(v).rjust(w) if i > 0 else str(v).ljust(w)
            for i, (v, w) in enumerate(zip(row, widths))
        )
        print(f"  {' | '.join(cells)}")


def fmt(value: float | None, suffix: str = "", decimal: int = 2) -> str:
    if value is None:
        return "-"
    return f"{value:,.{decimal}f}{suffix}"


async def screen_value_stocks(client: httpx.AsyncClient) -> list[dict]:
    """가치주 스크리닝: 낮은 PER + 낮은 PBR."""
    resp = await client.get(
        f"{BASE_URL}/screening",
        params={
            "market": "kospi",
            "per_min": 0.1,
            "per_max": 10,
            "pbr_min": 0.1,
            "pbr_max": 1.0,
            "page_size": 20,
        },
    )
    resp.raise_for_status()
    return resp.json().get("items", [])


async def screen_dividend_stocks(client: httpx.AsyncClient) -> list[dict]:
    """배당주 스크리닝: 높은 배당수익률."""
    resp = await client.get(
        f"{BASE_URL}/screening",
        params={
            "dividend_yield_min": 4.0,
            "page_size": 20,
        },
    )
    resp.raise_for_status()
    return resp.json().get("items", [])


async def screen_growth_stocks(client: httpx.AsyncClient) -> list[dict]:
    """성장주 스크리닝: 높은 ROE."""
    resp = await client.get(
        f"{BASE_URL}/screening",
        params={
            "roe_min": 15,
            "market_cap_min": 1000,
            "page_size": 20,
        },
    )
    resp.raise_for_status()
    return resp.json().get("items", [])


async def get_ranking(
    client: httpx.AsyncClient, metric: str, ascending: bool = False,
) -> list[dict]:
    """지표별 랭킹 조회."""
    resp = await client.get(
        f"{BASE_URL}/ranking/{metric}",
        params={"page_size": 10, "ascending": ascending},
    )
    resp.raise_for_status()
    return resp.json().get("items", [])


def display_screening_results(title: str, emoji: str, stocks: list[dict]) -> None:
    """스크리닝 결과를 테이블로 출력."""
    print_header(f"{emoji} {title}")

    if not stocks:
        print("  결과 없음")
        return

    print(f"  총 {len(stocks)}종목 발견\n")

    headers = ["종목코드", "종목명", "시장", "PER", "PBR", "ROE", "배당률", "시가총액"]
    widths = [8, 14, 6, 8, 8, 8, 8, 12]
    rows = []

    for s in stocks[:15]:
        rows.append([
            s.get("ticker", "-"),
            s.get("name", "-")[:14],
            (s.get("market") or "-").upper(),
            fmt(s.get("per"), "배"),
            fmt(s.get("pbr"), "배"),
            fmt(s.get("roe"), "%"),
            fmt(s.get("dividend_yield"), "%"),
            fmt(s.get("market_cap"), "억", 0),
        ])

    print_table(headers, rows, widths)


def display_ranking(title: str, metric_key: str, unit: str, stocks: list[dict]) -> None:
    """랭킹 결과를 출력."""
    print_header(f"🏆 {title} TOP 10")

    if not stocks:
        print("  결과 없음")
        return

    headers = ["순위", "종목코드", "종목명", metric_key.upper(), "시장"]
    widths = [4, 8, 14, 12, 6]
    rows = []

    for i, s in enumerate(stocks[:10], 1):
        rows.append([
            str(i),
            s.get("ticker", "-"),
            s.get("name", "-")[:14],
            fmt(s.get(metric_key), unit),
            (s.get("market") or "-").upper(),
        ])

    print_table(headers, rows, widths)


def compare_strategies(
    value_stocks: list[dict],
    dividend_stocks: list[dict],
    growth_stocks: list[dict],
) -> None:
    """전략별 결과 비교."""
    print_header("📊 전략별 비교 요약")

    def avg(stocks: list[dict], key: str) -> float | None:
        values = [s[key] for s in stocks if s.get(key) is not None]
        return sum(values) / len(values) if values else None

    strategies = [
        ("가치주 (저PER·저PBR)", value_stocks),
        ("배당주 (고배당)", dividend_stocks),
        ("성장주 (고ROE)", growth_stocks),
    ]

    headers = ["전략", "종목수", "평균PER", "평균PBR", "평균ROE", "평균배당률"]
    widths = [22, 6, 10, 10, 10, 10]
    rows = []

    for name, stocks in strategies:
        rows.append([
            name,
            str(len(stocks)),
            fmt(avg(stocks, "per"), "배"),
            fmt(avg(stocks, "pbr"), "배"),
            fmt(avg(stocks, "roe"), "%"),
            fmt(avg(stocks, "dividend_yield"), "%"),
        ])

    print_table(headers, rows, widths)

    # 중복 종목 분석
    value_tickers = {s["ticker"] for s in value_stocks}
    dividend_tickers = {s["ticker"] for s in dividend_stocks}
    growth_tickers = {s["ticker"] for s in growth_stocks}

    vd_overlap = value_tickers & dividend_tickers
    vg_overlap = value_tickers & growth_tickers
    dg_overlap = dividend_tickers & growth_tickers
    all_overlap = value_tickers & dividend_tickers & growth_tickers

    print("\n  🔗 전략 간 중복 종목:")
    print(f"    가치 ∩ 배당: {len(vd_overlap)}종목", end="")
    if vd_overlap:
        print(f" → {', '.join(sorted(vd_overlap)[:5])}", end="")
    print()
    print(f"    가치 ∩ 성장: {len(vg_overlap)}종목", end="")
    if vg_overlap:
        print(f" → {', '.join(sorted(vg_overlap)[:5])}", end="")
    print()
    print(f"    배당 ∩ 성장: {len(dg_overlap)}종목", end="")
    if dg_overlap:
        print(f" → {', '.join(sorted(dg_overlap)[:5])}", end="")
    print()
    if all_overlap:
        print(f"    ⭐ 3가지 전략 모두 충족: {', '.join(sorted(all_overlap))}")


async def main() -> None:
    print("🇰🇷 KRX Fundamentals API - 종목 스크리닝 예제")
    print(f"   서버: {BASE_URL}")

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # 병렬로 3가지 스크리닝 + 2가지 랭킹 실행
            (
                value_stocks,
                dividend_stocks,
                growth_stocks,
                per_ranking,
                roe_ranking,
            ) = await asyncio.gather(
                screen_value_stocks(client),
                screen_dividend_stocks(client),
                screen_growth_stocks(client),
                get_ranking(client, "per", ascending=True),
                get_ranking(client, "roe", ascending=False),
            )

            # 스크리닝 결과 출력
            display_screening_results("가치주 스크리닝 (PER < 10, PBR < 1.0)", "💎", value_stocks)
            display_screening_results("배당주 스크리닝 (배당수익률 ≥ 4%)", "💰", dividend_stocks)
            display_screening_results(
                "성장주 스크리닝 (ROE ≥ 15%, 시가총액 ≥ 1000억)", "🚀", growth_stocks,
            )

            # 랭킹 출력
            display_ranking("PER 낮은 순", "per", "배", per_ranking)
            display_ranking("ROE 높은 순", "roe", "%", roe_ranking)

            # 전략 비교
            compare_strategies(value_stocks, dividend_stocks, growth_stocks)

    except httpx.ConnectError:
        print("\n❌ 서버에 연결할 수 없습니다.")
        print("   docker-compose up 으로 서버를 먼저 실행하세요.")
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP 오류: {e.response.status_code}")
        print(f"   {e.response.text}")
        sys.exit(1)

    print(f"\n{'=' * 72}")
    print("  ✅ 스크리닝 완료!")
    print(f"{'=' * 72}")


if __name__ == "__main__":
    asyncio.run(main())
