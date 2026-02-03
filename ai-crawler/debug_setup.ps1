# Debug Setup Script
Write-Host "Setting up local environment for TeacherHub Crawler..."

# Check Python
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed. Please install Python 3.10+ and try again."
    exit 1
}

# Install Deps
Write-Host "Installing Python dependencies..."
python -m pip install -r requirements.txt

# Install Playwright Browsers
Write-Host "Installing Playwright browsers..."
python -m playwright install chromium

Write-Host "Setup Complete!"
Write-Host "Run 'python src/debug_local.py' to start crawling."
