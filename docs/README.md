# WAA-ADS Demo UI

Static, GitHub Pages-ready UI that demonstrates:
- Landing + docs overview
- Admin-lite demo (run scoring, download CSV)
- Scorecard + evidence viewer

## Run locally

```bash
cd docs
python3 -m http.server 8080
```

Open: http://localhost:8080

## Deploy with GitHub Pages

This repo publishes the `docs/` folder via GitHub Pages.

## Update data

Edit `docs/data/scorecard.sample.json` to reflect new demo runs.
