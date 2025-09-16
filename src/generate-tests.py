import json
from collections import defaultdict


def generate_tests():
    """
    Generate tests from SPARQL-style requirements file.
    This function reads the requirements, builds a mapping of scenario sets to quantities,
    propagates requirements from subsets to supersets, and saves the result in JSON format.
    """
    
    # Load the SPARQL-style requirements file
    with open("reports/reqs.json") as f:
        data = json.load(f)

    # Convert SPARQL-style bindings to list of dicts with 'id', 'scenarios', and 'quantity'
    requirements = []
    for binding in data["results"]["bindings"]:
        req_id = int(binding["id"]["value"])
        scenarios = list(map(int, binding["scenarios"]["value"].split(",")))
        quantity = int(binding["quantity"]["value"])
        requirements.append({
            "id": req_id,
            "scenarios": scenarios,
            "quantity": quantity
        })

    # Step 1: Build base structure: map (scenario_set) → {quantity_id → [requirement_ids]}
    config_to_quantities = defaultdict(lambda: defaultdict(set))

    for req in requirements:
        scenarios = frozenset(req['scenarios'])
        quantity_id = str(req['quantity'])  # keep as string to match JSON format
        req_id = req['id']
        config_to_quantities[scenarios][quantity_id].add(req_id)

    # Step 2: Transitive closure: propagate requirements from subsets to supersets
    all_configs = list(config_to_quantities.keys())
    inherited_config_to_quantities = defaultdict(lambda: defaultdict(set))

    for c1 in all_configs:
        for c2 in all_configs:
            if c1.issubset(c2):
                for q, reqs in config_to_quantities[c1].items():
                    inherited_config_to_quantities[c2][q].update(reqs)

    # Step 3: Format output
    output = []
    for idx, (config, quantities) in enumerate(inherited_config_to_quantities.items(), start=1):
        entry = {
            "id": idx,
            "scenarios": sorted(list(config)),
            "quantities": {
                qid: {"requirements": sorted(list(req_ids))}
                for qid, req_ids in quantities.items()
            }
        }
        output.append(entry)

    # Step 4: Save to JSON
    with open("reports/tests_raw_def.json", "w") as f:
        json.dump(output, f, indent=2)

    print("Saved to reports/tests_raw_def.json")