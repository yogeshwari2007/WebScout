# WebScout Backend Engine

FastAPI backend service and asynchronous Playwright website fetching engine for **WebScout** (wHACKiest 2026 Hackathon, Track 2).

The backend coordinates concurrent multi-website retrieval, robust anti-SSRF security checks, DOM content extraction and sanitization, and structured research response formatting.

---

## Architecture Overview

```
backend/
  app/
    main.py                 # FastAPI application with lifespan management and CORS
    config.py               # Centralized configuration via Pydantic Settings
    api/
      routes/
        health.py           # GET /api/health diagnostics
        research.py         # POST /api/research endpoint
    models/
      request.py            # ResearchRequest model with query and URL validation
      response.py           # Structured ResearchResponse matching frontend contract
      fetch.py              # FetchResult data structure
    services/
      fetchers/
        base.py             # Abstract PageFetcher interface
        playwright_fetcher.py # Headless Chromium with resource blocking & SSRF guards
        mock_fetcher.py     # Deterministic mock fetcher for tests & offline runs
      analyzers/
        base.py             # Abstract BaseAnalyzer interface
        mock_analyzer.py    # Illustrative mock analyzer (Gemini in Step 8)
      orchestrator.py       # Concurrent execution coordinator (Semaphore=5, 20s timeout)
    utils/
      url_validation.py     # Strict anti-SSRF, scheme, port, IP, and DNS validator
      content_cleaner.py    # BeautifulSoup4 cleaner (strips ads/nav/scripts, caps 12k chars)
  tests/                    # Automated pytest suite & manual integration test
  requirements.txt          # Python dependencies
  .env.example              # Environment variables template
  README.md                 # Documentation
```

---

## Security & Anti-SSRF Protection

User-supplied URLs are treated as strictly untrusted:
1. **Allowed Schemes**: Only `http://` and `https://` are permitted. Dangerous schemes (`file:`, `data:`, `javascript:`, `ftp:`) are blocked immediately.
2. **Port Restrictions**: Only standard ports `80` (HTTP) and `443` (HTTPS) are allowed. Internal service ports (`22`, `3000`, `8000`, `6379`, `9200`) are rejected.
3. **Restricted IP & Hostname Blocking**:
   - Loopback (`127.0.0.0/8`, `::1`), Localhost (`localhost`, `*.local`, `*.internal`, `*.lan`).
   - Private networks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `fc00::/7`).
   - Cloud metadata IP explicitly blocked: `169.254.169.254` (AWS, GCP, Azure, DigitalOcean).
   - Link-local and multicast ranges.
4. **DNS Resolution Verification**: Domain hostnames are resolved before connection. If any associated IP is restricted, the URL is rejected before opening a browser tab.
5. **Runtime Route Guarding**: Playwright intercepts all network requests and redirects. If a page attempts a client-side navigation or redirect to an internal IP, it is aborted with `blockedbyclient`.
6. **Safe Error Messages**: Error responses never disclose internal IP addresses, environment paths, or stack traces.

### Remaining SSRF Considerations & Limitations
- **DNS Rebinding**: A malicious authoritative nameserver could return a public IP during the pre-check lookup and later respond with a private IP (`127.0.0.1`) when Playwright connects. WebScout mitigates this by validating subrequests at the Playwright network route level (`page.route("**/*")`), aborting requests navigating to restricted destinations.
- **Bot Detection & Cloudflare**: Sites requiring human CAPTCHA or Cloudflare Turnstile return clean fetch failure statuses (`Page contained no readable text or content was protected by a paywall/bot check`) rather than crashing the system.

---

## Setup & Running Instructions

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Install Playwright Chromium
```bash
playwright install chromium
```

### 3. Environment Configuration
Copy `.env.example` to `.env` (optional, default values work out of the box for development):
```bash
cp .env.example .env
```

Key environment variables:
- `FETCHER`: `playwright` (default) or `mock`.
- `ANALYZER`: `mock` (Gemini is connected in Step 8).
- `USE_MOCK`: Set to `true` to force mock fetching without launching a browser.
- `MAX_URLS`: Maximum candidate websites per request (default `5`).
- `CORS_ORIGINS`: Allowed frontend origins (default `http://localhost:3000`).

### 4. Start Backend Server
```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Access Endpoints
- **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Root**: [http://localhost:8000/](http://localhost:8000/)

---

## Testing

### Run Automated Test Suite
```bash
pytest -v
```
Tests cover URL validation, SSRF restrictions, content extraction, mock fetching, error isolation, order preservation, and API request schemas.

### Run Manual Integration Test with Live Public Websites
```bash
python tests/manual_integration_test.py
```
Visits `https://example.com` and `https://en.wikipedia.org/wiki/Web_crawler` concurrently via headless Chromium, extracting and displaying cleaned content.
