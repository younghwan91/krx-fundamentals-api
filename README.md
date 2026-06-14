# 📊 KRX Fundamentals REST API

> 국내 기업 펀더멘탈 데이터를 수집·제공하는 REST API — 재무제표, 투자지표, 배당, 대주주, 종목 스크리닝

[![CI](https://github.com/younghwan91/krx-fundamentals-api/actions/workflows/ci.yml/badge.svg)](https://github.com/younghwan91/krx-fundamentals-api/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/github/license/younghwan91/krx-fundamentals-api)](https://github.com/younghwan91/krx-fundamentals-api/blob/main/LICENSE)

DART, KRX, 네이버 금융 등에서 기업 펀더멘탈 데이터를 자동 수집하여 정규화된 REST API로 제공합니다.

백그라운드 스케줄러가 주기적으로 데이터를 갱신하고 Redis에 캐싱하여, API 요청 시 즉시 응답하는 **캐시 우선(cache-first)** 아키텍처로 설계되었습니다.

## 주요 기능

- 📑 **재무제표 조회** — 연간/분기별 손익계산서, 재무상태표, 현금흐름표
- 📈 **투자지표 분석** — PER, PBR, ROE, ROA, EPS, BPS 등 핵심 밸류에이션 지표
- 💰 **배당정보 제공** — 배당금, 배당수익률, 배당성향 이력 조회
- 👥 **대주주/임원 현황** — 최대주주 지분율, 임원 보수 정보
- 🔍 **종목 스크리닝** — PER, PBR, ROE, 배당수익률 등 복합 조건 필터링
- 🏆 **랭킹 조회** — 시가총액, PER, 배당수익률 등 기준별 종목 순위

---

## 빠른 시작

### Docker로 실행 (권장)

```bash
git clone https://github.com/younghwan91/krx-fundamentals-api.git
cd krx-fundamentals-api

cp .env.example .env          # 환경변수 설정
# .env 파일에서 DART_API_KEY 입력 (필수, https://opendart.fss.or.kr 에서 무료 발급)

docker compose up -d           # API 서버 + Redis 시작
```

```bash
# 헬스체크
curl http://localhost:8001/health
# {"status":"ok"}

# Swagger UI 확인
open http://localhost:8001/docs
```

### 로컬 개발 환경

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Redis 실행 (Docker)
docker compose up -d redis

# 개발 서버 실행 (자동 리로드)
uvicorn krx_fundamentals_api.main:app --reload --port 8001
```

서버가 시작되면 자동으로 DART, KRX 등에서 펀더멘탈 데이터 수집을 시작합니다.

---

## API 문서

서버 실행 후 **Swagger UI**에서 전체 API를 확인하고 테스트할 수 있습니다:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

### 엔드포인트 목록

| 메서드 | 엔드포인트 | 설명 |
|-------|-----------|------|
| `GET` | `/api/v1/companies` | 전체 기업 목록 조회 |
| `GET` | `/api/v1/companies/{ticker}` | 개별 기업 상세 정보 |
| `GET` | `/api/v1/companies/{ticker}/financials` | 재무제표 (손익계산서, 재무상태표, 현금흐름표) |
| `GET` | `/api/v1/companies/{ticker}/ratios` | 투자지표 (PER, PBR, ROE 등) |
| `GET` | `/api/v1/companies/{ticker}/dividends` | 배당 이력 |
| `GET` | `/api/v1/companies/{ticker}/shareholders` | 대주주 현황 |
| `GET` | `/api/v1/companies/{ticker}/executives` | 임원 현황 및 보수 |
| `GET` | `/api/v1/market/overview` | 시장 전체 개요 (시가총액, 종목 수 등) |
| `GET` | `/api/v1/market/sectors` | 섹터별 통계 |
| `GET` | `/api/v1/ranking/{metric}` | 지표별 종목 랭킹 |
| `GET` | `/api/v1/screening` | 복합 조건 종목 스크리닝 |
| `GET` | `/api/v1/status` | 데이터 수집 상태 |
| `GET` | `/health` | 헬스체크 |

### 요청/응답 예시

#### 전체 기업 목록 조회

```bash
curl "http://localhost:8001/api/v1/companies?market=KOSPI&page=1&page_size=3"
```

```json
{
  "items": [
    {
      "ticker": "005930",
      "name": "삼성전자",
      "market": "KOSPI",
      "sector": "반도체",
      "market_cap": 358000000000000,
      "per": 12.5,
      "pbr": 1.18,
      "dividend_yield": 2.34
    },
    {
      "ticker": "000660",
      "name": "SK하이닉스",
      "market": "KOSPI",
      "sector": "반도체",
      "market_cap": 128000000000000,
      "per": 8.7,
      "pbr": 1.52,
      "dividend_yield": 1.12
    },
    {
      "ticker": "005380",
      "name": "현대차",
      "market": "KOSPI",
      "sector": "자동차",
      "market_cap": 52000000000000,
      "per": 5.2,
      "pbr": 0.65,
      "dividend_yield": 3.81
    }
  ],
  "total": 812,
  "page": 1,
  "page_size": 3,
  "has_next": true
}
```

#### 개별 기업 상세 정보

```bash
curl "http://localhost:8001/api/v1/companies/005930"
```

```json
{
  "ticker": "005930",
  "name": "삼성전자",
  "name_en": "Samsung Electronics Co., Ltd.",
  "market": "KOSPI",
  "sector": "반도체",
  "industry": "반도체 제조업",
  "listing_date": "1975-06-11",
  "fiscal_month": 12,
  "ceo": "한종희, 경계현",
  "homepage": "https://www.samsung.com/sec/",
  "market_cap": 358000000000000,
  "shares_outstanding": 5969782550,
  "per": 12.5,
  "pbr": 1.18,
  "eps": 4800,
  "bps": 50817,
  "dividend_yield": 2.34,
  "updated_at": "2026-03-31T10:00:00"
}
```

#### 재무제표 조회

```bash
# 삼성전자 연간 재무제표
curl "http://localhost:8001/api/v1/companies/005930/financials?period=annual"

# 분기별 재무제표
curl "http://localhost:8001/api/v1/companies/005930/financials?period=quarter"
```

```json
{
  "ticker": "005930",
  "name": "삼성전자",
  "period": "annual",
  "financials": [
    {
      "fiscal_year": 2025,
      "fiscal_quarter": null,
      "revenue": 302231000000000,
      "operating_income": 36183000000000,
      "net_income": 26401000000000,
      "total_assets": 455905000000000,
      "total_liabilities": 106151000000000,
      "total_equity": 349754000000000,
      "operating_cash_flow": 49843000000000,
      "investing_cash_flow": -53219000000000,
      "financing_cash_flow": -12764000000000
    },
    {
      "fiscal_year": 2024,
      "fiscal_quarter": null,
      "revenue": 258935000000000,
      "operating_income": 6567000000000,
      "net_income": 15487000000000,
      "total_assets": 448424000000000,
      "total_liabilities": 103618000000000,
      "total_equity": 344806000000000,
      "operating_cash_flow": 45108000000000,
      "investing_cash_flow": -48652000000000,
      "financing_cash_flow": -15401000000000
    }
  ]
}
```

#### 투자지표 조회

```bash
curl "http://localhost:8001/api/v1/companies/005930/ratios"
```

```json
{
  "ticker": "005930",
  "name": "삼성전자",
  "ratios": [
    {
      "fiscal_year": 2025,
      "per": 12.5,
      "pbr": 1.18,
      "roe": 7.85,
      "roa": 5.79,
      "eps": 4800,
      "bps": 50817,
      "dps": 1444,
      "debt_ratio": 30.35,
      "operating_margin": 11.97,
      "net_margin": 8.74
    },
    {
      "fiscal_year": 2024,
      "per": 35.2,
      "pbr": 1.25,
      "roe": 4.49,
      "roa": 3.45,
      "eps": 2131,
      "bps": 47488,
      "dps": 1444,
      "debt_ratio": 30.04,
      "operating_margin": 2.54,
      "net_margin": 5.98
    }
  ]
}
```

#### 배당정보 조회

```bash
curl "http://localhost:8001/api/v1/companies/005930/dividends"
```

```json
{
  "ticker": "005930",
  "name": "삼성전자",
  "dividends": [
    {
      "fiscal_year": 2025,
      "dividend_per_share": 1444,
      "dividend_yield": 2.34,
      "payout_ratio": 30.1,
      "total_dividends": 9620000000000,
      "ex_dividend_date": "2025-12-27"
    },
    {
      "fiscal_year": 2024,
      "dividend_per_share": 1444,
      "dividend_yield": 1.89,
      "payout_ratio": 67.8,
      "total_dividends": 9620000000000,
      "ex_dividend_date": "2024-12-27"
    }
  ]
}
```

#### 대주주 현황 조회

```bash
curl "http://localhost:8001/api/v1/companies/005930/shareholders"
```

```json
{
  "ticker": "005930",
  "name": "삼성전자",
  "shareholders": [
    {
      "name": "이재용",
      "position": "회장",
      "shares": 16530000,
      "ownership_pct": 0.28,
      "change": 0,
      "report_date": "2025-03-31"
    },
    {
      "name": "삼성생명보험",
      "position": "특수관계인",
      "shares": 503759000,
      "ownership_pct": 8.44,
      "change": 0,
      "report_date": "2025-03-31"
    },
    {
      "name": "국민연금공단",
      "position": "주요주주",
      "shares": 548291000,
      "ownership_pct": 9.19,
      "change": -12500000,
      "report_date": "2025-03-31"
    }
  ]
}
```

#### 임원 현황 조회

```bash
curl "http://localhost:8001/api/v1/companies/005930/executives"
```

```json
{
  "ticker": "005930",
  "name": "삼성전자",
  "executives": [
    {
      "name": "한종희",
      "position": "대표이사 부회장",
      "birth_year": 1962,
      "tenure_start": "2022-03-16",
      "compensation": 6800000000,
      "shares_held": 12500
    },
    {
      "name": "경계현",
      "position": "대표이사 사장",
      "birth_year": 1964,
      "tenure_start": "2022-03-16",
      "compensation": 4200000000,
      "shares_held": 8700
    }
  ]
}
```

#### 시장 개요

```bash
curl "http://localhost:8001/api/v1/market/overview"
```

```json
{
  "kospi": {
    "total_companies": 812,
    "total_market_cap": 2128000000000000,
    "avg_per": 11.8,
    "avg_pbr": 0.95,
    "avg_dividend_yield": 2.15
  },
  "kosdaq": {
    "total_companies": 1612,
    "total_market_cap": 418000000000000,
    "avg_per": 23.4,
    "avg_pbr": 1.85,
    "avg_dividend_yield": 0.92
  },
  "updated_at": "2026-03-31T10:00:00"
}
```

#### 섹터별 통계

```bash
curl "http://localhost:8001/api/v1/market/sectors"
```

```json
{
  "sectors": [
    {
      "name": "반도체",
      "companies_count": 45,
      "total_market_cap": 520000000000000,
      "avg_per": 15.3,
      "avg_pbr": 1.82,
      "avg_roe": 9.45
    },
    {
      "name": "자동차",
      "companies_count": 32,
      "total_market_cap": 185000000000000,
      "avg_per": 6.8,
      "avg_pbr": 0.72,
      "avg_roe": 11.2
    },
    {
      "name": "2차전지",
      "companies_count": 28,
      "total_market_cap": 210000000000000,
      "avg_per": 42.1,
      "avg_pbr": 3.15,
      "avg_roe": 5.8
    }
  ],
  "updated_at": "2026-03-31T10:00:00"
}
```

#### 랭킹 조회

```bash
# 시가총액 상위 종목
curl "http://localhost:8001/api/v1/ranking/market_cap?order=desc&limit=5"

# PER 하위 종목 (저PER)
curl "http://localhost:8001/api/v1/ranking/per?order=asc&limit=5"

# 배당수익률 상위 종목
curl "http://localhost:8001/api/v1/ranking/dividend_yield?order=desc&limit=5"
```

```json
{
  "metric": "market_cap",
  "order": "desc",
  "items": [
    { "rank": 1, "ticker": "005930", "name": "삼성전자", "value": 358000000000000 },
    { "rank": 2, "ticker": "000660", "name": "SK하이닉스", "value": 128000000000000 },
    { "rank": 3, "ticker": "373220", "name": "LG에너지솔루션", "value": 95000000000000 },
    { "rank": 4, "ticker": "207940", "name": "삼성바이오로직스", "value": 62000000000000 },
    { "rank": 5, "ticker": "005380", "name": "현대차", "value": 52000000000000 }
  ],
  "total": 812
}
```

**사용 가능한 랭킹 지표:**

| metric | 설명 |
|--------|------|
| `market_cap` | 시가총액 |
| `per` | PER (주가수익비율) |
| `pbr` | PBR (주가순자산비율) |
| `roe` | ROE (자기자본이익률) |
| `dividend_yield` | 배당수익률 |
| `revenue` | 매출액 |
| `operating_income` | 영업이익 |
| `net_income` | 당기순이익 |

#### 종목 스크리닝

```bash
# 저PER + 고배당 KOSPI 종목
curl "http://localhost:8001/api/v1/screening?market=KOSPI&per_max=10&dividend_yield_min=3&page_size=5"
```

```json
{
  "items": [
    {
      "ticker": "005380",
      "name": "현대차",
      "market": "KOSPI",
      "sector": "자동차",
      "per": 5.2,
      "pbr": 0.65,
      "roe": 12.5,
      "dividend_yield": 3.81,
      "market_cap": 52000000000000
    },
    {
      "ticker": "000270",
      "name": "기아",
      "market": "KOSPI",
      "sector": "자동차",
      "per": 4.8,
      "pbr": 0.82,
      "roe": 17.1,
      "dividend_yield": 4.52,
      "market_cap": 38000000000000
    },
    {
      "ticker": "086790",
      "name": "하나금융지주",
      "market": "KOSPI",
      "sector": "금융",
      "per": 4.6,
      "pbr": 0.48,
      "roe": 10.4,
      "dividend_yield": 5.12,
      "market_cap": 18500000000000
    }
  ],
  "total": 47,
  "page": 1,
  "page_size": 5,
  "has_next": true
}
```

#### 수집 상태 확인

```bash
curl "http://localhost:8001/api/v1/status"
```

```json
[
  {
    "source": "dart",
    "last_collected_at": "2026-03-31T09:00:12",
    "companies_count": 2424,
    "is_healthy": true,
    "error": null
  },
  {
    "source": "krx",
    "last_collected_at": "2026-03-31T10:00:05",
    "companies_count": 2424,
    "is_healthy": true,
    "error": null
  },
  {
    "source": "naver",
    "last_collected_at": "2026-03-31T10:00:08",
    "companies_count": 2424,
    "is_healthy": true,
    "error": null
  }
]
```

### 에러 응답

| 상태 코드 | 의미 | 예시 |
|----------|------|------|
| `200` | 성공 | 정상 응답 |
| `404` | 종목 없음 | `{"detail": "Company 999999 not found"}` |
| `422` | 유효성 검증 실패 | 필수 파라미터 누락, 잘못된 값 |
| `503` | Redis 연결 실패 | `{"detail": "Cache service unavailable"}` |
| `500` | 서버 내부 에러 | `{"detail": "Internal server error"}` |

---

## 스크리닝 파라미터

`GET /api/v1/screening` 엔드포인트에서 사용 가능한 필터 파라미터입니다. 모든 파라미터는 선택 사항이며, 조합하여 사용할 수 있습니다.

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|-------|------|
| `market` | `string` | — | 시장 필터 (`KOSPI`, `KOSDAQ`) |
| `sector` | `string` | — | 섹터 필터 (예: `반도체`, `자동차`, `금융`) |
| `per_min` | `float` | — | PER 최소값 |
| `per_max` | `float` | — | PER 최대값 |
| `pbr_min` | `float` | — | PBR 최소값 |
| `pbr_max` | `float` | — | PBR 최대값 |
| `roe_min` | `float` | — | ROE 최소값 (%) |
| `dividend_yield_min` | `float` | — | 배당수익률 최소값 (%) |
| `market_cap_min` | `int` | — | 최소 시가총액 (원) |
| `page` | `int` | `1` | 페이지 번호 |
| `page_size` | `int` | `20` | 페이지 크기 (최대 100) |

**사용 예시:**

```bash
# 고ROE + 저PBR 가치주 스크리닝
curl "http://localhost:8001/api/v1/screening?roe_min=15&pbr_max=1.0"

# KOSDAQ 반도체 섹터 중 시총 1조 이상
curl "http://localhost:8001/api/v1/screening?market=KOSDAQ&sector=반도체&market_cap_min=1000000000000"

# 배당주 스크리닝: PER 10 이하, 배당수익률 3% 이상
curl "http://localhost:8001/api/v1/screening?per_max=10&dividend_yield_min=3"
```

---

## 데이터 소스

| 소스 | URL | 데이터 | 갱신 주기 | 인증 |
|-----|-----|-------|----------|------|
| **DART OpenAPI** | [opendart.fss.or.kr](https://opendart.fss.or.kr) | 재무제표, 배당, 대주주, 임원 | 매일 | API 키 (필수) |
| **KRX 정보데이터시스템** | [data.krx.co.kr](http://data.krx.co.kr) | PER, PBR, 시가총액, 섹터 | 1시간 | 불필요 |
| **네이버 금융** | [finance.naver.com](https://finance.naver.com) | 종목 보조정보, 컨센서스 | 1시간 | 불필요 |

> **참고:** DART API 키는 [opendart.fss.or.kr](https://opendart.fss.or.kr)에서 무료 발급 가능합니다. 키가 없으면 재무제표, 배당, 대주주, 임원 데이터를 수집할 수 없습니다.

---

## 캐시 전략

| 데이터 | Redis 구조 | TTL | 키 패턴 |
|-------|-----------|-----|---------|
| 기업 목록 | Hash | 1시간 | `companies:list` |
| 기업 상세 | Hash | 1시간 | `company:{ticker}` |
| 재무제표 | String (JSON) | 24시간 | `financials:{ticker}:{period}` |
| 투자지표 | String (JSON) | 1시간 | `ratios:{ticker}` |
| 배당 이력 | String (JSON) | 24시간 | `dividends:{ticker}` |
| 대주주 현황 | String (JSON) | 24시간 | `shareholders:{ticker}` |
| 임원 현황 | String (JSON) | 24시간 | `executives:{ticker}` |
| 시장 개요 | String (JSON) | 1시간 | `market:overview` |
| 섹터 통계 | String (JSON) | 1시간 | `market:sectors` |
| 랭킹 | Sorted Set | 1시간 | `ranking:{metric}` |
| 스크리닝 결과 | String (JSON) | 10분 | `screening:{params_hash}` |
| 수집 상태 | String (JSON) | 없음 | `collector:status:{source}` |

---

## 아키텍처

```
┌──────────────────────────────────────────────────────────────────────┐
│                          FastAPI 서버                                 │
│                                                                       │
│  ┌─────────┐      ┌────────────────┐      ┌────────┐                │
│  │ Client  │─────→│  Routes (API)  │─────→│ Redis  │ ← 즉시 응답    │
│  └─────────┘      └────────────────┘      └───┬────┘                │
│                                                │                      │
│  ┌─────────────────────────────────────────────┘                      │
│  │  백그라운드 데이터 수집 (APScheduler)                                │
│  │                                                                    │
│  │  ┌───────────────────┐    ┌────────────┐    ┌────────┐           │
│  │  │   Data Collectors │───→│  정규화/파싱 │───→│ Redis  │           │
│  │  │                   │    └────────────┘    └────────┘           │
│  │  │ · DART OpenAPI    │                                            │
│  │  │ · KRX 정보데이터   │  DART: 매일 06:00                          │
│  │  │ · 네이버 금융      │  KRX/네이버: 매 1시간                       │
│  │  └───────────────────┘                                            │
│  └────────────────────────────────────────────────────────────────────│
└──────────────────────────────────────────────────────────────────────┘
```

### 데이터 흐름

1. **서버 시작** → 모든 소스에서 초기 데이터 수집 실행
2. **스케줄러** → DART 매일, KRX/네이버 1시간 간격 반복 수집
3. **컬렉터** → API 호출 또는 HTML 파싱으로 원본 데이터 수집
4. **정규화** → 기업 정보, 재무제표, 투자지표 등을 통일 스키마로 변환
5. **Redis 저장** → Hash/Sorted Set/String 등 용도별 구조로 캐싱
6. **API 응답** → Redis에서 직접 읽어 즉시 반환

---

## 예제 코드

`examples/` 디렉토리에 바로 실행 가능한 예제가 포함되어 있습니다.

| 파일 | 설명 |
|------|------|
| [`basic_usage.py`](examples/basic_usage.py) | 기본 사용법 — 기업 조회, 재무제표, 투자지표 |
| [`screening.py`](examples/screening.py) | 종목 스크리닝 — 가치주/배당주/성장주 필터링 |
| [`portfolio_analysis.py`](examples/portfolio_analysis.py) | 포트폴리오 분석 — 복수 종목 펀더멘탈 비교 |

```bash
# 서버 실행 후
pip install httpx
python examples/basic_usage.py
```

---

## 환경변수

`.env` 파일 또는 환경변수로 설정합니다. `.env.example`을 복사하여 사용하세요.

```bash
cp .env.example .env
```

| 변수 | 기본값 | 필수 | 설명 |
|-----|-------|------|------|
| `REDIS_URL` | `redis://localhost:6379` | — | Redis 연결 URL |
| `DART_API_KEY` | — | ✅ | DART Open API 키 ([발급](https://opendart.fss.or.kr)) |
| `COLLECT_INTERVAL_DART` | `86400` | — | DART 수집 주기 (초, 기본 24시간) |
| `COLLECT_INTERVAL_KRX` | `3600` | — | KRX 수집 주기 (초, 기본 1시간) |
| `COLLECT_INTERVAL_NAVER` | `3600` | — | 네이버 수집 주기 (초, 기본 1시간) |
| `LOG_LEVEL` | `INFO` | — | 로그 레벨 (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `HOST` | `0.0.0.0` | — | 서버 바인드 주소 |
| `PORT` | `8001` | — | 서버 포트 |
| `WORKERS` | `1` | — | Uvicorn 워커 수 |
| `CORS_ORIGINS` | `["*"]` | — | CORS 허용 origin 목록 |

---

## 개발

### 테스트

```bash
# 전체 테스트 (Redis 불필요 — fakeredis로 자동 mock)
pytest

# 상세 출력
pytest -v

# 단일 테스트
pytest tests/test_api.py::test_health -v

# 특정 파일
pytest tests/test_models.py -v
```

### 린트 & 포맷

```bash
# 린트 검사
ruff check src/ tests/

# 자동 수정
ruff check --fix src/ tests/

# 코드 포맷팅
ruff format src/ tests/
```

### Docker 빌드

```bash
# 이미지 빌드
docker build -t krx-fundamentals-api .

# 단독 실행
docker run -p 8001:8001 --env-file .env krx-fundamentals-api

# Docker Compose (권장)
docker compose up -d           # 시작
docker compose logs -f api     # 로그 확인
docker compose down            # 중지
```

---

## 생태계

이 프로젝트는 한국 주식시장 데이터 인프라의 일부로, 아래 API들과 함께 사용할 수 있습니다.

```
┌─────────────────────────────────────────────────────────────┐
│                    한국 주식시장 데이터 인프라                   │
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  kiwoom-rest-api │  │krx-news-rest-api│  │    krx-     │ │
│  │                  │  │                 │  │fundamentals-│ │
│  │  매매 실행 + 시세  │  │  뉴스 + 공시     │  │    api      │ │
│  │  주문, 잔고, 체결  │  │  KIND, DART,    │  │             │ │
│  │  호가, 체결가     │  │  네이버, 한경,   │  │ 재무제표,    │ │
│  │                  │  │  더벨           │  │ 투자지표,    │ │
│  │                  │  │                 │  │ 배당, 스크리닝│ │
│  └─────────────────┘  └─────────────────┘  └──────┬──────┘ │
│                                                ← 현재 │       │
└─────────────────────────────────────────────────────────────┘
```

| 저장소 | 역할 | 포트 |
|-------|------|------|
| [kiwoom-rest-api](https://github.com/younghwan91/kiwoom-rest-api) | 매매 실행 + 실시간 시세 | `8000` |
| [krx-news-rest-api](https://github.com/younghwan91/krx-news-rest-api) | 뉴스 / 공시 수집 | `8000` |
| **krx-fundamentals-api** | 기업 펀더멘탈 데이터 ← 현재 | `8001` |

---

## 기술 스택

| 구성 요소 | 기술 |
|----------|------|
| 프레임워크 | [FastAPI](https://fastapi.tiangolo.com/) |
| HTTP 클라이언트 | [httpx](https://www.python-httpx.org/) (async) |
| HTML 파싱 | [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) + lxml |
| 캐시 | [Redis](https://redis.io/) (redis-py async) |
| 스케줄러 | [APScheduler](https://apscheduler.readthedocs.io/) |
| 데이터 검증 | [Pydantic](https://docs.pydantic.dev/) |
| 설정 관리 | [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| 린트/포맷 | [Ruff](https://docs.astral.sh/ruff/) |
| 테스트 | [pytest](https://pytest.org/) + fakeredis |
| CI/CD | GitHub Actions |
| 컨테이너 | Docker + docker-compose |

---

## 라이선스

MIT
