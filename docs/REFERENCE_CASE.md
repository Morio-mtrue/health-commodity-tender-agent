# Selected public reference case

**KEMSA/OIT05/2024-2026:** Supply of Health Products (Liquid Dosage Forms, Inhalation Products and Topical Formulations).

Source: https://kemsa.go.ke/tender/view/kemsa-oit05-2024-2026

The official archive, inspected on 10 October 2026, marks the case closed on 12 November 2024. It lists the original tender uploaded 15 October 2024, Addendum 1 uploaded 25 October, and Addendum 2 uploaded 2 November.

The official extension notice dated 1 November 2024 lists a new closing date of 13 November 2024 for this reference. Both dates are in the past, so this is a closed-tender candidate, but **the exact applicable closing timestamp remains unresolved** until all original/addendum documents are reconciled. Do not silently choose the archive date for date-sensitive checks.

Identified official source URLs:
- Original: https://kemsa.go.ke/download/file/747e605cfecae01cf9a53102136d681d.pdf
- Extension: https://kemsa.go.ke/download/file/a85fa50f20d8655dd811155fb22b34d2.pdf
- Addendum 1: https://kemsa.go.ke/download/file/cdf1c6c2bd8e468a3843cd45f1181ff7.pdf
- Addendum 2: https://kemsa.go.ke/download/file/49dfc23a66ba0983f8798f6db435a7a9.pdf
- Original PPIP mirror: https://tenders.go.ke/storage/Documents/1728986416665-supply-of-health-products-liquid-dosage-forms-inhalation-products-and-topical-formulations.pdf

Automated downloads encountered a portal timeout. Web retrieval of the download URLs also rejected the server's application/octet-stream response. The documents have not been used to make evaluation findings.

Run `uv run python -m scripts.fetch_reference` to attempt all four official documents into ignored `local_data/`. `--only addendum-1.pdf addendum-2.pdf` selects particular files. All four official downloads timed out on this computer on 11 October 2026. A successfully downloaded original plus one extension is **not** proof that every applicable addendum has been retrieved; compare with the archive and retain all versions.

The included demo is an original synthetic tender with original synthetic bids. Its criteria, shelf-life amendment, prices, registrations, and missing-evidence labels are fictitious. It is not a transcription or official evaluation of this KEMSA tender. Three candidate oral product lines will be chosen from the actual schedule after successful retrieval; the synthetic fixture product names are not asserted to be line items in this public reference.

## Published OCDS record (checked 15 October 2026)

The Kenya PPRA OCDS publication (OCP Data Registry publication 147, file `2024.jsonl.gz`, SHA-256 `02f59043ad1b72f103720479981cecdf79dcffd66a07f7db9fbe20b51a49a808`, line 23962) carries this tender as `ocds-5whusi-KEMSA/OIT05/2024-2026`:

- `tender/tenderPeriod/endDate`: **2024-11-13T00:00:00+03:00**, which agrees with the extension notice and differs from the archive page (12 November).
- `tender/tenderPeriod/startDate`: 2024-11-06, later than the 15 October upload date, so the start field is not reliable.
- Eight awards, all KES, total **45,188,853**, contract periods from March or April 2025 to March or April 2027. Seven of the eight supplier names carry list numbers (for example `17.	Laboratory & Allied Ltd`).

The workbench links the synthetic demo case to this OCID. `search_award_history` reports the 12 versus 13 November difference as an unresolved, cited observation for the committee; it does not pick a date. The awards are public context and are never used as findings against any supplier.
