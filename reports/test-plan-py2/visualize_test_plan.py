import json
from pathlib import Path
from typing import Dict, List, Tuple

# ------------- Hard-coded inputs/outputs -------------
COST_MAP_FILE = "costs.json"                 # same role as --cost-map in Ruby
OPTIMIZED_PLAN_FILE = "test_order_optimized.json"      # plan with {"tests":[...], reconfiguration_cost, observation_cost}
UNOPTIMIZED_TESTS_FILE = "pruned_tests.json" # raw pruned tests (list of test objects, no wrapper)
OUTPUT_HTML = "visualize_plan.html"          # only write HTML; no console printing
# -----------------------------------------------------

TEN_MARKER = ".........|"

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def parse_prefix_order(label: str) -> Tuple[str, int]:
    parts = label.split(".")
    if len(parts) >= 2:
        prefix = ".".join(parts[:-1])
        try:
            order = int(parts[-1])
        except ValueError:
            order = 0
    else:
        prefix, order = label, 0
    return prefix, order

def sort_categories(categories: List[str], costs: Dict[str, int]) -> List[str]:
    def key_fn(s: str):
        prefix, order = parse_prefix_order(s)
        return (costs.get(s, 0), prefix, order)
    return sorted(categories, key=key_fn)

def plan_like_from_tests_raw(
    tests_raw: List[dict],
    scenarios_cost: Dict[str, int],
    observations_cost: Dict[str, int],
) -> dict:
    """
    Build a plan-like dict from a raw pruned tests list:
      {
        "tests": [...same order...],
        "reconfiguration_cost": <computed>,
        "observation_cost": <computed>
      }
    Reconfiguration cost is computed as a *cycle*:
      empty -> t1 -> t2 -> ... -> tN -> empty
    Observation cost: sum over tests of observation costs present in each test.
    """
    # Observation cost
    obs_cost = 0
    for t in tests_raw:
        qs = t.get("quantities", {}) or {}
        for q in qs.keys():
            obs_cost += observations_cost.get(q, 0)

    # Reconfiguration cost: include closing edge back to empty (cycle)
    reconfig_cost = 0
    prev = set()  # empty configuration
    for t in tests_raw:
        curr = set(t.get("scenarios", []) or [])
        changes = (prev - curr) | (curr - prev)
        reconfig_cost += sum(scenarios_cost.get(str(s), 0) for s in changes)
        prev = curr
    # Add the final hop last -> empty (this was missing before)
    if tests_raw:
        closing_changes = prev  # prev -> empty means turn off all remaining scenarios
        reconfig_cost += sum(scenarios_cost.get(str(s), 0) for s in closing_changes)

    return {
        "tests": tests_raw,
        "reconfiguration_cost": reconfig_cost,
        "observation_cost": obs_cost,
    }

def marker_line(length: int) -> str:
    rem = length % 10
    tens = (length - rem) // 10
    return "      " + (TEN_MARKER * tens) + ("." * rem) + " changes"

def build_rows_for_plan(
    plan: dict,
    costs: Dict[str, int],
    mode: str = "scenarios",
) -> str:
    """
    mode: "scenarios" or "observations"
    Returns a multi-line string of the visualization block (header + rows).
    """
    tests = plan["tests"]
    reconfiguration_cost = plan.get("reconfiguration_cost", 0)
    observation_cost = plan.get("observation_cost", 0)

    categories_set = set()
    for t in tests:
        if mode == "observations":
            categories_set |= set((t.get("quantities", {}) or {}).keys())
        else:
            categories_set |= set(t.get("scenarios", []) or [])

    categories = sort_categories(list(categories_set), costs)

    lines = []
    lines.append(f"reconfiguration cost: {reconfiguration_cost}")
    lines.append(f"observation cost: {observation_cost}")
    lines.append(marker_line(len(tests)))

    for cat in categories:
        label = f"{cat:>5s} "
        last_in = False
        changes = 0
        row_chars = []
        for t in tests:
            if mode == "observations":
                t_cats = set((t.get("quantities", {}) or {}).keys())
            else:
                t_cats = set(t.get("scenarios", []) or [])
            now_in = (cat in t_cats)
            if now_in != last_in:
                last_in = now_in
                changes += 1
            row_chars.append("■" if now_in else " ")
        if last_in:
            changes += 1
        lines.append(f"{label}{''.join(row_chars)}    {changes:4d}")

    return "\n".join(lines)

def html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
    )

def main():
    # Load costs
    costs_root = load_json(COST_MAP_FILE)
    scenarios_cost = costs_root.get("scenarios", {})
    observations_cost = costs_root.get("observations", {})

    # Load optimized plan (expects {"tests": [...]})
    plan_opt_raw = load_json(OPTIMIZED_PLAN_FILE)
    if isinstance(plan_opt_raw, dict) and "tests" in plan_opt_raw:
        plan_opt = plan_opt_raw
    else:
        plan_opt = plan_like_from_tests_raw(plan_opt_raw, scenarios_cost, observations_cost)

    # Load unoptimized plan from raw pruned tests list
    tests_unopt_raw = load_json(UNOPTIMIZED_TESTS_FILE)
    if isinstance(tests_unopt_raw, dict) and "tests" in tests_unopt_raw:
        plan_unopt = tests_unopt_raw
    else:
        if not isinstance(tests_unopt_raw, list):
            raise ValueError(f"{UNOPTIMIZED_TESTS_FILE} must be a list of tests or a plan object.")
        plan_unopt = plan_like_from_tests_raw(tests_unopt_raw, scenarios_cost, observations_cost)

    # Build scenario visualizations (unoptimized first, as requested)
    unopt_rows = build_rows_for_plan(plan_unopt, scenarios_cost, mode="scenarios")
    opt_rows = build_rows_for_plan(plan_opt, scenarios_cost, mode="scenarios")

    # Compose HTML
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Test Plan Visualization</title>
<style>
  body {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; padding: 24px; }}
  h1, h2 {{ margin: 0 0 12px 0; }}
  .section {{ margin-bottom: 40px; }}
  .box {{ white-space: pre; font-size: 13px; line-height: 1.2; background: #0b1020; color: #e6edf3; padding: 16px; border-radius: 8px; overflow-x: auto; }}
  .subtle {{ color: #9fb0c3; font-size: 12px; margin-top: 6px; }}
</style>
</head>
<body>
  <h1>Test Plan Visualization (Scenarios)</h1>

  <div class="section">
    <h2>Unoptimized Plan (from raw pruned tests)</h2>
    <div class="box">{html_escape(unopt_rows)}</div>
    <div class="subtle">Source: {html_escape(UNOPTIMIZED_TESTS_FILE)} &nbsp;&nbsp; Costs: {html_escape(COST_MAP_FILE)}</div>
  </div>

  <div class="section">
    <h2>Optimized Plan</h2>
    <div class="box">{html_escape(opt_rows)}</div>
    <div class="subtle">Source: {html_escape(OPTIMIZED_PLAN_FILE)} &nbsp;&nbsp; Costs: {html_escape(COST_MAP_FILE)}</div>
  </div>
</body>
</html>
"""
    Path(OUTPUT_HTML).write_text(html, encoding="utf-8")
    # No console output

if __name__ == "__main__":
    main()
