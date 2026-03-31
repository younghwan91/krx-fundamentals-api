# 예제 스크립트

KRX Fundamentals REST API의 사용 예제 모음입니다.

## 사전 준비

```bash
# 1. 서버 실행 (포트 8010)
docker-compose up

# 2. 의존성 설치
pip install httpx
```

## 예제 목록

| 파일 | 설명 | 방식 |
|------|------|------|
| `basic_usage.py` | 모든 주요 API 엔드포인트를 순서대로 호출하는 기본 예제 (기업 조회, 재무제표, 투자 지표, 배당, 주주, 임원, 크롤러 상태) | 동기 (`httpx`) |
| `screening.py` | 가치주·배당주·성장주 전략별 종목 스크리닝 및 랭킹 비교 | 비동기 (`httpx` + `asyncio`) |
| `portfolio_analysis.py` | 포트폴리오 투자 지표 분석, 배당 이력, 시장 평균 대비 비교 | 비동기 (`httpx` + `asyncio`) |

## 실행 방법

```bash
# 기본 사용 예제
python examples/basic_usage.py

# 종목 스크리닝
python examples/screening.py

# 포트폴리오 분석
python examples/portfolio_analysis.py
```

## API 서버

- **기본 주소**: `http://localhost:8010/api/v1`
- **Swagger 문서**: `http://localhost:8010/docs`
- **ReDoc 문서**: `http://localhost:8010/redoc`
