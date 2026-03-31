"""KRX Fundamentals API 기본 사용 예제.

동기 방식으로 주요 API 엔드포인트를 호출하는 기본 예제입니다.
기업 목록 조회, 상세 정보, 재무제표, 투자 지표, 배당, 주주, 임원 정보 및
크롤러 상태 확인까지 전체 API를 순서대로 체험할 수 있습니다.

사용법:
    pip install httpx
    python examples/basic_usage.py
"""

from __future__ import annotations

import sys

import httpx

BASE_URL = "http://localhost:8010/api/v1"
TIMEOUT = 10.0


def print_header(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def check_health(client: httpx.Client) -> bool:
    """서버 헬스 체크."""
    print_header("서버 헬스 체크")
    try:
        resp = client.get(f"{BASE_URL.rsplit('/api', 1)[0]}/health")
        resp.raise_for_status()
        print(f"  상태: {resp.json()}")
        return True
    except httpx.ConnectError:
        print("  ❌ 서버에 연결할 수 없습니다.")
        print("     docker-compose up 으로 서버를 먼저 실행하세요.")
        return False


def list_companies(client: httpx.Client) -> None:
    """기업 목록 조회 및 검색."""
    print_header("기업 목록 조회")

    # 전체 목록 (첫 페이지)
    resp = client.get(f"{BASE_URL}/companies", params={"page": 1, "page_size": 5})
    resp.raise_for_status()
    data = resp.json()
    print(f"  전체 기업 수: {data['total']}개")
    for company in data["items"]:
        print(f"    {company['ticker']} | {company['name']} | {company.get('market', '-')}")

    # 이름으로 검색
    print("\n  🔍 '삼성' 검색 결과:")
    resp = client.get(f"{BASE_URL}/companies", params={"q": "삼성", "page_size": 5})
    resp.raise_for_status()
    data = resp.json()
    for company in data["items"]:
        print(f"    {company['ticker']} | {company['name']}")


def get_company_detail(client: httpx.Client, ticker: str = "005930") -> None:
    """기업 상세 정보 조회."""
    print_header(f"기업 상세 정보 ({ticker})")
    resp = client.get(f"{BASE_URL}/companies/{ticker}")
    resp.raise_for_status()
    company = resp.json()

    fields = [
        ("종목코드", company.get("ticker")),
        ("기업명", company.get("name")),
        ("영문명", company.get("name_en")),
        ("시장", company.get("market")),
        ("섹터", company.get("sector")),
        ("대표이사", company.get("ceo")),
        ("홈페이지", company.get("website")),
        ("결산월", f"{company.get('fiscal_month')}월"),
    ]
    for label, value in fields:
        if value:
            print(f"  {label}: {value}")


def get_financials(client: httpx.Client, ticker: str = "005930") -> None:
    """재무제표 조회."""
    print_header(f"재무제표 ({ticker})")
    resp = client.get(f"{BASE_URL}/companies/{ticker}/financials")
    resp.raise_for_status()
    data = resp.json()

    if not data.get("statements"):
        print("  데이터 없음")
        return

    print(f"  총 {data['total']}건")
    for stmt in data["statements"][:5]:
        print(f"\n  📊 {stmt['year']}년 ({stmt['report_type']})")
        if stmt.get("revenue") is not None:
            print(f"    매출액:     {stmt['revenue']:>15,.0f}")
        if stmt.get("operating_income") is not None:
            print(f"    영업이익:   {stmt['operating_income']:>15,.0f}")
        if stmt.get("net_income") is not None:
            print(f"    당기순이익: {stmt['net_income']:>15,.0f}")
        if stmt.get("total_assets") is not None:
            print(f"    자산총계:   {stmt['total_assets']:>15,.0f}")
        if stmt.get("total_equity") is not None:
            print(f"    자본총계:   {stmt['total_equity']:>15,.0f}")


def get_ratios(client: httpx.Client, ticker: str = "005930") -> None:
    """투자 지표 조회 (PER, PBR, ROE 등)."""
    print_header(f"투자 지표 ({ticker})")
    resp = client.get(f"{BASE_URL}/companies/{ticker}/ratios")
    resp.raise_for_status()
    ratio = resp.json()

    metrics = [
        ("종목명", ratio.get("name"), ""),
        ("현재가", ratio.get("price"), "원"),
        ("시가총액", ratio.get("market_cap"), "억원"),
        ("PER", ratio.get("per"), "배"),
        ("PBR", ratio.get("pbr"), "배"),
        ("PSR", ratio.get("psr"), "배"),
        ("EPS", ratio.get("eps"), "원"),
        ("BPS", ratio.get("bps"), "원"),
        ("ROE", ratio.get("roe"), "%"),
        ("ROA", ratio.get("roa"), "%"),
        ("부채비율", ratio.get("debt_ratio"), "%"),
        ("영업이익률", ratio.get("operating_margin"), "%"),
        ("순이익률", ratio.get("net_margin"), "%"),
        ("배당수익률", ratio.get("dividend_yield"), "%"),
        ("외국인비율", ratio.get("foreign_ratio"), "%"),
        ("52주 최고", ratio.get("high_52w"), "원"),
        ("52주 최저", ratio.get("low_52w"), "원"),
    ]
    for label, value, unit in metrics:
        if value is not None:
            if isinstance(value, float):
                print(f"  {label:>10}: {value:>12,.2f} {unit}")
            else:
                print(f"  {label:>10}: {value} {unit}")


def get_dividends(client: httpx.Client, ticker: str = "005930") -> None:
    """배당 정보 조회."""
    print_header(f"배당 정보 ({ticker})")
    resp = client.get(f"{BASE_URL}/companies/{ticker}/dividends")
    resp.raise_for_status()
    data = resp.json()

    if not data.get("dividends"):
        print("  데이터 없음")
        return

    print(f"  총 {data['total']}건")
    for div in data["dividends"][:5]:
        print(f"\n  💰 {div['year']}년")
        if div.get("dividend_per_share") is not None:
            print(f"    주당배당금:   {div['dividend_per_share']:>10,.0f}원")
        if div.get("dividend_yield") is not None:
            print(f"    배당수익률:   {div['dividend_yield']:>10.2f}%")
        if div.get("payout_ratio") is not None:
            print(f"    배당성향:     {div['payout_ratio']:>10.2f}%")
        if div.get("ex_dividend_date"):
            print(f"    배당락일:     {div['ex_dividend_date']}")


def get_shareholders(client: httpx.Client, ticker: str = "005930") -> None:
    """주주 정보 조회."""
    print_header(f"주주 정보 ({ticker})")
    resp = client.get(f"{BASE_URL}/companies/{ticker}/shareholders")
    resp.raise_for_status()
    data = resp.json()

    if not data.get("shareholders"):
        print("  데이터 없음")
        return

    print(f"  총 {data['total']}명")
    for sh in data["shareholders"][:10]:
        pct = f"{sh['ownership_pct']:.2f}%" if sh.get("ownership_pct") else "-"
        shares = f"{sh['shares']:,}주" if sh.get("shares") else "-"
        print(f"    {sh['name']:>12} | {shares:>15} | {pct:>8}")


def get_executives(client: httpx.Client, ticker: str = "005930") -> None:
    """임원 정보 조회."""
    print_header(f"임원 정보 ({ticker})")
    resp = client.get(f"{BASE_URL}/companies/{ticker}/executives")
    resp.raise_for_status()
    data = resp.json()

    if not data.get("executives"):
        print("  데이터 없음")
        return

    print(f"  총 {data['total']}명")
    for ex in data["executives"][:10]:
        registered = "등기" if ex.get("is_registered") else "비등기"
        print(
            f"    {ex.get('name', '-'):>8}"
            f" | {ex.get('position', '-'):>10}"
            f" | {ex.get('role', '-'):>10}"
            f" | {registered}"
        )


def check_crawler_status(client: httpx.Client) -> None:
    """크롤러 상태 확인."""
    print_header("크롤러 상태")
    resp = client.get(f"{BASE_URL}/status")
    resp.raise_for_status()
    statuses = resp.json()

    if not statuses:
        print("  상태 정보 없음")
        return

    for s in statuses:
        healthy = "✅" if s.get("is_healthy") else "❌"
        last = s.get("last_crawled_at", "없음")
        print(f"  {healthy} [{s.get('source', '-')}] {s.get('job_name', '-')}")
        print(f"       수집 건수: {s.get('items_count', 0):,}건")
        print(f"       마지막 수집: {last}")
        if s.get("error"):
            print(f"       오류: {s['error']}")


def main() -> None:
    ticker = "005930"  # 삼성전자
    print("🇰🇷 KRX Fundamentals API - 기본 사용 예제")
    print(f"   서버: {BASE_URL}")

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            if not check_health(client):
                sys.exit(1)

            list_companies(client)
            get_company_detail(client, ticker)
            get_financials(client, ticker)
            get_ratios(client, ticker)
            get_dividends(client, ticker)
            get_shareholders(client, ticker)
            get_executives(client, ticker)
            check_crawler_status(client)

    except httpx.ConnectError:
        print("\n❌ 서버에 연결할 수 없습니다.")
        print("   docker-compose up 으로 서버를 먼저 실행하세요.")
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP 오류: {e.response.status_code}")
        print(f"   {e.response.text}")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print("  ✅ 모든 API 호출 완료!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
