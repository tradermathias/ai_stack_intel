@echo off
REM Quick .env setup script for agentic_trust_dashboard (Windows)

echo.
echo 🚀 Agentic Trust Dashboard - Environment Setup (Windows)
echo ======================================================
echo.

REM Check if .env already exists
if exist ".env" (
    echo ⚠️  .env file already exists!
    set /p overwrite="Do you want to overwrite it? (y/n): "
    if /i not "!overwrite!"=="y" (
        echo Keeping existing .env file
        exit /b 0
    )
)

echo 📝 Creating .env file...
echo.

REM Prompt user for API key
set /p api_key="Paste your Anthropic API key (from https://console.anthropic.com/): "

REM Validate input
if "!api_key!"=="" (
    echo ❌ Error: API key cannot be empty!
    exit /b 1
)

REM Create .env file
(
    echo # Anthropic API Configuration
    echo # Generated: %date% %time%
    echo ANTHROPIC_API_KEY=%api_key%
) > .env

echo.
echo ✅ .env file created successfully!
echo.
echo 📋 File contents:
echo    ANTHROPIC_API_KEY=****** (hidden for security)
echo.
echo 🔒 Security reminder:
echo    ✓ .env is in .gitignore (won't be committed)
echo    ✓ Never share your .env file
echo    ✓ Rotate key if exposed
echo.
echo Ready to run: python agentic_trust_dashboard.py
echo.
pause
