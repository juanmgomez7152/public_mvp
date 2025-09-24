@echo off
REM Quick Test Runner for Windows
REM This batch file makes it easy to run tests on Windows

echo ========================================
echo Omnicom MVP Test Suite
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Python detected: 
python --version
echo.

REM Check if we're in the right directory
if not exist "tests\run_tests.py" (
    echo ERROR: Please run this script from the project root directory
    echo Expected to find: tests\run_tests.py
    pause
    exit /b 1
)

echo Running tests...
echo ========================================
echo.

REM Run tests with our custom test runner
python tests\run_tests.py %*

echo.
echo ========================================
echo Test run completed!
echo.

REM Show coverage report if coverage was used
if exist "htmlcov\index.html" (
    echo HTML coverage report generated: htmlcov\index.html
    echo.
    set /p choice="Open coverage report in browser? (y/N): "
    if /i "%choice%"=="y" (
        start htmlcov\index.html
    )
)

echo.
echo Usage examples:
echo   run_tests.bat                    - Run all tests
echo   run_tests.bat --unit             - Run unit tests only
echo   run_tests.bat --integration      - Run integration tests only
echo   run_tests.bat --coverage         - Run with coverage report
echo   run_tests.bat --verbose          - Run with verbose output
echo.

pause