import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import streamlit as st


def build_scenario_df(tests):
    rows = []
    for idx, test in enumerate(tests, start=1):
        for scenario in test["scenarios"]:
            rows.append({
                "test_index": idx,
                "test_id": test["id"],
                "scenario": scenario
            })
    return pd.DataFrame(rows)

def plot_scenario_heatmaps():
    with open('reports/tests_optimized_def.json') as f:
        opt_data = json.load(f)['tests']
    with open('reports/tests_unoptimized_def.json') as f:
        unopt_data = json.load(f)['tests']

    df_opt = build_scenario_df(opt_data)
    df_unopt = build_scenario_df(unopt_data)

    z_opt = df_opt.pivot_table(index='scenario', columns='test_index', aggfunc='size', fill_value=0)
    z_unopt = df_unopt.pivot_table(index='scenario', columns='test_index', aggfunc='size', fill_value=0)
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Optimized Scenario Schedule', 'Unoptimized Scenario Schedule'),
        shared_yaxes=True
    )
    fig1 = go.Figure(data=go.Heatmap(z=z_opt.values, x=z_opt.columns, y=z_opt.index, colorscale='Viridis'))
    fig2 = go.Figure(data=go.Heatmap(z=z_unopt.values, x=z_unopt.columns, y=z_unopt.index, colorscale='Viridis'))

    # fig.update_layout(
    #     height=600, width=1000,
    #     title_text="Heatmap of Scenarios per Test Index",
    #     xaxis_title="Test Step",
    #     yaxis_title="Scenario ID"
    # )

    return fig1, fig2

def plot_sequence_dots(tests, title):
    
    # Extract ordered test IDs and their scenarios from tests
    # test: [{id: "1", scenarios: ["3", "19"]}, {id: "2", scenarios: ["3", "19", "5"]}, ...]
    # extract test id and the consequent scenario in separate lists
    seq_ids = []
    test_ids = []
    for test in tests:
        test_ids.extend([test['id']] * len(test['scenarios']))
        seq_ids.extend(test['scenarios'])

    fig = go.Figure(go.Scatter(
        x=test_ids,
        y=seq_ids,
        mode='markers',
        marker=dict(size=10),
        line=dict(shape='hv')
    ))
    fig.update_layout(
        title=title,
        xaxis_title='Test ID (in original order)',
        yaxis_title='Scenarios',
        xaxis=dict(type='category', categoryorder='array', categoryarray=test_ids),
        yaxis=dict(type='category', categoryorder='array', categoryarray=sorted(seq_ids), autorange='reversed'),
        showlegend=False,
        height=600
    )

    return fig

def build_scenario_timeline(tests, title="Scenario Timeline"):
    """
    Build a Plotly timeline (Gantt) figure that shows how long each scenario
    remains active across a test sequence.

    Parameters
    ----------
    tests : list[dict]
        The list of test dictionaries loaded from the JSON file:
        [
          {
            "id": "1",
            "scenarios": ["3", "19"],
            "apply":   ["3", "19"],
            "retract": []
          },
          ...
        ]
    title : str
        Figure title.

    Returns
    -------
    plotly.graph_objects.Figure
    """

    ordered_test_ids = [str(t["id"]) for t in tests]        # X‑axis order
    scenario_ids = sorted({s for t in tests for s in t["scenarios"]})
    ordered_scenario_ids = list(map(str, scenario_ids))     # Y‑axis order

    # ------------------------------------------------------------------
    # 2. Flatten (test ID, scenario ID) pairs for scatter plotting  -----
    # ------------------------------------------------------------------
    xs, ys = [], []
    for t in tests:
        x = str(t["id"])
        for s in t["scenarios"]:
            xs.append(x)
            ys.append(str(s))

    # ------------------------------------------------------------------
    # 3. Build the figure  ---------------------------------------------
    # ------------------------------------------------------------------
    fig = go.Figure(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers",
            marker=dict(size=14, symbol="square"),   # “small bar” feel
            hovertemplate="Test ID: %{x}<br>Scenario ID: %{y}<extra></extra>",
        )
    )

    # 4. Cosmetics: preserve categorical order exactly as requested
    fig.update_layout(
        title=title,
        xaxis=dict(
            title="Test ID (execution order)",
            type="category",
            categoryorder="array",
            categoryarray=ordered_test_ids,
            tickangle=45
        ),
        yaxis=dict(
            title="Scenario ID",
            type="category",
            categoryorder="array",
            # reverse so the numerically first scenario appears at the top
            categoryarray=ordered_scenario_ids[::-1]
        ),
        height=650,
        margin=dict(l=80, r=40, t=80, b=120)
    )
    return fig


