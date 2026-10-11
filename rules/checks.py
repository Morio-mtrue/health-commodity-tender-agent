from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from mcp_server.schemas.models import ProductLine


def financial_check(line: ProductLine, rule: dict):
    """Check submitted arithmetic, never replace a price or silently assume FX."""
    precision = Decimal(rule.get("rounding", "0.01"))
    expected_total = (line.quantity * line.unit_price).quantize(precision, rounding=ROUND_HALF_UP)
    normalized = line.unit_price / line.pack_size
    result = {"item_id": line.item_id, "submitted_unit_price": str(line.unit_price),
              "submitted_extended_price": str(line.extended_price), "quantity": str(line.quantity),
              "pack_size": str(line.pack_size), "base_unit": line.base_unit,
              "calculated_extended_price": str(expected_total),
              "normalized_price_per_base_unit": str(normalized), "currency": line.currency,
              "formula": "quantity × submitted unit price; unit price ÷ pack size",
              "discrepancy": expected_total != line.extended_price, "status": "SUPPORTED"}
    target = rule.get("currency", line.currency)
    if line.currency != target:
        fx = rule.get("fx", {}).get(line.currency)
        if not fx or not all(fx.get(k) for k in ("rate", "date", "source", "method")) or fx.get("method") != "multiply":
            result.update(status="UNRESOLVED", reason="Tender-specified currency conversion rule is missing")
        else:
            rate = Decimal(fx["rate"])
            if not rate.is_finite() or rate <= 0:
                raise ValueError("FX rate must be finite and positive")
            result.update(converted_currency=target, fx=fx,
                          converted_observed_price=str((expected_total * rate).quantize(precision, rounding=ROUND_HALF_UP)))
    if result["discrepancy"] and result["status"] == "SUPPORTED":
        result["status"] = "UNSUPPORTED"
    return result


def field_value(data, path):
    value = data
    for part in path.split("."):
        if isinstance(value, list):
            value = next((row for row in value if isinstance(row, dict) and row.get("item_id") == part), None)
        elif isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return value


def evaluate_value(method, value, expected, as_of):
    if value is None or value == "":
        return "UNSUPPORTED", "Required submitted evidence is absent from the inspected bid inventory."
    if method == "manual":
        return "UNRESOLVED", "Evidence is present and requires human interpretation."
    if method == "present":
        return "SUPPORTED", "Required evidence is present in the submitted document; authenticity is not established."
    if method == "exact":
        if str(value).strip().casefold() == expected.strip().casefold():
            return "SUPPORTED", "Submitted value matches the locked requirement."
        return "UNRESOLVED", "Submitted wording differs from the locked requirement; equivalence needs human review."
    try:
        if method == "minimum":
            actual, minimum = Decimal(str(value)), Decimal(expected)
            if not actual.is_finite() or not minimum.is_finite():
                raise ValueError("Non-finite value")
            return ("SUPPORTED", "Submitted value meets the published minimum.") if actual >= minimum else (
                "UNSUPPORTED", "Submitted value is below the published minimum.")
        if method == "expiry":
            actual = date.fromisoformat(str(value))
            return ("SUPPORTED", "Submitted expiry is on or after the tender reference date.") if actual >= date.fromisoformat(as_of) else (
                "UNSUPPORTED", "Submitted expiry precedes the tender reference date; committee review is required.")
    except (ValueError, InvalidOperation):
        return "UNRESOLVED", "Submitted value cannot be interpreted safely using the locked rule."
    return "UNRESOLVED", "Unsupported evaluation method."
