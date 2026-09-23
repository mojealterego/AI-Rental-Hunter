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

## Continuous monitoring

The agent supports persistent watches. A user can create a watch with a 60-minute or 120-minute interval (or another interval >= 60 minutes), and the service periodically searches again. Only listings not previously seen are emitted as new results.

Example MCP workflow:

1. `create_rental_watch` with the user's criteria and `interval_minutes=60`.
2. The background scheduler performs repeated scans.
3. `scan_watch_now` can force an immediate scan.
4. `list_rental_watches` shows active watches.

### Search coverage

The web-search layer is instructed to search broadly across Polish rental portals, property sites, and publicly indexed social/web pages. It cannot guarantee literally every page on the internet: private groups, login-only content, robots restrictions, CAPTCHA/anti-bot systems and non-indexed posts are not bypassed. The agent must never circumvent those controls.

### New-result semantics

A listing is considered new when its normalized individual listing URL has not previously been recorded. The database is SQLite by default and can be moved with `DATABASE_PATH`.

## Deep-search policy

Each scan is a multi-source research pass. The search prompt explicitly requests independent domains, Polish rental portals, local property sites, agency pages, classifieds and publicly indexed social-media pages, with alternative query formulations. The agent preserves direct listing URLs and does not stop at the first matching source.

Monitoring is incremental: after the initial baseline, the watch returns listings whose normalized URL has not previously been stored. This prevents repeated notifications for the same listing.

A watch interval is enforced at **60 minutes minimum**. One-hour and two-hour monitoring are therefore supported.