# ----------------------------------------------------------------------
# 1. Build Scenario × Test matrix with status codes
# ----------------------------------------------------------------------
def make_presence_df(tests, flipped=False) -> pd.DataFrame:
    """
    Return a DataFrame whose values are:
        2 → newly applied
        1 → active (carried over)
       -1 → retracted
        0 → inactive
    """

    test_ids      = [str(t["id"]) for t in tests]           # column order
    scenario_all  = sorted({s for t in tests for s in t["scenarios"]}
                           | {s for t in tests for s in t["apply"]}
                           | {s for t in tests for s in t["retract"]})
    df = pd.DataFrame(0, index=scenario_all, columns=test_ids, dtype=int)

    for t in tests:
        tid = str(t["id"])

        # 2 → newly applied
        for sc in t["apply"]:
            df.at[sc, tid] = 2

        # 1 → active but not newly applied
        for sc in t["scenarios"]:
            if df.at[sc, tid] == 0:               # skip if already marked 2
                df.at[sc, tid] = 1

        # -1 → retracted
        for sc in t["retract"]:
            df.at[sc, tid] = -1                  # overwrite any 0

    df.index.name   = "Scenario ID"
    df.columns.name = "Test ID"

    if flipped:
        # Transpose the DataFrame to have tests as rows and scenarios as columns
        df = df.T
    

    # ------------------------------------------------------------------
    # 3.  Load Scenario‑to‑Requirement map (from scenarios.csv)
    #     -------------------------------------------------------------
    # The file is assumed to have *at least* two columns:
    #     scenario_id , requirement_id
    # (If it also contains quantity_id or other fields that is fine;
    #  we only use the two shown.)
    # ------------------------------------------------------------------
    sc_map = (
        pd.read_csv("reports/scenarios.csv")          # ← path to the file the user supplied
        .groupby("scenarioID")["requirementIDs"]
        .agg(list)                         # scenario_id → [req1, req2, …]
        .to_dict()
    )

    # ------------------------------------------------------------------
    # 4.  Pre‑compute, for every Test, which requirements are present
    #     -----------------------------------------------------------
    #  – Because the JSON already tells us, per test, which quantity
    #    objects are loaded and which requirements each quantity
    #    fulfils, we can build a quick helper dictionary.  This way
    #    we do not need scenarios.csv again later on.
    # ------------------------------------------------------------------
    test_req_map = {}     # a dictionary mapping test_id → set of requirement_ids
    for t in tests:                                  # ← the same `tests` list you already parsed
        tid = str(t["id"])
        reqs = []
        for q in t["quantities"].values():
            reqs.extend(q["requirements"])
        test_req_map[tid] = set(reqs)                # faster look‑ups later
    
    # ------------------------------------------------------------------
    # 5.  Build a *text* matrix with the requirement lists
    #     -----------------------------------------------
    #     – Wherever the scenario is *inactive* we keep an empty string.
    #     – Wherever the scenario is active / applied / retracted we
    #       insert a comma‑separated list *filtered* to requirements
    #       that are actually in the current test.
    # ------------------------------------------------------------------
    disp = pd.DataFrame(
            "", index=df.index, columns=df.columns   # `df` is the presence‑matrix from step 1
    )

    for sc in disp.index:
        sc_reqs = set(sc_map.get(sc, []))            # all reqs this scenario can satisfy
        for tid in disp.columns:
            if df.at[sc, tid] != 0:                  # only non‑white cells
                disp.at[sc, tid] = ", ".join(
                    str(r) for r in sorted(sc_reqs & test_req_map[tid])
                )

    return df, disp


# ----------------------------------------------------------------------
# 2. Style function with custom colours
# ----------------------------------------------------------------------
def style_presence(df: pd.DataFrame, show_additional: bool = False):
    colours = {2: "#4f8aff",     # light blue  – newly applied
               1: "#2a4b8d",     # dark  blue  – active / carried‑over
              -1: "#ffafaf",     # light red   – retracted
               0: "#ffffff"}     # white       – inactive

    if not show_additional:
        colours.update({
            0: "#ffffff", 
            1: "#2a4b8d",
            -1: '#2a4b8d',
            2: '#2a4b8d'
        })

    

    # formatting hides the numeric values
    return df.style.applymap(lambda v: f"background-color: {colours[v]}")\
                    .format("") \
                    .set_table_styles([
                        {"selector": "tr", "props": "line-height: 1px;"},
                        {"selector": "td,th", "props": "line-height: inherit; padding: 0;"}
                    ])
