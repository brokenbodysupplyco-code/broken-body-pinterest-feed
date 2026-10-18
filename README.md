# BROKEN BODY™ Pinterest feed

## Setup

1. Store Fourthwall Open API Basic credentials in GitHub Actions secrets `FOURTHWALL_API_USER` and `FOURTHWALL_API_PASSWORD`. Never put credentials in files.
2. Upload `feed.py`, `requirements.txt`, and `.github/workflows/update-feed.yml` preserving the workflow folder path.
3. Enable GitHub Actions and set workflow permissions to **Read and write permissions** in Settings → Actions → General.
4. Run **Actions → Update Pinterest product feed → Run workflow**. If Fourthwall rejects Basic auth, the job fails safely and does not publish a feed. This API's separate help documentation describes Bearer authentication, so that result needs investigation rather than guessing.
5. If the run succeeds, inspect `docs/products.csv` for correct product links, images, prices, and product eligibility. Do not submit to Pinterest until verified.
6. Enable **Settings → Pages → Deploy from a branch**, branch `main`, folder `/docs`. Once published, the feed URL should be `https://brokenbodysupplyco-code.github.io/broken-body-pinterest-feed/products.csv`.
7. Add that URL to Pinterest Catalogs only after validating the file and Pinterest's current requirements.

This starter uses product-level rows, not variant-level rows. Pinterest requirements and product URL shapes still need validation. The repository and feed are public; credentials remain GitHub secrets.
