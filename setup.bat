@echo off
echo Installing Python dependencies...
python -m pip install -r requirements.txt

echo Installing Playwright browsers...
python -m playwright install chromium

echo Setup complete! You can now start the backend server with:
echo uvicorn backend.app:app --reload
