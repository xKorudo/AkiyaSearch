# One-shot: scrape fresh data, backfill photos, build the static snapshot,
# and deploy it to Cloudflare Pages. Run manually or via Task Scheduler.
#
#   powershell -ExecutionPolicy Bypass -File deploy.ps1
#
$ErrorActionPreference = "Continue"
Set-Location -Path $PSScriptRoot

Write-Host "== 1/4 Scraping (incremental) =="
python run_pipeline.py

Write-Host "== 2/4 Backfilling detail-page photos =="
python enrich_images.py 80

Write-Host "== 3/4 Building static snapshot (public/) =="
python export_static.py

Write-Host "== 4/4 Deploying to Cloudflare Pages =="
wrangler pages deploy public --project-name=akiya-finder

Write-Host "== Done =="
