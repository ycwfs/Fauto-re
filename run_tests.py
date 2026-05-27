"""
Run all tests with coverage report.

Usage:
    python run_tests.py
    python run_tests.py --verbose
    python run_tests.py --coverage
"""
import sys
import subprocess


def run_tests(verbose=False, coverage=False):
    """Run pytest with appropriate flags."""
    cmd = ["pytest"]

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=80",
        ])

    # Run tests
    result = subprocess.run(cmd, cwd="backend")
    return result.returncode


def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    coverage = "--coverage" in sys.argv or "-c" in sys.argv

    print("=" * 70)
    print("Running Full-Auto-Research Test Suite")
    print("=" * 70)

    exit_code = run_tests(verbose=verbose, coverage=coverage)

    if exit_code == 0:
        print("\n" + "=" * 70)
        print("✅ All tests passed!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("❌ Some tests failed!")
        print("=" * 70)

    if coverage:
        print("\n📊 Coverage report generated at: backend/htmlcov/index.html")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
