"""Reject new Ruff findings and require removal of resolved legacy baseline entries."""

import json
from collections import Counter
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    baseline = json.loads((root / ".github/ruff-baseline.json").read_text())
    expected = Counter({
        (entry["path"], entry["code"], entry["message"]): entry["count"]
        for entry in baseline
    })
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--output-format", "json",
         "tools", "tests", "scripts"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    if result.returncode not in (0, 1):
        sys.stderr.write(result.stderr)
        return result.returncode

    findings = json.loads(result.stdout)
    actual = Counter()
    for finding in findings:
        path = Path(finding["filename"]).relative_to(root).as_posix()
        key = (path, finding["code"], finding["message"])
        actual[key] += 1
        status = "KNOWN" if actual[key] <= expected[key] else "NEW"
        print(f'{status} {path}:{finding["location"]["row"]}: '
              f'{finding["code"]} {finding["message"]}')

    new = actual - expected
    resolved = expected - actual
    if resolved:
        print("Remove resolved findings from .github/ruff-baseline.json:")
        for key, count in sorted(resolved.items()):
            print(f"  {key}: {count}")
    print(f"{sum(actual.values())} existing/current findings; "
          f"{sum(new.values())} new; {sum(resolved.values())} resolved.")
    return int(bool(new or resolved))


if __name__ == "__main__":
    sys.exit(main())
