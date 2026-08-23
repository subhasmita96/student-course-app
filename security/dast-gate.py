#!/usr/bin/env python3
"""
Evaluates an OWASP ZAP traditional-json report against a severity
threshold and exits non-zero if High-risk alerts exceed the allowed
maximum. Prints a human-readable summary for the Jenkins console log.

ZAP risk levels (as reported in the JSON): 0=Informational, 1=Low,
2=Medium, 3=High.

Usage:
    python3 dast-gate.py zap-dast-report.json --max-high 0 --max-medium 5
"""
import json
import sys
import argparse

RISK_NAMES = {"0": "Informational", "1": "Low", "2": "Medium", "3": "High"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report", help="Path to ZAP traditional-json report")
    parser.add_argument("--max-high", type=int, default=0,
                         help="Max allowed High-risk alerts. Default: 0")
    parser.add_argument("--max-medium", type=int, default=5,
                         help="Max allowed Medium-risk alerts. Default: 5")
    args = parser.parse_args()

    try:
        with open(args.report) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"DAST GATE: report file not found at {args.report}")
        sys.exit(2)
    except json.JSONDecodeError:
        print(f"DAST GATE: report file at {args.report} is not valid JSON")
        sys.exit(2)

    counts = {"High": 0, "Medium": 0, "Low": 0, "Informational": 0}
    alerts_by_risk = {"High": [], "Medium": [], "Low": [], "Informational": []}

    sites = data.get("site", [])
    for site in sites:
        for alert in site.get("alerts", []):
            risk_code = alert.get("riskcode", "0")
            risk_name = RISK_NAMES.get(str(risk_code), "Informational")
            counts[risk_name] += 1
            alerts_by_risk[risk_name].append({
                "name": alert.get("name", "unknown"),
                "count": alert.get("count", len(alert.get("instances", []))),
                "cweid": alert.get("cweid", "N/A"),
                "desc": alert.get("desc", "").strip().split("\n")[0][:140],
            })

    print("=" * 70)
    print("DAST GATE — OWASP ZAP Results Summary")
    print("=" * 70)
    print(f"  High:          {counts['High']}  (threshold: {args.max_high})")
    print(f"  Medium:        {counts['Medium']}  (threshold: {args.max_medium})")
    print(f"  Low:           {counts['Low']}  (informational, no gate)")
    print(f"  Informational: {counts['Informational']}  (informational, no gate)")
    print("=" * 70)

    if counts["High"] > 0:
        print("\nHIGH risk alerts:")
        for a in alerts_by_risk["High"]:
            print(f"  [CWE-{a['cweid']}] {a['name']}  ({a['count']} instance(s))")
            print(f"      {a['desc']}")

    if counts["Medium"] > 0:
        print("\nMEDIUM risk alerts:")
        for a in alerts_by_risk["Medium"]:
            print(f"  [CWE-{a['cweid']}] {a['name']}  ({a['count']} instance(s))")
            print(f"      {a['desc']}")

    failed = False
    if counts["High"] > args.max_high:
        print(f"\nFAIL: {counts['High']} High-risk findings exceed threshold of {args.max_high}")
        failed = True
    if counts["Medium"] > args.max_medium:
        print(f"\nFAIL: {counts['Medium']} Medium-risk findings exceed threshold of {args.max_medium}")
        failed = True

    if failed:
        sys.exit(1)

    print("\nPASS: DAST findings within configured thresholds")
    sys.exit(0)


if __name__ == "__main__":
    main()
