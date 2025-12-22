# MEIH Automated Deployment Workflow
# This script runs tests first. If they pass, it pushes to GitHub to trigger Render/Vercel.

Write-Host "`n[1/3] Running Automated Tests..." -ForegroundColor Cyan
python test_suite.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nTests Passed! Preparing for Deployment..." -ForegroundColor Green
    
    Write-Host "`n[2/3] Adding changes to Git..." -ForegroundColor Cyan
    git add .
    
    $commitMsg = "Automated Production Update: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    git commit -m $commitMsg
    
    Write-Host "`n[3/3] Pushing to Repository..." -ForegroundColor Cyan
    git push origin main
    
    Write-Host "`nDEPLOYMENT TRIGGERED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "Monitor your Render Dashboard: https://dashboard.render.com"
}
else {
    Write-Host "`nDEPLOYMENT ABORTED: One or more tests failed." -ForegroundColor Red
    Write-Host "Please fix the scraper logic or IP blocking issues before trying again." -ForegroundColor Yellow
}
