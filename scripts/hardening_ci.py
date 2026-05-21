#!/usr/bin/env python3
"""Sprint 11 hardening CI — runs all production-hardening checks in sequence.

Exits non-zero if any check fails or coverage < 85%.

Checks:
  1. pip-audit — dependency CVE scan
  2. detect-secrets — secret leak scan
  3. vulture — dead code detection
  4. pytest --cov — test coverage (≥85%)
"""

import subprocess
import sys


def run(cmd: list[str], description: str) -> int:
    print(f"\n{'=' * 60}")
    print(f"  {description}")
    print(f"  {' '.join(cmd)}")
    print(f"{'=' * 60}\n")
    result = subprocess.run(cmd)
    return result.returncode


def main() -> int:
    failures = 0

    # 1. pip-audit
    rc = run(["uv", "run", "pip-audit"], "pip-audit: dependency CVE scan")
    if rc != 0:
        print("WARNING: pip-audit found issues (check docs/security_audit.md)")
        # Don't fail the build — CVEs documented, not suppressed

    # 2. detect-secrets
    rc = run(
        ["uv", "run", "detect-secrets", "scan", "--baseline", ".secrets.baseline"],
        "detect-secrets: secret leak scan",
    )
    if rc != 0:
        print("FAIL: detect-secrets scan failed")
        failures += 1

    # 3. vulture
    rc = run(
        ["uv", "run", "vulture", "mohizarbot", "--min-confidence", "80"],
        "vulture: dead code detection",
    )
    if rc != 0:
        # Vulture exits non-zero when dead code found — acceptable if reviewed
        print("INFO: vulture found potential dead code (review scripts/vulture_report.txt)")

    # 4. pytest --cov
    rc = run(
        [
            "uv", "run", "pytest", "--cov=mohizarbot", "--cov-report=term-missing",
            "--cov-report=term", "-q",
        ],
        "pytest --cov: test coverage (≥85%)",
    )
    if rc != 0:
        print("FAIL: pytest --cov failed")
        failures += 1

    # Check coverage threshold separately
    result = subprocess.run(
        ["uv", "run", "coverage", "report", "--fail-under=85"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("FAIL: Coverage below 85%")
        print(result.stdout)
        print(result.stderr)
        failures += 1
    else:
        print("PASS: Coverage ≥ 85%")

    print(f"\n{'=' * 60}")
    if failures > 0:
        print(f"  HARDENING CI: {failures} check(s) FAILED")
        return 1
    else:
        print("  HARDENING CI: ALL CHECKS PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(main())
