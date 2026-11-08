import sys
from pathlib import Path

out = Path(sys.argv[1])
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("{not-json", encoding="utf-8")
raise SystemExit(0)
