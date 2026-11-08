import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
out.parent.mkdir(parents=True, exist_ok=True)
log = {
    "$schema": "https://docs.oasis-open.org/sarif/sarif/v2.1.0/cos02/schemas/sarif-schema-2.1.0.json",
    "version": "2.1.0",
    "runs": [
        {
            "tool": {
                "driver": {
                    "name": "fixture-findings",
                    "rules": [{"id": "CBE-SECRET-001", "name": "NoHardcodedSecrets"}],
                }
            },
            "results": [
                {
                    "ruleId": "CBE-SECRET-001",
                    "ruleIndex": 0,
                    "level": "error",
                    "message": {"text": "fixture secret finding"},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": "src/a.py"},
                                "region": {"startLine": 1, "startColumn": 1},
                            }
                        }
                    ],
                }
            ],
        }
    ],
}
out.write_text(json.dumps(log), encoding="utf-8")
raise SystemExit(1)
