"""Run search_award_history over every real KEMSA contracting process in the local OCDS index.

uv run python -m scripts.ocds_sweep
Checks the tool on messy public data: no crashes, every award cited, contact details absent.
"""
import json
import sqlite3
import time
from collections import Counter
from pathlib import Path

from connectors.ocds import award_history, index_path

KEMSA_BUYER_ID = "5098"


def main():
    db = sqlite3.connect(index_path())
    ocids = [r[0] for r in db.execute("SELECT ocid FROM release WHERE buyer_id=? ORDER BY ocid", (KEMSA_BUYER_ID,))]
    dump_has_contacts = any("contactPoint" in r[0] for r in db.execute("SELECT awards FROM release"))
    db.close()
    flags, errors, uncited = Counter(), [], 0
    records = awards = with_awards = 0
    started = time.monotonic()
    for ocid in ocids:
        try:
            result = award_history(ocid=ocid)
        except Exception as error:
            errors.append({"ocid": ocid, "error": f"{type(error).__name__}: {error}"})
            continue
        for record in result["records"]:
            records += 1
            with_awards += bool(record["awards"])
            flags.update(f["flag"] for f in record["flags"])
            for award in record["awards"]:
                awards += 1
                flags.update(award["flags"])
                citation = award["citation"]
                if not (citation["file_sha256"] and citation["line"] and citation["pointer"].startswith("/awards/")):
                    uncited += 1
    summary = {"buyer": "Kenya Medical Supplies Authority (buyer id 5098)", "ocids": len(ocids), "records": records,
               "records_with_awards": with_awards, "awards": awards, "flags": dict(flags), "errors": errors,
               "awards_without_full_citation": uncited, "contact_points_in_index": dump_has_contacts,
               "seconds": round(time.monotonic() - started, 2)}
    Path("outputs/ocds-sweep-result.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
