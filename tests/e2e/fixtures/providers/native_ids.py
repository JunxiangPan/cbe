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
            "tool": {"driver": {"name": "fixture-native", "rules": [{"id": "generic-api-key"}]}},
            "results": [
                {
                    "ruleId": "generic-api-key",
                    "ruleIndex": 0,
                    "level": "warning",
                    "message": {"text": "native provider id"},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": "src/b.py"},
                                "region": {"startLine": 2, "startColumn": 1},
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
