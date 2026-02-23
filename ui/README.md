# WAA-ADS Demo UI

Static, Netlify-ready UI that demonstrates:
- Landing + docs overview
- Admin-lite demo (run scoring, download CSV)
- Scorecard + evidence viewer

## Run locally

```bash
cd ui
python3 -m http.server 8080
```

Open: http://localhost:8080

## Deploy with Netlify

This repo includes a `netlify.toml` that publishes the `ui/` folder as-is.

1. Connect the repo in Netlify
2. Use these settings:
   - Build command: (leave empty)
   - Publish directory: `ui`
3. Deploy

## Update data

Edit `ui/data/scorecard.sample.json` to reflect new demo runs.
