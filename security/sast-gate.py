#!/usr/bin/env python3
"""
Evaluates a Semgrep JSON report against a severity threshold and exits
non-zero if the count of ERROR-severity (critical/high) findings exceeds
the allowed maximum. Also prints a short human-readable summary for the
Jenkins console log.

Usage:
    python3 sast-gate.py semgrep-report.json --max-error 0 --max-warning 10
"""
import json
import sys
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report", help="Path to semgrep JSON report")
    parser.add_argument("--max-error", type=int, default=0,
                         help="Max allowed ERROR-severity findings (critical/high). Default: 0")
    parser.add_argument("--max-warning", type=int, default=15,
                         help="Max allowed WARNING-severity findings (medium). Default: 15")
    args = parser.parse_args()

    try:
        with open(args.report) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"SAST GATE: report file not found at {args.report}")
        sys.exit(2)
    except json.JSONDecodeError:
        print(f"SAST GATE: report file at {args.report} is not valid JSON")
        sys.exit(2)

    results = data.get("results", [])
    counts = {"ERROR": 0, "WARNING": 0, "INFO": 0}
    findings_by_severity = {"ERROR": [], "WARNING": [], "INFO": []}

    for r in results:
        sev = r.get("extra", {}).get("severity", "INFO")
        if sev not in counts:
            sev = "INFO"
        counts[sev] += 1
        findings_by_severity[sev].append({
            "rule": r.get("check_id", "unknown"),
            "path": r.get("path", "unknown"),
            "line": r.get("start", {}).get("line", "?"),
            "message": r.get("extra", {}).get("message", "").strip().split("\n")[0][:120],
        })

    print("=" * 70)
    print("SAST GATE — Semgrep Results Summary")
    print("=" * 70)
    print(f"  ERROR   (critical/high): {counts['ERROR']}  (threshold: {args.max_error})")
    print(f"  WARNING (medium):        {counts['WARNING']}  (threshold: {args.max_warning})")
    print(f"  INFO    (low):           {counts['INFO']}  (informational, no gate)")
    print("=" * 70)

    if counts["ERROR"] > 0:
        print("\nCRITICAL/HIGH findings:")
        for f in findings_by_severity["ERROR"]:
            print(f"  [{f['rule']}] {f['path']}:{f['line']}")
            print(f"      {f['message']}")

    if counts["WARNING"] > 0:
        print("\nMEDIUM findings (first 10 shown):")
        for f in findings_by_severity["WARNING"][:10]:
            print(f"  [{f['rule']}] {f['path']}:{f['line']}")
            print(f"      {f['message']}")

    failed = False
    if counts["ERROR"] > args.max_error:
        print(f"\nFAIL: {counts['ERROR']} critical/high findings exceed threshold of {args.max_error}")
        failed = True
    if counts["WARNING"] > args.max_warning:
        print(f"\nFAIL: {counts['WARNING']} medium findings exceed threshold of {args.max_warning}")
        failed = True

    if failed:
        sys.exit(1)

    print("\nPASS: SAST findings within configured thresholds")
    sys.exit(0)


if __name__ == "__main__":
    main()
