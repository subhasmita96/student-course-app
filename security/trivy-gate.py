#!/usr/bin/env python3
"""
Evaluates a Trivy JSON image scan report against a severity threshold and
exits non-zero if the count of CRITICAL/HIGH findings exceeds the allowed
maximum. Prints a human-readable summary for the Jenkins console log.

Deliberately plain Python + stdlib json (no Jenkins plugin dependency,
unlike the built-in readJSON pipeline step which requires the Pipeline
Utility Steps plugin to be installed).

Usage:
    python3 trivy-gate.py trivy-report.json --max-critical 0 --max-high 5
"""
import json
import sys
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report", help="Path to trivy JSON report")
    parser.add_argument("--max-critical", type=int, default=0,
                         help="Max allowed CRITICAL findings. Default: 0")
    parser.add_argument("--max-high", type=int, default=5,
                         help="Max allowed HIGH findings. Default: 5")
    args = parser.parse_args()

    try:
        with open(args.report) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"IMAGE SCAN GATE: report file not found at {args.report}")
        sys.exit(2)
    except json.JSONDecodeError:
        print(f"IMAGE SCAN GATE: report file at {args.report} is not valid JSON")
        sys.exit(2)

    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    findings_by_sev = {"CRITICAL": [], "HIGH": []}

    for result in data.get("Results", []) or []:
        target = result.get("Target", "unknown")
        for vuln in result.get("Vulnerabilities", []) or []:
            sev = vuln.get("Severity", "UNKNOWN")
            if sev not in counts:
                sev = "UNKNOWN"
            counts[sev] += 1
            if sev in ("CRITICAL", "HIGH"):
                findings_by_sev[sev].append({
                    "id": vuln.get("VulnerabilityID", "unknown"),
                    "pkg": vuln.get("PkgName", "unknown"),
                    "installed": vuln.get("InstalledVersion", "?"),
                    "fixed": vuln.get("FixedVersion", "none"),
                    "target": target,
                })

    print("=" * 70)
    print("IMAGE SECURITY GATE — Trivy Results Summary")
    print("=" * 70)
    print(f"  CRITICAL: {counts['CRITICAL']}  (threshold: {args.max_critical})")
    print(f"  HIGH:     {counts['HIGH']}  (threshold: {args.max_high})")
    print(f"  MEDIUM:   {counts['MEDIUM']}  (informational, no gate)")
    print(f"  LOW:      {counts['LOW']}  (informational, no gate)")
    print("=" * 70)

    if findings_by_sev["CRITICAL"]:
        print("\nCRITICAL vulnerabilities:")
        for f in findings_by_sev["CRITICAL"]:
            fix = f["fixed"] if f["fixed"] != "none" else "no fix available yet"
            print(f"  [{f['id']}] {f['pkg']} {f['installed']} (fix: {fix}) — {f['target']}")

    if findings_by_sev["HIGH"]:
        print("\nHIGH vulnerabilities (first 15 shown):")
        for f in findings_by_sev["HIGH"][:15]:
            fix = f["fixed"] if f["fixed"] != "none" else "no fix available yet"
            print(f"  [{f['id']}] {f['pkg']} {f['installed']} (fix: {fix}) — {f['target']}")

    failed = False
    if counts["CRITICAL"] > args.max_critical:
        print(f"\nFAIL: {counts['CRITICAL']} CRITICAL findings exceed threshold of {args.max_critical}")
        failed = True
    if counts["HIGH"] > args.max_high:
        print(f"\nFAIL: {counts['HIGH']} HIGH findings exceed threshold of {args.max_high}")
        failed = True

    if failed:
        sys.exit(1)

    print("\nPASS: image scan findings within configured thresholds")
    sys.exit(0)


if __name__ == "__main__":
    main()
