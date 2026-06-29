from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pandas as pd


def save_industrial_bundle(bundle: Dict[str, Any], output_dir: str | Path, name_prefix: str = "industrial_analysis") -> Dict[str, str]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = out_dir / f"{name_prefix}_{ts}.json"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)

    exports: Dict[str, str] = {"analysis_json": str(json_path)}

    sensitivity = bundle.get("sensitivity")
    if isinstance(sensitivity, list) and sensitivity:
        sensitivity_path = out_dir / f"{name_prefix}_sensitivity_{ts}.csv"
        pd.DataFrame(sensitivity).to_csv(sensitivity_path, index=False)
        exports["sensitivity_csv"] = str(sensitivity_path)

    monte_carlo = bundle.get("monte_carlo", {})
    records = monte_carlo.get("records") if isinstance(monte_carlo, dict) else None
    if isinstance(records, list) and records:
        mc_path = out_dir / f"{name_prefix}_monte_carlo_{ts}.csv"
        pd.DataFrame(records).to_csv(mc_path, index=False)
        exports["monte_carlo_csv"] = str(mc_path)

    return exports
