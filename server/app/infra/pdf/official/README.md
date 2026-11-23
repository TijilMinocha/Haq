# Official claim forms

Blank official claim forms that Haq fills in. Where each came from is in `SOURCES.md`.

| Scheme | Form | Map |
|---|---|---|
| PMJJBY | `pmjjby.pdf` | `PMJJBY.yaml` |
| PMSBY | `pmsby.pdf` | `PMSBY.yaml` |
| RuPay PMJDY | `rupay_pmjdy.pdf` | `RUPAY_PMJDY.yaml` |

`enrolment/` holds the scheme **enrolment** forms (consent-cum-declaration). They are for
re-joining a lapsed scheme, never for claims.

A claim-form download returns the filled official form first, then Haq's bilingual
claim-details pages (deadline, blockers, evidence, checklist). If a form or its map is
missing, only Haq's pages are returned.

## Updating a form (for example, a new financial year's RuPay form)

1. Replace the PDF here and update `SOURCES.md`.
2. Write the map like `example.yaml.txt`. Anchor each value to its printed label where the
   PDF has selectable text; the value keys are in `app/services/forms/official_values.py`.
3. Only for labels that are not text (scanned forms), read coordinates off a grid:
   `uv run python -m scripts.calibrate_form PMJJBY` (from `server/`) writes
   `PMJJBY-page<N>-grid.png` here. These images are gitignored.
4. Run the tests: `tests/unit/forms/test_official_forms.py` fails if any anchor is missing.
   Then download a filled form and check that every value sits in its box.
