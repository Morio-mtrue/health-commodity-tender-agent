"""Award history from published OCDS releases (Kenya PPRA via the OCP Data Registry).

The publication carries tenders and awards but no item lines, so award values are whole-contract
amounts. Nothing here produces a unit-price benchmark or a finding against a supplier.
Parties are dropped at index time: they carry contact points with personal details.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

DATASET = "Kenya PPRA OCDS (Public Procurement Information Portal), via the OCP Data Registry publication 147"
REGISTRY_URL = "https://data.open-contracting.org/en/publication/147"
DOWNLOAD_URL = REGISTRY_URL + "/download?name={year}.jsonl.gz"
ENUMERATED = re.compile(r"^\s*\d{1,3}\s*[.)]\s*")
PRICE_NOTE = ("Award values are whole-contract amounts. This publication has no tender or award items, "
              "so no unit-price benchmark is computed.")


def index_path():
    return Path(os.getenv("TENDER_OCDS_INDEX", "local_data/ocds/kenya-ppra.sqlite"))


def clean_supplier(name):
    raw = name or ""
    cleaned = " ".join(ENUMERATED.sub("", raw).split())
    return cleaned, cleaned != " ".join(raw.split())


def _date(value):
    return value[:10] if isinstance(value, str) and len(value) >= 10 else None


def build_index(sources, target=None):
    """sources: [{"path", "url", "retrieved_at"}]. Rebuilds the index from the gzipped JSONL files."""
    target = Path(target or index_path())
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".building")
    temporary.unlink(missing_ok=True)
    db = sqlite3.connect(temporary)
    db.executescript("""
      CREATE TABLE source (name TEXT PRIMARY KEY, url TEXT, sha256 TEXT, bytes INTEGER, retrieved_at TEXT, records INTEGER);
      CREATE TABLE release (ocid TEXT PRIMARY KEY, release_id TEXT, release_date TEXT, buyer_id TEXT, buyer_name TEXT,
        title TEXT, title_lower TEXT, tender_start TEXT, tender_end TEXT, method TEXT, category TEXT,
        awards TEXT, source_name TEXT, line INTEGER);
      CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
    """)
    amounts, schemes = [], {}
    for source in sources:
        path = Path(source["path"])
        records = 0
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                release = json.loads(line)
                records += 1
                tender = release.get("tender") or {}
                period = tender.get("tenderPeriod") or {}
                for party in release.get("parties") or []:
                    scheme = (party.get("identifier") or {}).get("scheme")
                    schemes[str(scheme)] = schemes.get(str(scheme), 0) + 1
                awards = []
                for position, award in enumerate(release.get("awards") or []):
                    value = award.get("value") or {}
                    contract = award.get("contractPeriod") or {}
                    amount = value.get("amount")
                    if isinstance(amount, (int, float)) and amount > 0:
                        amounts.append(amount)
                    awards.append({"index": position, "id": award.get("id"), "title": award.get("title"),
                                   "amount": None if amount is None else str(amount), "currency": value.get("currency"),
                                   "suppliers": [{"id": s.get("id"), "name": s.get("name")} for s in award.get("suppliers") or []],
                                   "contract_start": _date(contract.get("startDate")), "contract_end": _date(contract.get("endDate"))})
                title = tender.get("title") or ""
                db.execute("INSERT OR REPLACE INTO release VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                    release["ocid"], release.get("id"), release.get("date"),
                    (release.get("buyer") or {}).get("id"), (release.get("buyer") or {}).get("name"),
                    title, title.lower(), period.get("startDate"), period.get("endDate"),
                    tender.get("procurementMethod"), tender.get("mainProcurementCategory"),
                    json.dumps(awards, ensure_ascii=False), path.name, line_number))
        db.execute("INSERT INTO source VALUES (?,?,?,?,?,?)", (
            path.name, source.get("url"), hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_size,
            source.get("retrieved_at"), records))
    amounts.sort()
    p99 = amounts[int(len(amounts) * 0.99)] if amounts else None
    meta = {"dataset": DATASET, "registry_url": REGISTRY_URL, "built_at": datetime.now(timezone.utc).isoformat(),
            "award_amount_p99": None if p99 is None else str(p99), "positive_award_amounts": len(amounts),
            "party_identifier_schemes": schemes}
    db.executemany("INSERT INTO meta VALUES (?,?)", [(k, json.dumps(v)) for k, v in meta.items()])
    db.commit()
    db.close()
    os.replace(temporary, target)
    return meta


def _quartiles(values):
    ordered = sorted(values)
    if not ordered:
        return None
    def at(fraction):
        position = (len(ordered) - 1) * fraction
        low = int(position)
        high = min(low + 1, len(ordered) - 1)
        return ordered[low] + (ordered[high] - ordered[low]) * Decimal(str(position - low))
    return {"q1": str(at(0.25)), "median": str(at(0.5)), "q3": str(at(0.75)), "count": len(ordered)}


def award_history(ocid="", query="", buyer="", limit=10, target=None):
    path = Path(target or index_path())
    if not path.exists():
        return {"status": "SOURCE_UNAVAILABLE", "dataset": DATASET, "records": [],
                "reason": "No local OCDS index. Run: uv run python -m scripts.fetch_ocds"}
    if not (ocid or query.strip()):
        raise ValueError("Provide an OCID or title keywords")
    limit = max(1, min(int(limit), 50))
    db = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        meta = {r["key"]: json.loads(r["value"]) for r in db.execute("SELECT * FROM meta")}
        sources = {r["name"]: dict(r) for r in db.execute("SELECT * FROM source")}
        if ocid:
            rows = db.execute("SELECT * FROM release WHERE ocid=?", (ocid,)).fetchall()
        else:
            words = [w for w in re.split(r"\W+", query.lower()) if len(w) > 2][:6]
            if not words:
                raise ValueError("Title keywords must contain at least one word of three letters or more")
            clauses = " AND ".join("title_lower LIKE ?" for _ in words)
            params = [f"%{w}%" for w in words]
            if buyer:
                clauses += " AND lower(buyer_name) LIKE ?"
                params.append(f"%{buyer.lower()}%")
            rows = db.execute(f"SELECT * FROM release WHERE {clauses} ORDER BY tender_end DESC LIMIT ?",
                              (*params, limit)).fetchall()
    finally:
        db.close()
    p99 = Decimal(meta["award_amount_p99"]) if meta.get("award_amount_p99") else None
    records, usable = [], []
    for row in rows:
        source = sources[row["source_name"]]
        def cite(pointer):
            return {"dataset": DATASET, "file": row["source_name"], "file_sha256": source["sha256"],
                    "line": row["line"], "ocid": row["ocid"], "release_id": row["release_id"], "pointer": pointer}
        flags = []
        start, end = row["tender_start"], row["tender_end"]
        if start and end and start > end:
            flags.append({"flag": "TENDER_PERIOD_INVERTED", "detail": "tenderPeriod.startDate is after endDate",
                          "citation": cite("/tender/tenderPeriod")})
        awards = []
        for award in json.loads(row["awards"]):
            amount = Decimal(award["amount"]) if award["amount"] is not None else None
            award_flags = []
            suppliers = []
            for s in award["suppliers"]:
                cleaned, changed = clean_supplier(s["name"])
                suppliers.append({"id": s["id"], "published_name": s["name"], "normalized_name": cleaned})
                if changed:
                    award_flags.append("SUPPLIER_NAME_HAS_LIST_NUMBER")
            if amount is None:
                award_flags.append("AWARD_VALUE_MISSING")
            elif amount == 0:
                award_flags.append("AWARD_VALUE_ZERO")
            elif p99 is not None and amount > p99:
                award_flags.append("AWARD_VALUE_ABOVE_DATASET_P99")
            # A numbered supplier name is a naming defect; only value defects exclude an award from statistics.
            value_flags = [f for f in award_flags if f.startswith("AWARD_VALUE")]
            if award["currency"] and amount and not value_flags:
                usable.append((award["currency"], amount))
            awards.append({**award, "suppliers": suppliers, "flags": award_flags, "excluded_from_statistics": bool(value_flags),
                           "citation": cite(f"/awards/{award['index']}")})
        records.append({"ocid": row["ocid"], "buyer": row["buyer_name"], "title": row["title"],
                        "closing_date_published": end, "tender_period_start": start, "procurement_method": row["method"],
                        "category": row["category"], "awards": awards, "flags": flags,
                        "citation": cite("/tender/tenderPeriod/endDate")})
    currencies = {c for c, _ in usable}
    summary = {"records": len(records), "awards": sum(len(r["awards"]) for r in records),
               "awards_used_for_statistics": len(usable),
               "awards_excluded_for_value_flags": sum(a["excluded_from_statistics"] for r in records for a in r["awards"]),
               "currency": next(iter(currencies)) if len(currencies) == 1 else None,
               "total_award_value": str(sum(a for _, a in usable)) if len(currencies) == 1 else None,
               "award_value_quartiles": _quartiles([a for _, a in usable]) if len(currencies) == 1 else None}
    return {"status": "FOUND" if records else "NO_MATCH", "dataset": DATASET, "registry_url": REGISTRY_URL,
            "price_note": PRICE_NOTE, "summary": summary, "records": records,
            "dataset_quality": {"award_amount_p99": meta.get("award_amount_p99"),
                                "party_identifier_schemes": meta.get("party_identifier_schemes"),
                                "note": "Supplier identifiers use the portal's internal 'Bidders' scheme, not a company "
                                        "registry, so they cannot establish legal identity. Contact details are not indexed."},
            "sources": list(sources.values())}
