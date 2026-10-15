"""Download Kenya PPRA OCDS years from the OCP Data Registry and build the local award-history index.

uv run python -m scripts.fetch_ocds            # 2024 and 2025, skip files already present
uv run python -m scripts.fetch_ocds --refresh  # download again
Data stays in ignored local_data/ocds/ and is never committed.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx

from connectors.ocds import DOWNLOAD_URL, build_index, index_path

ALLOWED_HOSTS = {"data.open-contracting.org", "fastly.data.open-contracting.org"}


def download(url, target):
    with httpx.Client(timeout=httpx.Timeout(300, connect=15), follow_redirects=True, trust_env=False) as client:
        with client.stream("GET", url) as response:
            if urlparse(str(response.url)).hostname not in ALLOWED_HOSTS:
                raise ValueError(f"Unexpected download host: {response.url}")
            response.raise_for_status()
            partial = target.with_suffix(".part")
            with partial.open("wb") as handle:
                for block in response.iter_bytes():
                    handle.write(block)
            partial.replace(target)
            return str(response.url)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", nargs="+", default=["2024", "2025"])
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    folder = index_path().parent
    folder.mkdir(parents=True, exist_ok=True)
    provenance_file = folder / "retrieval.json"
    provenance = json.loads(provenance_file.read_text(encoding="utf-8")) if provenance_file.exists() else {}
    sources = []
    for year in args.years:
        target = folder / f"kenya-ppra-{year}.jsonl.gz"
        url = DOWNLOAD_URL.format(year=year)
        if args.refresh or not target.exists():
            print(f"Downloading {url}")
            served = download(url, target)
            provenance[target.name] = {"url": url, "served_from": served,
                                       "retrieved_at": datetime.now(timezone.utc).isoformat()}
        record = provenance.get(target.name, {"url": url, "retrieved_at": None})
        sources.append({"path": target, "url": record["url"], "retrieved_at": record["retrieved_at"]})
    provenance_file.write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    meta = build_index(sources)
    print(f"Indexed {len(sources)} file(s) into {index_path()} (award p99 {meta['award_amount_p99']} KES)")


if __name__ == "__main__":
    main()
