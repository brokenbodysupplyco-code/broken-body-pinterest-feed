# BROKEN BODY™ Pinterest product feed

Generates a product feed from Fourthwall's Product Offer API using GitHub Actions.

## Setup
1. In Fourthwall, open **Settings → For Developers → OpenAPI** and generate an OpenAPI credential. Do not share or paste it in chat.
2. In GitHub, open **Settings → Secrets and variables → Actions → New repository secret**. Name it `FOURTHWALL_API_KEY` and paste the credential there.
3. Enable Actions workflows and allow workflow write permissions in **Settings → Actions → General → Workflow permissions**.
4. Run **Actions → Update Pinterest product feed → Run workflow**.
5. Review the generated `public/products.csv` and check that the URLs and prices are correct before submitting to Pinterest.
6. In **Settings → Pages**, deploy from branch `main`, folder `/docs` (or change output to `docs/products.csv`). GitHub Pages does not support deploying from `/public` using branch mode. Recommended: use GitHub Pages GitHub Actions deployment workflow instead.

**Note:** This is a starter scaffold, not a verified Pinterest-ready integration. The Fourthwall Product Offer API field names for product URLs and images, and Pinterest's current required catalog fields and validation rules, must be confirmed with real API responses before activation. It intentionally refuses to publish an empty feed.
