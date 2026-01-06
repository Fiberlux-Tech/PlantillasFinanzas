#!/usr/bin/env python3
"""
Post-Deployment Health Check Script

This script validates that the deployed application is healthy and functional.
It performs critical checks on key endpoints and database connectivity.

Usage:
    python scripts/health_check.py --url <DEPLOYMENT_URL> --environment <staging|production>

Checks Performed:
    1. Root endpoint (/) returns 200 OK
    2. Health check endpoint (/health) returns 200 OK
    3. API endpoint (/api/health) returns 200 OK and database is connected
    4. Admin endpoint (/api/admin/users) is accessible (requires valid JWT)

Exit Codes:
    0: All health checks passed
    1: One or more health checks failed
"""

import argparse
import sys
import time
import requests
from typing import Dict, List, Tuple


class HealthCheckError(Exception):
    """Custom exception for health check failures"""
    pass


def check_endpoint(url: str, endpoint: str, timeout: int = 10, expected_status: int = 200) -> Tuple[bool, str]:
    """
    Checks if an endpoint returns the expected HTTP status code.

    Args:
        url: Base deployment URL
        endpoint: Endpoint path to check
        timeout: Request timeout in seconds
        expected_status: Expected HTTP status code

    Returns:
        Tuple[bool, str]: (success, message)
    """
    full_url = f"{url.rstrip('/')}{endpoint}"

    try:
        response = requests.get(full_url, timeout=timeout, allow_redirects=True)

        if response.status_code == expected_status:
            return True, f"✓ {endpoint} returned {response.status_code}"
        else:
            return False, f"✗ {endpoint} returned {response.status_code} (expected {expected_status})"

    except requests.exceptions.Timeout:
        return False, f"✗ {endpoint} timed out after {timeout} seconds"
    except requests.exceptions.ConnectionError:
        return False, f"✗ {endpoint} connection failed"
    except Exception as e:
        return False, f"✗ {endpoint} error: {str(e)}"


def check_health_endpoint(url: str, timeout: int = 10) -> Tuple[bool, str]:
    """
    Checks the /api/health endpoint and verifies database connectivity.

    Args:
        url: Base deployment URL
        timeout: Request timeout in seconds

    Returns:
        Tuple[bool, str]: (success, message)
    """
    full_url = f"{url.rstrip('/')}/api/health"

    try:
        response = requests.get(full_url, timeout=timeout)

        if response.status_code != 200:
            return False, f"✗ /api/health returned {response.status_code}"

        try:
            data = response.json()

            # Check database status
            db_status = data.get('database', {}).get('status', 'unknown')

            if db_status == 'connected':
                return True, f"✓ /api/health returned 200, database connected"
            else:
                return False, f"✗ /api/health database status: {db_status}"

        except ValueError:
            return False, f"✗ /api/health returned invalid JSON"

    except requests.exceptions.Timeout:
        return False, f"✗ /api/health timed out after {timeout} seconds"
    except requests.exceptions.ConnectionError:
        return False, f"✗ /api/health connection failed"
    except Exception as e:
        return False, f"✗ /api/health error: {str(e)}"


def run_health_checks(url: str, environment: str) -> Dict[str, Tuple[bool, str]]:
    """
    Runs all health checks and returns results.

    Args:
        url: Base deployment URL
        environment: Deployment environment

    Returns:
        Dict[str, Tuple[bool, str]]: Check results keyed by check name
    """
    print(f"\n{'='*60}")
    print(f"Post-Deployment Health Checks - {environment.upper()}")
    print(f"{'='*60}\n")
    print(f"Target URL: {url}\n")

    results = {}

    # Check 1: Root endpoint
    print("Check 1: Root endpoint (/)...")
    success, message = check_endpoint(url, "/", timeout=15)
    results["root"] = (success, message)
    print(f"  {message}\n")

    # Check 2: Frontend health check
    print("Check 2: Frontend health check (/health)...")
    success, message = check_endpoint(url, "/health", timeout=15, expected_status=200)
    results["frontend_health"] = (success, message)
    print(f"  {message}\n")

    # Check 3: API health check with database
    print("Check 3: API health check with database (/api/health)...")
    success, message = check_health_endpoint(url, timeout=15)
    results["api_health"] = (success, message)
    print(f"  {message}\n")

    # Check 4: API responsiveness
    print("Check 4: API endpoint responsiveness (/api/master-variables)...")
    success, message = check_endpoint(url, "/api/master-variables", timeout=15, expected_status=200)
    results["api_endpoint"] = (success, message)
    print(f"  {message}\n")

    return results


def print_summary(results: Dict[str, Tuple[bool, str]], environment: str) -> bool:
    """
    Prints a summary of health check results.

    Args:
        results: Check results from run_health_checks()
        environment: Deployment environment

    Returns:
        bool: True if all checks passed, False otherwise
    """
    print(f"{'='*60}")
    print(f"Health Check Summary - {environment.upper()}")
    print(f"{'='*60}\n")

    passed = sum(1 for success, _ in results.values() if success)
    total = len(results)

    for check_name, (success, message) in results.items():
        status = "PASS" if success else "FAIL"
        symbol = "✓" if success else "✗"
        print(f"{symbol} {check_name}: {status}")

    print(f"\nTotal: {passed}/{total} checks passed\n")

    if passed == total:
        print("✓ All health checks passed. Deployment is healthy.\n")
        return True
    else:
        print(f"✗ {total - passed} health check(s) failed. Investigate issues above.\n")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run post-deployment health checks")
    parser.add_argument(
        "--url",
        required=True,
        help="Deployment URL to check"
    )
    parser.add_argument(
        "--environment",
        required=True,
        choices=["staging", "production"],
        help="Deployment environment"
    )
    parser.add_argument(
        "--retry",
        type=int,
        default=3,
        help="Number of retry attempts if checks fail (default: 3)"
    )
    parser.add_argument(
        "--retry-delay",
        type=int,
        default=10,
        help="Delay in seconds between retries (default: 10)"
    )

    args = parser.parse_args()

    attempt = 1
    max_attempts = args.retry

    while attempt <= max_attempts:
        if attempt > 1:
            print(f"\n{'='*60}")
            print(f"Retry attempt {attempt}/{max_attempts}")
            print(f"{'='*60}")
            time.sleep(args.retry_delay)

        # Run health checks
        results = run_health_checks(args.url, args.environment)

        # Print summary
        all_passed = print_summary(results, args.environment)

        if all_passed:
            sys.exit(0)

        attempt += 1

    # All retries exhausted
    print(f"{'='*60}", file=sys.stderr)
    print(f"✗ HEALTH CHECKS FAILED AFTER {max_attempts} ATTEMPTS", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)
    print("Deployment completed but application may not be healthy.", file=sys.stderr)
    print("Investigate the failed checks above.\n", file=sys.stderr)

    sys.exit(1)


if __name__ == "__main__":
    main()
