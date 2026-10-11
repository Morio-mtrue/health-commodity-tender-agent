from __future__ import annotations

from urllib.parse import urlparse
import httpx
from orchestrator.store import now

SOURCES = {
    "ppb": "https://products.pharmacyboardkenya.org/ppb_admin/pages/public_view_retention_products.php",
    "ppra": "https://ppra.go.ke/debarred-firms/",
    "keml": "https://www.kemsa.go.ke/content/135/downloads/other-downloads",
    "benchmark": "https://ppra.go.ke/market-price-index/",
}
ALLOWED = {urlparse(url).hostname for url in SOURCES.values()}


def lookup(source, *, live=False):
    url = SOURCES[source]
    result = {"source": source, "url": url, "retrieved_at": now(), "data_as_of": None,
              "status": "UNRESOLVED", "advisory": True,
              "reason": "Live lookup was not requested. No registry assertion is made."}
    if live:
        try:
            # Redirects are deliberately disabled: a portal cannot expand the allowlist.
            with httpx.Client(timeout=15, follow_redirects=False, trust_env=False) as client:
                with client.stream("GET", url, headers={"User-Agent": "HealthTenderWorkbench/0.1"}) as response:
                    response.raise_for_status()
                    total = 0
                    for block in response.iter_bytes():
                        total += len(block)
                        if total > 2_000_000:
                            raise ValueError("Source response exceeds the size limit")
                    result.update(http_status=response.status_code,
                                  reason="Portal retrieved, but no verified structured record or data-as-of date is available.")
        except (httpx.HTTPError, ValueError) as error:
            result["reason"] = f"SOURCE_UNAVAILABLE: {type(error).__name__}"
    return result


def exact_identity_match(legal_name, registration_number, records):
    if not legal_name or not registration_number:
        return {"status": "UNRESOLVED", "record": None}
    matches = [r for r in records if r.get("legal_name") == legal_name and r.get("registration_number") == registration_number]
    # A missing match is never proof of eligibility or noncompliance.
    return {"status": "MATCH_FOR_HUMAN_REVIEW" if len(matches) == 1 else "UNRESOLVED",
            "record": matches[0] if len(matches) == 1 else None}
