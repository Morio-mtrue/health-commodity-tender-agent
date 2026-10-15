"""Original synthetic tender and three original synthetic bids. No real supplier identities."""
import base64
import json
from copy import deepcopy


def request(operator="Demo operator"):
    criteria = [
        {"id":"P01", "stage":"preliminary", "wording":"A signed declaration must be submitted.", "required_evidence":"Signed declaration", "method":"present", "field":"declaration"},
        {"id":"P02", "stage":"preliminary", "wording":"A valid manufacturing certificate must be submitted.", "required_evidence":"Manufacturing certificate", "method":"present", "field":"manufacturing_certificate"},
        {"id":"T01", "stage":"technical", "wording":"The minimum remaining shelf life is 24 months.", "required_evidence":"Shelf life in months", "method":"minimum", "field":"shelf_life_months", "expected":"24"},
        {"id":"T02", "stage":"technical", "wording":"Amoxicillin must be supplied at a strength of 125 mg/5 mL.", "required_evidence":"Amoxicillin strength", "method":"exact", "field":"products.AMOX.strength", "expected":"125 mg/5 mL"},
        {"id":"T03", "stage":"technical", "wording":"The product registration must remain valid on the tender closing date.", "required_evidence":"Submitted registration expiry", "method":"expiry", "field":"registration_expiry"},
        {"id":"F01", "stage":"financial", "wording":"Compare quantity multiplied by submitted unit price to the submitted extended price. Prices are in KES and rounded to 0.01 KES. Normalize the unit price by the declared pack size.", "required_evidence":"Product price schedule", "method":"arithmetic", "field":"products", "expected":'{"currency":"KES","rounding":"0.01"}'},
    ]
    addendum = {"id":"T01A", "stage":"technical", "wording":"The minimum remaining shelf life is amended to 18 months, replacing criterion T01.", "required_evidence":"Shelf life in months", "method":"minimum", "field":"shelf_life_months", "expected":"18", "supersedes":"T01"}
    products = [
        {"item_id":"AMOX", "generic":"Amoxicillin", "strength":"125 mg/5 mL", "dosage_form":"Oral suspension", "base_unit":"mL", "pack_size":"100", "quantity":"500", "unit_price":"120.00", "extended_price":"60000.00", "currency":"KES"},
        {"item_id":"PARA", "generic":"Paracetamol", "strength":"120 mg/5 mL", "dosage_form":"Oral suspension", "base_unit":"mL", "pack_size":"100", "quantity":"400", "unit_price":"80.00", "extended_price":"32000.00", "currency":"KES"},
        {"item_id":"ORS", "generic":"Oral rehydration salts", "strength":"WHO formulation", "dosage_form":"Powder for oral solution", "base_unit":"sachet", "pack_size":"10", "quantity":"100", "unit_price":"150.00", "extended_price":"15000.00", "currency":"KES"},
    ]
    base = {"synthetic":True,"declaration":"Synthetic signed declaration supplied", "manufacturing_certificate":"Synthetic certificate supplied", "shelf_life_months":"20", "registration_expiry":"2027-01-01", "products":products}
    missing = deepcopy(base)
    del missing["manufacturing_certificate"]
    missing["products"][0]["extended_price"] = "59000.00"
    ambiguous = deepcopy(base)
    ambiguous["products"][0]["strength"] = "0.125 g per 5 mL"
    ambiguous["shelf_life_months"] = "16"
    ambiguous["registration_expiry"] = "2024-01-01"
    docs = []
    for name,kind,payload,bidder in [
        ("synthetic-tender.json","tender",{"synthetic":True,"title":"Synthetic oral formulations tender","criteria":criteria},None),
        ("synthetic-addendum.json","addendum",{"synthetic":True,"criteria":[addendum]},None),
        ("synthetic-bid-a.json","bid",base,"BID_A"),
        ("synthetic-bid-b.json","bid",missing,"BID_B"),
        ("synthetic-bid-c.json","bid",ambiguous,"BID_C"),
    ]:
        docs.append({"name":name,"kind":kind,"bidder_id":bidder,"synthetic":True,
                     "content_base64":base64.b64encode(json.dumps(payload,indent=2).encode()).decode()})
    # The public reference is linked for award-history context only. Its archive page says 12 November 2024;
    # the agent compares that declared date with the published OCDS tenderPeriod.endDate.
    return {"name":"Oral formulations · synthetic review", "operator":operator,"closed_on":"2024-11-12",
            "closure_source":"KEMSA archive page for reference KEMSA/OIT05/2024-2026; bids and criteria are synthetic",
            "reference_ocid":"ocds-5whusi-KEMSA/OIT05/2024-2026", "documents":docs}
