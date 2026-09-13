# krx-fundamentals-client

[![CI](https://github.com/younghwan91/krx-fundamentals-client/actions/workflows/ci.yml/badge.svg)](https://github.com/younghwan91/krx-fundamentals-client/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/younghwan91/krx-fundamentals-client)](https://github.com/younghwan91/krx-fundamentals-client/blob/main/LICENSE)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-younghwan--chae-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/younghwan-chae/)

[한국어](README.md)

**A Python client library that pulls Korean corporate fundamentals from DART, KRX and Naver Finance into one schema** — financial statements, valuation ratios, dividends, major shareholders, executives, and stock screening.

Same shape as [kiwoom-client](https://github.com/younghwan91/kiwoom-client) and [krx-news-client](https://github.com/younghwan91/krx-news-client) — no standing server. It hits the upstream source directly, in-process, whenever you call it, and hands back normalized results.

> ⛔ **The KRX collection path is currently blocked (measured 2026-08).**
> KRX put a login in front of the MDCSTAT endpoints, and OTP issuance now returns `LOGOUT` instead of a
> token. The scraper treats that string as a valid OTP and passes it along, so it **returns an empty
> list and raises nothing**. Everything KRX fills — valuation ratios, market cap, sectors — goes quietly
> empty (the top 100 tickers can be backfilled with `NaverScraper`; the DART path is unaffected).
> Code walkthrough: [docs/krx-blocked.md](docs/krx-blocked.md) (Korean).

## Install

```bash
pip install krx-fundamentals-client
```

## Quick start

```python
import asyncio
from krx_fundamentals_client import DartScraper

async def main():
    scraper = DartScraper(api_key="...")  # free key at https://opendart.fss.or.kr
    try:
        company = await scraper.fetch_company("005930")
        print(company.name, company.ceo)

        financials = await scraper.fetch_financials("005930", year=2025)
        print(financials.revenue, financials.operating_income)
    finally:
        await scraper.close()

asyncio.run(main())
```

Market-wide ratios plus ranking/screening:

```python
from krx_fundamentals_client import KrxScraper, Market, RankingMetric, rank_stocks, screen_stocks

async def screen():
    scraper = KrxScraper()
    try:
        ratios = await scraper.fetch_investment_ratios(Market.KOSPI)
    finally:
        await scraper.close()

    value_stocks = screen_stocks(ratios, per_max=10, pbr_max=1.0)
    top_by_roe = rank_stocks(ratios, RankingMetric.ROE)
```

Financials for many tickers at once (DART's `fnlttMultiAcnt` batch endpoint, up to 100 tickers per call):

```python
financials = await scraper.fetch_financials_batch(
    ["005930", "000660", "035420"], year=2025,
)
for ticker, fs in financials.items():
    if fs is not None:
        print(ticker, fs.revenue, fs.net_income)
```

More examples in [`examples/`](examples/).

DART keys carry a daily call quota. Once exhausted, every `DartScraper` method
raises `DartQuotaExceededError` — a distinct exception so an orchestrator
rotating multiple keys can tell "no data" apart from "quota exceeded":

```python
from krx_fundamentals_client import DartQuotaExceededError, DartScraper

async def fetch_with_rotation(tickers, keys):
    for key in keys:
        scraper = DartScraper(api_key=key)
        try:
            return [await scraper.fetch_company(t) for t in tickers]
        except DartQuotaExceededError:
            continue
        finally:
            await scraper.close()
    raise RuntimeError("all keys exhausted their daily quota")
```

## Data sources

| Source | Data | Unit of collection | Auth |
|--------|------|---------------------|------|
| [DART OpenAPI](https://opendart.fss.or.kr) | Company profile, financials, dividends, shareholders, executives | Per ticker (financials also batchable, up to 100 tickers/call) | API key (free) |
| [KRX Information Data System](http://data.krx.co.kr) | PER, PBR, market cap, sectors | Whole-market bulk CSV | None (⛔ currently blocked by login) |
| [Naver Finance](https://m.stock.naver.com) | Price, PER, PBR, EPS, BPS, dividend yield | Per ticker | None |

## Response models

`Company`, `FinancialStatement`, `InvestmentRatio`, `Dividend`, `Shareholder`, `Executive`, `SectorOverview` — all Pydantic models, importable directly from `krx_fundamentals_client`. See [`models/schemas.py`](src/krx_fundamentals_client/models/schemas.py) for fields.

## Screening / ranking

`screen_stocks` and `rank_stocks` are pure functions with no cache or state — pass them the `list[InvestmentRatio]` you got from `KrxScraper.fetch_investment_ratios()` and they filter/sort it on the spot. See [docs/architecture.md](docs/architecture.md) (Korean) for details.

## Development

```bash
uv sync --extra dev
uv run pytest                        # tests
uv run ruff check src/ tests/        # lint
uv run ruff format src/ tests/       # format
```

## Docs

- [docs/architecture.md](docs/architecture.md) — scraper structure, ranking/screening, DART call order
- [docs/krx-blocked.md](docs/krx-blocked.md) — code walkthrough of the KRX block
- [`examples/`](examples/) — runnable usage examples

(The docs under `docs/` are written in Korean.)

## License

Apache-2.0 ([LICENSE](LICENSE))

## Author

**Younghwan Chae** · [GitHub @younghwan91](https://github.com/younghwan91) · [LinkedIn](https://www.linkedin.com/in/younghwan-chae/)

Bugs and questions go to [Issues](https://github.com/younghwan91/krx-fundamentals-client/issues); a ⭐ helps if this was useful.

## Related projects — open-source quant stack

Part of an open-source stack spanning Korean equities, US equities and crypto. Each repository stands on its own.

| Market | Project | What it is |
|---|---|---|
| 🇰🇷 Korean equities | **[kiwoom-client](https://github.com/younghwan91/kiwoom-client)** | Kiwoom Securities REST API client — full domestic-equity endpoint coverage, real-time WebSocket, sync + async (`pip install kiwoom-client`) |
| 🇰🇷 Korean equities | **[krx-news-client](https://github.com/younghwan91/krx-news-client)** | Korean market news & disclosure Python client library (DART + Hankyung + TheBell + Toss) |
| 🇰🇷 Korean equities | **[fin-checkup](https://github.com/younghwan91/fin-checkup)** | Telegram alerts for risk disclosures + a DART/SEC financial health checkup — reports measurements and facts, never a recommendation |
| 🇰🇷 Korean equities | **[quant-airflow](https://github.com/younghwan91/quant-airflow)** | Airflow pipeline collecting Korean market data into TimescaleDB — delisted names included, so downstream backtests aren't survivorship-biased |
| 🇰🇷 Korean equities | **[kr-quant](https://github.com/younghwan91/kr-quant)** | KOSPI/KOSDAQ alpha research — walk-forward, random null controls, purged CV and Deflated Sharpe enforced as CI guardrails |
| 🇺🇸 US equities | **[portfolio-research](https://github.com/younghwan91/portfolio-research)** | US equity factor engine — walk-forward gated by Deflated Sharpe and PBO on point-in-time, survivorship-bias-free data (plus tactical ETF allocation: 9 pre-registered, 0 adopted) |
| 🇺🇸 US equities | **[automated-stock-trading-systems](https://github.com/younghwan91/automated-stock-trading-systems)** | Backtester for Bensdorp's seven non-correlated trading systems (educational reimplementation) |
| ₿ Crypto | **[binance-quant-engine](https://github.com/younghwan91/binance-quant-engine)** | Crypto futures backtest & execution engine — zero lookahead, backtest↔live parity |

