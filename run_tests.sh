#!/bin/bash

# Test execution script for Audio Enhancement Service
# Created by Sergie Code

echo "🧪 Audio Enhancement Service - Test Execution Script"
echo "===================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
print_status "Installing dependencies..."
pip install -r requirements.txt
pip install -r requirements-test.txt

# Create necessary directories
print_status "Creating test directories..."
mkdir -p test_uploads test_outputs test_models logs

# Run different test suites based on argument
case "$1" in
    "quick")
        print_status "Running quick tests..."
        python tests/run_tests.py --suite quick
        ;;
    "security")
        print_status "Running security tests..."
        python tests/run_tests.py --suite security
        ;;
    "performance")
        print_status "Running performance tests..."
        python tests/run_tests.py --suite performance
        ;;
    "integration")
        print_status "Running integration tests..."
        print_warning "Note: Integration tests require the service to be running!"
        print_status "Start service with: uvicorn app.main:app --host 0.0.0.0 --port 8000"
        python tests/run_tests.py --suite integration
        ;;
    "coverage")
        print_status "Running tests with coverage..."
        pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
        print_success "Coverage report generated in htmlcov/index.html"
        ;;
    "lint")
        print_status "Running code quality checks..."
        black --check app/ tests/
        flake8 app/ tests/
        mypy app/
        print_success "Code quality checks completed"
        ;;
    "all")
        print_status "Running complete test suite..."
        python tests/run_tests.py --suite all
        ;;
    *)
        echo "Usage: $0 {quick|security|performance|integration|coverage|lint|all}"
        echo ""
        echo "Test suites:"
        echo "  quick       - Fast unit tests only"
        echo "  security    - Security vulnerability tests"
        echo "  performance - Performance and load tests"
        echo "  integration - End-to-end integration tests"
        echo "  coverage    - Run tests with coverage reporting"
        echo "  lint        - Code quality and style checks"
        echo "  all         - Complete test suite"
        exit 1
        ;;
esac

# Check exit code
if [ $? -eq 0 ]; then
    print_success "Tests completed successfully!"
else
    print_error "Tests failed!"
    exit 1
fi
