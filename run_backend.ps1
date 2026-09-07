Write-Host "Starting Automated MoM Generator Backend on http://localhost:8000..." -ForegroundColor Cyan
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
