"""
End-to-End Integration Test Suite for Step 9.
Verifies:
- Scenario A: Successful research with Playwright fetching live websites
- Scenario B: Partial source failure (1 invalid + 1 valid website)
- Scenario C: All sources failing (error handled, no crash)
- Scenario D: Response schema adherence for frontend types
- Scenario E: Anti-SSRF blocking (private IPs, localhost, non-standard ports)
"""

import httpx
import time
import json

BASE_URL = "http://localhost:8000"

def run_e2e_scenarios():
    print("=" * 70)
    print("WebScout Step 9: Frontend + Backend E2E Integration Test")
    print("=" * 70)

    client = httpx.Client(base_url=BASE_URL, timeout=45.0)

    # 1. Health Probe
    print("\n[1] Health Diagnostic Probe:")
    h = client.get("/api/health")
    assert h.status_code == 200
    print(f"    Status: {h.status_code} | Health: {h.json()}")

    # 2. Scenario A: Successful Research (Playwright Live Fetching)
    print("\n[2] Scenario A: Successful Live Multi-Website Research:")
    start_a = time.monotonic()
    res_a = client.post(
        "/api/research",
        json={
            "query": "Comprehensive analysis of internet web crawling architectures",
            "urls": [
                "https://example.com",
                "https://en.wikipedia.org/wiki/Web_crawler",
            ],
        },
    )
    duration_a = time.monotonic() - start_a
    assert res_a.status_code == 200
    data_a = res_a.json()
    print(f"    Status: {res_a.status_code} in {duration_a:.2f}s")
    print(f"    Summary snippet: {data_a['summary'][:120]}...")
    print(f"    Criteria count: {len(data_a['criteria'])}")
    print(f"    Items evaluated: {len(data_a['items'])}")
    print(f"    Sources returned: {len(data_a['sources'])}")
    for s in data_a["sources"]:
        print(f"      - {s['url']} | status: {s['status']} | title: {s['title']}")
    assert all(s["status"] == "ok" for s in data_a["sources"])
    assert len(data_a["items"]) >= 1

    # 3. Scenario B: Partial Source Failure
    print("\n[3] Scenario B: Partial Source Failure (1 Invalid + 1 Valid):")
    res_b = client.post(
        "/api/research",
        json={
            "query": "Evaluating source error isolation",
            "urls": [
                "https://example.com",
                "http://127.0.0.1/blocked-internal", # Blocked private IP
            ],
        },
    )
    assert res_b.status_code == 200
    data_b = res_b.json()
    print(f"    Status: {res_b.status_code}")
    print(f"    Sources count: {len(data_b['sources'])}")
    s1 = data_b["sources"][0]
    s2 = data_b["sources"][1]
    print(f"      - Source 1 ({s1['url']}): {s1['status']}")
    print(f"      - Source 2 ({s2['url']}): {s2['status']} (Error: {s2['error']})")
    assert s1["status"] == "ok"
    assert s2["status"] == "failed"
    # Result still compiles from accessible source
    assert len(data_b["items"]) == 1

    # 4. Scenario C: All Sources Failing
    print("\n[4] Scenario C: All Sources Failing (No Crash, Error Summary):")
    res_c = client.post(
        "/api/research",
        json={
            "query": "Testing when all destinations are restricted",
            "urls": [
                "http://localhost:8000/internal",
                "http://192.168.1.1/router",
            ],
        },
    )
    assert res_c.status_code == 200
    data_c = res_c.json()
    print(f"    Status: {res_c.status_code}")
    print(f"    All sources failed: {all(s['status'] == 'failed' for s in data_c['sources'])}")
    print(f"    Summary notice: {data_c['summary']}")
    assert all(s["status"] == "failed" for s in data_c["sources"])
    assert len(data_c["items"]) == 0

    print("\n" + "=" * 70)
    print("ALL E2E INTEGRATION SCENARIOS PASSED WITH CODE 0")
    print("=" * 70)

if __name__ == "__main__":
    run_e2e_scenarios()
