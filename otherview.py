import streamlit as st
import os
import json
import plotly.graph_objects as go
import pandas as pd

from makeplots import make_presence_df, style_presence

def render(project: dict) -> None:
    folder   = project["folder"]
    csv_path = os.path.join(folder, "reqs.csv")
    json_path = os.path.join(folder, "reqs.json")

    if not os.path.exists(json_path):
        st.info("reqs.json data is not available – upload it via **🪄 Edit Data**")
        return
    
    unopt_tests = json.load(open(os.path.join("reports/tests_unoptimized_def.json")))
    # opt_tests = json.load(open(os.path.join("reports/tests_optimized_def.json")))
    df1, _ = make_presence_df(unopt_tests["tests"])
    df1 = style_presence(df1)

    df_info = st.dataframe(df1, use_container_width=True, on_select="rerun", selection_mode=["multi-row", "multi-column"])

    st.write(df_info)

    # ──────────────────────────── 2.  Load data once ────────────────────────────
    SCENARIOS_DF = load_csv("reports/scenarios.csv")  # columns: scenario_id, requirement_id
    REQS_DF      = load_csv("reports/test_optimization_dashboard/reqs.csv")       # columns: requirement_id, quantity_id
    TESTS        = load_tests()
    COSTS_LU     = load_cost_lookup()


    st.subheader("Select scenario(s) to inspect")
    cho_scenarios = st.multiselect(
        "Scenario ID", sorted(SCENARIOS_DF["scenarioID"].unique()), max_selections=10
    )
    if cho_scenarios:
        fig = build_sankey(SCENARIOS_DF, REQS_DF, cho_scenarios)
        # st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("⬆️ Pick one or more scenario IDs to show the Sankey.")
        
    st.subheader("Running cost incurred by each test configuration")
    df_cost = calc_costs_per_test(TESTS, COSTS_LU)
    bar = go.Bar(x=df_cost["test_id"], y=df_cost["cost"])
    st.plotly_chart(
        go.Figure(bar).update_layout(xaxis_title="Test ID", yaxis_title="Cost",
                                     xaxis=dict(
                                         type="category", categoryorder="array",
                                         categoryarray=sorted(list(df_cost["test_id"])),
                                     )
        ),
        use_container_width=True,
    )
    st.dataframe(df_cost.sort_values("test_id"), use_container_width=True)

    st.subheader("Which quantities satisfy a requirement?")
    req_id = st.multiselect(
        "Requirement ID", sorted(REQS_DF["id"].unique())
    )

    if req_id != []:
        # st.success(f"Requirement **{req_id}** is covered by quantity ID(s):"
        #            f" {', '.join(map(str, q_list))}")
        st.write(REQS_DF.query("id in @req_id")[["id", "quantity"]])
    else:
        st.info("⬆️ Pick one or more requirement IDs to show the quantities that satisfy them.")




@st.cache_data
def load_csv(name: str) -> pd.DataFrame:
    """Load a CSV once and cache the result."""
    return pd.read_csv(name)

@st.cache_data
def load_tests(path: str = "reports/tests_optimized_def.json") -> list[dict]:
    """Return the list of tests from the JSON definition."""
    with open(path, "r") as f:
        return json.load(f)["tests"]

@st.cache_data
def load_cost_lookup(path: str = "reports/costs.json") -> dict[int, int]:
    """scenario‑id → monetary cost lookup table (int)."""
    with open(path, "r") as f:
        raw = json.load(f)
    return {
        int(b["scenarioID"]["value"]): int(b["cost"]["value"])
        for b in raw["results"]["bindings"]
    }



def build_sankey(
    scenarios_df: pd.DataFrame,
    reqs_df: pd.DataFrame,
    selected_scenarios: list[int],
) -> go.Figure:
    """
    Build a Scenario → Requirement → Quantity Sankey focused on the user
    selection.
    """
    # ------------------------------------------------------------------ nodes
    #   1. keep only rows for the chosen scenario(s)
    s_df = scenarios_df.query("scenarioID in @selected_scenarios")

    #   2. join to find requirements and quantities
    sr_df = (
        pd.concat([s_df, reqs_df], join='inner', axis=1)
        .dropna(subset=["quantity"])
        # .astype(int)
    )

    st.write(s_df)
    list_of_requirements = [int(i) for i in sr_df["requirementIDs"].iloc[0].split(",")]
    # st.write(list_of_requirements)
    r_df = reqs_df.query("id in @list_of_requirements")
    st.write(r_df)

    # build sr_df with scenrioID, requirementIDs, quantity  
    # s_df -> dataframe with scenarioID, requirementIDs (comma separated)
    # r_df -> dataframe with requirementID, quantity

    
    # #   3. build unique label set
    # labels_s      = [f"S{sid}" for sid in sr_df["scenarioID"].unique()]
    # labels_r      = [f"R{rid}" for rid in sr_df["requirementIDs"].unique()]
    # labels_q      = [f"Q{qid}" for qid in sr_df["quantity"].unique()]
    # labels        = labels_s + labels_r + labels_q
    # index         = {lab: i for i, lab in enumerate(labels)}

    # # ------------------------------------------------------------------ links
    # # Scenario ▶ Requirement
    # l1 = (
    #     sr_df[["scenario_id", "requirement_id"]]
    #     .drop_duplicates()
    #     .assign(
    #         source=lambda d: d["scenario_id"].map(lambda x: index[f"S{x}"]),
    #         target=lambda d: d["requirement_id"].map(lambda x: index[f"R{x}"]),
    #         value=1,
    #     )
    # )
    # # Requirement ▶ Quantity
    # l2 = (
    #     sr_df[["requirement_id", "quantity_id"]]
    #     .drop_duplicates()
    #     .assign(
    #         source=lambda d: d["requirement_id"].map(lambda x: index[f"R{x}"]),
    #         target=lambda d: d["quantity_id"].map(lambda x: index[f"Q{x}"]),
    #         value=1,
    #     )
    # )
    # links = pd.concat([l1, l2], ignore_index=True)

    # # ------------------------------------------------------------------ plotly
    # sankey = go.Sankey(
    #     arrangement="snap",
    #     node=dict(label=labels, pad=10, thickness=14),
    #     link=dict(
    #         source=links["source"],
    #         target=links["target"],
    #         value=links["value"],
    #     ),
    # )
    # return go.Figure(data=[sankey]).update_layout(
    #     title="Scenario → Requirement → Quantity flow"
    # )

def calc_costs_per_test(tests: list[dict], cost_lu: dict[int, int]) -> pd.DataFrame:
    """Return DataFrame with per‑test running cost (apply + retract)."""
    rows = []
    for t in tests:
        tid = t["id"]
        apply_ids   = t.get("apply",   [])
        retract_ids = t.get("retract", [])
        cost = sum(cost_lu.get(s, 0) for s in apply_ids + retract_ids)
        rows.append({"test_id": tid, "cost": cost})
    return pd.DataFrame(rows)
