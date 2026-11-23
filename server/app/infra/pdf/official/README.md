# Official claim forms

Put the official, blank claim forms here, then add a map so Haq writes values onto them.

1. Download the blank forms from an official source, for example the Jan Suraksha portal
   (jansuraksha.gov.in, "Forms") or your bank's website. Save them as
   `PMJJBY.pdf`, `PMSBY.pdf` and `RUPAY_PMJDY.pdf` in this folder.
2. From `server/`, render a grid over a form to read off coordinates (in points, origin at
   the top left):
   `uv run python -m scripts.calibrate_form PMJJBY`
   This writes `official/PMJJBY-page<N>-grid.png` for each page.
3. Create `PMJJBY.yaml` like `example.yaml.txt`, with one entry per value. The value keys
   are listed in `app/services/forms/official_values.py`.
4. Download a claim form from the API and check that every value sits in its box.

Without a form and map, Haq generates its own bilingual claim-details form instead.
Both are always included: the official form first, then Haq's details pages.
