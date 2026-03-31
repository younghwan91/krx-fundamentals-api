from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class DataSource(StrEnum):
    DART = "dart"
    KRX = "krx"
    NAVER = "naver"


class Market(StrEnum):
    KOSPI = "kospi"
    KOSDAQ = "kosdaq"
    KONEX = "konex"


class ReportType(StrEnum):
    ANNUAL = "annual"  # 사업보고서 11011
    HALF = "half"  # 반기보고서 11012
    Q1 = "q1"  # 1분기보고서 11013
    Q3 = "q3"  # 3분기보고서 11014


class RankingMetric(StrEnum):
    MARKET_CAP = "market_cap"
    PER = "per"
    PBR = "pbr"
    ROE = "roe"
    DIVIDEND_YIELD = "dividend_yield"
    REVENUE = "revenue"
    NET_INCOME = "net_income"


# --- 기업 정보 ---


class Company(BaseModel):
    ticker: str = Field(description="종목코드 (6자리)")
    corp_code: str = Field(default="", description="DART 고유번호 (8자리)")
    name: str
    name_en: str = ""
    market: Market | None = None
    sector: str = ""
    industry: str = ""
    ceo: str = ""
    address: str = ""
    phone: str = ""
    website: str = ""
    ir_url: str = ""
    established_date: str = ""
    listing_date: str = ""
    fiscal_month: int = 12
    updated_at: datetime = Field(default_factory=datetime.now)


# --- 재무제표 ---


class FinancialStatement(BaseModel):
    ticker: str
    year: int
    report_type: ReportType
    currency: str = "KRW"

    revenue: float | None = None  # 매출액
    operating_income: float | None = None  # 영업이익
    net_income: float | None = None  # 당기순이익
    total_assets: float | None = None  # 자산총계
    total_liabilities: float | None = None  # 부채총계
    total_equity: float | None = None  # 자본총계

    revenue_yoy: float | None = None  # 매출 전년비 (%)
    operating_income_yoy: float | None = None  # 영업이익 전년비 (%)
    net_income_yoy: float | None = None  # 순이익 전년비 (%)

    collected_at: datetime = Field(default_factory=datetime.now)


# --- 투자지표 ---


class InvestmentRatio(BaseModel):
    ticker: str
    name: str = ""
    market: Market | None = None

    market_cap: float | None = None  # 시가총액 (억원)
    per: float | None = None
    pbr: float | None = None
    psr: float | None = None
    pcr: float | None = None
    eps: float | None = None  # 주당순이익
    bps: float | None = None  # 주당순자산
    roe: float | None = None  # 자기자본이익률 (%)
    roa: float | None = None  # 총자산이익률 (%)
    debt_ratio: float | None = None  # 부채비율 (%)
    operating_margin: float | None = None  # 영업이익률 (%)
    net_margin: float | None = None  # 순이익률 (%)
    dividend_yield: float | None = None  # 배당수익률 (%)

    price: float | None = None  # 현재가
    volume: int | None = None  # 거래량
    high_52w: float | None = None  # 52주 최고
    low_52w: float | None = None  # 52주 최저
    foreign_ratio: float | None = None  # 외국인비율 (%)

    updated_at: datetime = Field(default_factory=datetime.now)


# --- 배당 ---


class Dividend(BaseModel):
    ticker: str
    year: int
    dividend_per_share: float | None = None  # 주당 배당금 (원)
    dividend_yield: float | None = None  # 배당수익률 (%)
    payout_ratio: float | None = None  # 배당성향 (%)
    total_dividends: float | None = None  # 배당금 총액 (백만원)
    ex_dividend_date: str = ""
    payment_date: str = ""
    collected_at: datetime = Field(default_factory=datetime.now)


# --- 대주주 ---


class Shareholder(BaseModel):
    ticker: str
    name: str  # 주주명
    shares: int = 0  # 보유 주식수
    ownership_pct: float = 0.0  # 지분율 (%)
    change_shares: int = 0  # 증감
    report_date: str = ""
    collected_at: datetime = Field(default_factory=datetime.now)


# --- 임원 ---


class Executive(BaseModel):
    ticker: str
    name: str
    birth_year: str = ""
    gender: str = ""
    position: str = ""  # 직위
    role: str = ""  # 담당업무
    tenure: str = ""  # 재임기간
    is_registered: bool = False  # 등기임원 여부
    collected_at: datetime = Field(default_factory=datetime.now)


# --- 섹터 ---


class SectorOverview(BaseModel):
    sector: str
    company_count: int = 0
    total_market_cap: float | None = None
    avg_per: float | None = None
    avg_pbr: float | None = None
    avg_dividend_yield: float | None = None


# --- 응답 ---


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    has_next: bool


class CrawlerStatus(BaseModel):
    source: DataSource
    job_name: str = ""
    last_crawled_at: datetime | None = None
    items_count: int = 0
    is_healthy: bool = True
    error: str | None = None
