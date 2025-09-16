import json

def test_optimize():
    """
    Optimize the test configurations by reordering them based on scenario transition costs.
    This function reads the unoptimized test configurations and scenario costs,
    applies a greedy algorithm to minimize transition costs, and saves the optimized output.
    """
    # Load test configurations
    with open("../reports/tests_unoptimized_def.json", "r") as f:
        unoptimized_data = json.load(f)
        tests = unoptimized_data["tests"]

    # Load scenario costs
    with open("../reports/costs.json", "r") as f:
        costs_data = json.load(f)

    scenario_costs = {
        int(binding["scenarioID"]["value"]): int(binding["cost"]["value"])
        for binding in costs_data["results"]["bindings"]
    }

    # Greedy reordering based on scenario transition cost
    remaining = tests[:]
    ordered = []
    current_scenarios = set()

    while remaining:
        best_test = None
        best_cost = float('inf')

        for test in remaining:
            test_scenarios = set(test["scenarios"])
            apply_cost = sum(scenario_costs.get(s, 0) for s in test_scenarios - current_scenarios)
            retract_cost = sum(scenario_costs.get(s, 0) for s in current_scenarios - test_scenarios)
            cost = apply_cost + retract_cost

            if cost < best_cost:
                best_cost = cost
                best_test = test

        ordered.append(best_test)
        current_scenarios = set(best_test["scenarios"])
        remaining.remove(best_test)

    # Recalculate 'apply' and 'retract' for new order
    final_tests = []
    prev_scenarios = set()
    for test in ordered:
        current_scenarios = set(test["scenarios"])
        test["apply"] = sorted(current_scenarios - prev_scenarios)
        test["retract"] = sorted(prev_scenarios - current_scenarios)
        final_tests.append(test)
        prev_scenarios = current_scenarios

    # Final retraction at the end
    final_retract = sorted(prev_scenarios)

    # Save optimized output
    with open("../reports/tests_optimized_def.json", "w") as f:
        json.dump({"tests": final_tests}, f, indent=2)

    print("Final retract cost (at end):", sum(scenario_costs.get(s, 0) for s in final_retract))
    print("Saved to reports/tests_optimized_def.json")
