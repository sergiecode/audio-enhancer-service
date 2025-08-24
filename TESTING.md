# 🧪 Testing Documentation

## Audio Enhancement Service Test Suite
**Created by Sergie Code**

This document provides comprehensive information about the testing framework and methodologies used in the Audio Enhancement Service.

## 📋 Table of Contents

- [Test Structure](#test-structure)
- [Test Categories](#test-categories)
- [Running Tests](#running-tests)
- [Test Configuration](#test-configuration)
- [Coverage Reports](#coverage-reports)
- [Continuous Integration](#continuous-integration)
- [Writing New Tests](#writing-new-tests)

## 🏗️ Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest fixtures and configuration
├── run_tests.py               # Main test runner
├── test_api_endpoints.py      # API endpoint tests
├── test_audio_processing.py   # Audio processing logic tests
├── test_config.py             # Configuration management tests
├── test_integration.py        # End-to-end integration tests
├── test_performance.py        # Performance and load tests
└── test_security.py           # Security vulnerability tests
```

## 🎯 Test Categories

### 1. Unit Tests (`test_*.py`)
- **API Endpoints**: FastAPI route testing
- **Audio Processing**: Core inference logic
- **Configuration**: Settings and environment handling

### 2. Integration Tests (`test_integration.py`)
- End-to-end workflow testing
- Service interaction validation
- Client library testing

### 3. Performance Tests (`test_performance.py`)
- Load testing and scalability
- Memory usage monitoring
- Response time benchmarks
- Concurrent request handling

### 4. Security Tests (`test_security.py`)
- Input validation and sanitization
- File upload security
- Path traversal protection
- DoS attack prevention

## 🚀 Running Tests

### Quick Start

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
python tests/run_tests.py

# Run specific test suite
python tests/run_tests.py --suite quick
```

### Platform-Specific Scripts

**Windows:**
```cmd
run_tests.bat all
run_tests.bat quick
run_tests.bat security
```

**Unix/Linux/macOS:**
```bash
chmod +x run_tests.sh
./run_tests.sh all
./run_tests.sh quick
./run_tests.sh security
```

### Test Suites

| Suite | Description | Command |
|-------|-------------|---------|
| `quick` | Fast unit tests only | `./run_tests.sh quick` |
| `security` | Security vulnerability tests | `./run_tests.sh security` |
| `performance` | Performance and load tests | `./run_tests.sh performance` |
| `integration` | End-to-end integration tests | `./run_tests.sh integration` |
| `coverage` | Tests with coverage reporting | `./run_tests.sh coverage` |
| `lint` | Code quality checks | `./run_tests.sh lint` |
| `all` | Complete test suite | `./run_tests.sh all` |

### Direct Pytest Commands

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api_endpoints.py -v

# Run tests matching pattern
pytest tests/ -k "test_process_audio" -v

# Run tests with specific markers
pytest tests/ -m "not slow" -v
```

## ⚙️ Test Configuration

### Pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
minversion = 6.0
addopts = -ra -q --strict-markers
testpaths = tests
asyncio_mode = auto
timeout = 300
```

### Custom Markers

- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.security` - Security tests
- `@pytest.mark.performance` - Performance tests

### Fixtures (`conftest.py`)

Common fixtures available in all tests:

- `client` - FastAPI test client
- `temp_dir` - Temporary directory for test files
- `sample_audio_file` - Valid WAV audio file
- `large_audio_file` - Large audio file for testing
- `invalid_file` - Non-audio file for validation testing

## 📊 Coverage Reports

### Generate Coverage Report

```bash
# Terminal coverage report
pytest tests/ --cov=app --cov-report=term-missing

# HTML coverage report
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser

# XML coverage report (for CI)
pytest tests/ --cov=app --cov-report=xml
```

### Coverage Targets

- **Minimum Coverage**: 80%
- **Target Coverage**: 90%+
- **Critical Modules**: 95%+

## 🔄 Continuous Integration

### GitHub Actions Workflow

The CI pipeline runs automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main`

### CI Test Matrix

- **Operating Systems**: Ubuntu, Windows, macOS
- **Python Versions**: 3.9, 3.10, 3.11
- **Test Categories**: Unit, Integration, Security, Performance

### CI Stages

1. **Code Quality**
   - Linting with flake8
   - Type checking with mypy
   - Format checking with black

2. **Unit Testing**
   - Fast unit tests
   - Security tests
   - Configuration tests

3. **Integration Testing**
   - Service startup
   - End-to-end workflows
   - API integration

4. **Docker Testing**
   - Container build
   - Service health checks
   - Basic functionality

5. **Security Scanning**
   - Dependency vulnerability scan
   - Code security analysis

## ✍️ Writing New Tests

### Test File Naming

```
test_<module_name>.py
```

### Test Function Naming

```python
def test_<functionality>_<scenario>():
    """Test description"""
    pass
```

### Example Test Structure

```python
"""
Test Module Documentation
Created by Sergie Code
"""

import pytest
from unittest.mock import patch

class TestFeatureName:
    """Test class for specific feature"""
    
    @pytest.fixture
    def setup_data(self):
        """Setup test data"""
        return {"key": "value"}
    
    def test_positive_scenario(self, setup_data):
        """Test successful execution"""
        # Arrange
        input_data = setup_data
        
        # Act
        result = function_under_test(input_data)
        
        # Assert
        assert result is not None
        assert result["status"] == "success"
    
    def test_negative_scenario(self):
        """Test error handling"""
        with pytest.raises(ValueError):
            function_under_test(invalid_input)
    
    @pytest.mark.asyncio
    async def test_async_function(self):
        """Test async functionality"""
        result = await async_function()
        assert result is not None
```

### Best Practices

1. **Arrange-Act-Assert**: Structure tests clearly
2. **Descriptive Names**: Make test purpose obvious
3. **Independent Tests**: No dependencies between tests
4. **Mock External Dependencies**: Use mocks for external services
5. **Test Edge Cases**: Include boundary conditions
6. **Error Testing**: Test error handling paths

### Async Testing

```python
@pytest.mark.asyncio
async def test_async_audio_processing():
    """Test async audio processing"""
    result = await process_audio(input_file, output_file)
    assert result["success"] is True
```

### Mocking Examples

```python
@patch('app.inference.audio_enhancer.enhance_audio')
async def test_with_mock(mock_enhance):
    """Test with mocked dependencies"""
    mock_enhance.return_value = {"status": "success"}
    
    result = await process_audio("input.wav", "output.wav")
    assert result["status"] == "success"
    mock_enhance.assert_called_once()
```

## 🔧 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure project root is in Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **Async Test Issues**
   ```python
   # Use pytest-asyncio
   pip install pytest-asyncio
   ```

3. **File Permission Errors**
   ```bash
   # Ensure test directories are writable
   chmod 755 test_uploads test_outputs
   ```

4. **Service Not Running (Integration Tests)**
   ```bash
   # Start service before integration tests
   uvicorn app.main:app --host 0.0.0.0 --port 8000 &
   ```

### Debug Mode

```bash
# Run tests with debug output
pytest tests/ -v -s --tb=long

# Run single test with debugging
pytest tests/test_api_endpoints.py::TestRootEndpoint::test_root_endpoint_success -v -s
```

## 📈 Performance Testing

### Load Testing

```python
@pytest.mark.performance
def test_concurrent_processing():
    """Test service under load"""
    # Simulate multiple concurrent requests
    pass
```

### Memory Testing

```python
def test_memory_usage():
    """Monitor memory usage during processing"""
    import psutil
    
    initial_memory = psutil.Process().memory_info().rss
    # Perform operations
    final_memory = psutil.Process().memory_info().rss
    
    assert final_memory - initial_memory < threshold
```

## 🔒 Security Testing

### Input Validation

```python
def test_malicious_input_handling():
    """Test handling of malicious inputs"""
    malicious_inputs = [
        "../../../etc/passwd",
        "<script>alert('xss')</script>",
        "'; DROP TABLE users; --"
    ]
    
    for malicious_input in malicious_inputs:
        # Test that input is properly sanitized
        pass
```

### File Upload Security

```python
def test_file_upload_security():
    """Test file upload security measures"""
    # Test various attack vectors
    pass
```

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)

---

**Created with ❤️ by Sergie Code for the developer and musician community**
