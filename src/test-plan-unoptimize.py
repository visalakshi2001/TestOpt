import json

def test_unoptimize():
    # Load the raw test configurations
    with open("../reports/tests_raw_def.json", "r") as f:
        raw_tests = json.load(f)

    # Track the previous configuration's scenarios
    prev_scenarios = set()

    # Add 'apply' and 'retract' to each configuration
    for cfg in raw_tests:
        current_scenarios = set(cfg["scenarios"])
        cfg["apply"] = sorted(current_scenarios - prev_scenarios)
        cfg["retract"] = sorted(prev_scenarios - current_scenarios)
        prev_scenarios = current_scenarios

    # Wrap in final structure without 'length'
    output_data = {
        "tests": raw_tests
    }

    # Write to new file
    with open("../reports/tests_unoptimized_def.json", "w") as f:
        json.dump(output_data, f, indent=2)
        
    print("Saved to reports/tests_unoptimized_def.json")
