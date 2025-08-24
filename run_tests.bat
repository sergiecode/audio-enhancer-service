@echo off
REM Test execution script for Audio Enhancement Service (Windows)
REM Created by Sergie Code

echo 🧪 Audio Enhancement Service - Test Execution Script
echo ====================================================

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt
pip install -r requirements-test.txt

REM Create necessary directories
echo 📁 Creating test directories...
if not exist "test_uploads" mkdir test_uploads
if not exist "test_outputs" mkdir test_outputs
if not exist "test_models" mkdir test_models
if not exist "logs" mkdir logs

REM Run different test suites based on argument
if "%1"=="quick" (
    echo ⚡ Running quick tests...
    python tests\run_tests.py --suite quick
) else if "%1"=="security" (
    echo 🔒 Running security tests...
    python tests\run_tests.py --suite security
) else if "%1"=="performance" (
    echo 🚀 Running performance tests...
    python tests\run_tests.py --suite performance
) else if "%1"=="integration" (
    echo 🔗 Running integration tests...
    echo ⚠️  Note: Integration tests require the service to be running!
    echo Start service with: uvicorn app.main:app --host 0.0.0.0 --port 8000
    python tests\run_tests.py --suite integration
) else if "%1"=="coverage" (
    echo 📊 Running tests with coverage...
    pytest tests\ --cov=app --cov-report=html --cov-report=term-missing
    echo ✅ Coverage report generated in htmlcov\index.html
) else if "%1"=="lint" (
    echo 🔍 Running code quality checks...
    black --check app\ tests\
    flake8 app\ tests\
    mypy app\
    echo ✅ Code quality checks completed
) else if "%1"=="all" (
    echo 🧪 Running complete test suite...
    python tests\run_tests.py --suite all
) else (
    echo Usage: %0 {quick^|security^|performance^|integration^|coverage^|lint^|all}
    echo.
    echo Test suites:
    echo   quick       - Fast unit tests only
    echo   security    - Security vulnerability tests
    echo   performance - Performance and load tests
    echo   integration - End-to-end integration tests
    echo   coverage    - Run tests with coverage reporting
    echo   lint        - Code quality and style checks
    echo   all         - Complete test suite
    goto :end
)

REM Check exit code
if %ERRORLEVEL% EQU 0 (
    echo ✅ Tests completed successfully!
) else (
    echo ❌ Tests failed!
    exit /b 1
)

:end
