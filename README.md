# AI Rental Hunter

AI Rental Hunter is a production-oriented MCP service for finding, normalizing, scoring, and risk-screening rental property listings for use from ChatGPT and other MCP-compatible clients.

## Current scope

- MCP tools for rental search and listing analysis
- Provider-agnostic web search adapter
- Structured rental listing model
- Total-cost normalization
- Requirement matching and ranking
- Basic scam/risk signal detection
- Deterministic scoring for reproducible results
- Docker and Railway deployment files
- Environment-based configuration

## Architecture

```text
ChatGPT / MCP client
        |
        v
   MCP server
        |
   Rental Hunter
    /    |     \
 search  scoring  risk
    |       |      |
 web      model   signals
 sources   data    rules
```

## Quick start

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m rental_hunter
```

The HTTP transport is intended for hosted MCP deployments. Local stdio transport is provided for development.

## Core tools

- `search_rentals` — search for rental listings using natural-language constraints.
- `analyze_listing` — parse and risk-score a single listing URL or text payload.
- `rank_listings` — rank candidate listings against a renter profile.
- `calculate_total_cost` — estimate recurring monthly and one-time move-in costs.

## Important limitation

A provider adapter must comply with each source's terms, robots rules, rate limits, and technical constraints. The baseline implementation uses a generic search gateway rather than bypassing anti-bot controls or authenticated areas.

## License

MIT
