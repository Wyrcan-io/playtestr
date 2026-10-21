"""Controlled child helper for immutable evidence-phase propagation regression."""
import json
from pathlib import Path
import sys

from readiness_evidence import Campaign, RAW

root=Path(sys.argv[1]).resolve()
root.relative_to(RAW.resolve())
campaign=Campaign(root)
print(json.dumps(dict(phase=campaign.phase,catalog_project=campaign.catalog_project)))
