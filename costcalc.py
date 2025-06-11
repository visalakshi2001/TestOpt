import json


def calculate_costs(tests):
    """
    Calculate the total apply and retract costs from the test data.
    Costs are loaded from a JSON file and summed based on scenario IDs.
    """
    # Load costs from costs.json and build a cost lookup dictionary
    with open('reports/costs.json', 'r') as cost_file:
        cost_data = json.load(cost_file)
        cost_lookup = {
            int(binding['scenarioID']['value']): int(binding['cost']['value'])
            for binding in cost_data['results']['bindings']
        }

    # # Load the test data
    # file_path = 'reports/tests_unoptimized_def.json'
    # with open(file_path, 'r') as file:
    #     data = json.load(file)

    total_apply_cost = 0
    total_retract_cost = 0
    # tests = data.get('tests', [])

    # Helper function to get cost of a list of scenario IDs
    def compute_cost(scenario_ids):
        return sum(cost_lookup.get(scenario_id, 0) for scenario_id in scenario_ids)

    for i, test in enumerate(tests, start=1):
        apply_ids = test.get('apply', [])
        retract_ids = test.get('retract', [])

        apply_sum = compute_cost(apply_ids)
        retract_sum = compute_cost(retract_ids)

        total_apply_cost += apply_sum
        total_retract_cost += retract_sum

        # print(f"Test {i}: apply = {apply_sum}, retract = {retract_sum}")

    # Add the final configuration (last test's apply list) to retract cost
    final_scenarios = tests[-1].get('scenarios', [])
    final_retract_sum = compute_cost(final_scenarios)
    total_retract_cost += final_retract_sum

    total_combined = total_apply_cost + total_retract_cost
    # declared_length = data.get("length", "Not specified")

    print("\n--- Totals ---")
    print(f"Total Apply Cost: {total_apply_cost}")
    print(f"Total Retract Cost: {total_retract_cost}")
    print(f"Total Combined Cost: {total_combined}")

    return {
        "total_apply_cost": total_apply_cost,
        "total_retract_cost": total_retract_cost,
        "total_combined_cost": total_combined
    }