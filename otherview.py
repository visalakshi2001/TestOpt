import streamlit as st
import os
import json
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from makeplots import build_sankey, make_presence_df, style_presence, make_cost_plots
from costcalc import calculate_costs

from streamlit_echarts import st_echarts

def render(project: dict) -> None:
    folder   = project["folder"]
    csv_path = os.path.join(folder, "reqs.csv")
    json_path = os.path.join(folder, "reqs.json")

    if not os.path.exists(json_path):
        st.info("reqs.json data is not available – upload it via **🪄 Edit Data**")
        return
    
    unopt_tests = json.load(open(os.path.join("reports/tests_unoptimized_def.json")))
    opt_tests = json.load(open(os.path.join("reports/tests_optimized_def.json")))

    # ──────────────────────────── 2.  Load data once ────────────────────────────
    SCENARIOS_DF = load_csv("reports/scenarios.csv")  # columns: scenario_id, requirement_id
    REQS_DF      = load_csv("reports/test_optimization_dashboard/reqs.csv")       # columns: requirement_id, quantity_id


    # ──────────────────────────── 3.   Sankey  ────────────────────────────

    st.subheader("Select scenario(s) to inspect")
    cho_scenarios = st.multiselect(
        "Scenario ID", sorted(SCENARIOS_DF["scenarioID"].unique()), max_selections=10
    )
    if cho_scenarios:
        with st.expander("Show plot settings", expanded=False):
            plot_height = st.slider(
                "Set plot size",
                min_value=450, max_value=900, value=600, step=30,)
        fig = build_sankey(SCENARIOS_DF, REQS_DF, cho_scenarios, plot_height=plot_height)
        st.plotly_chart(fig)
    else:
        st.info("⬆️ Pick one or more scenario IDs to show the Sankey.")
    


    # ──────────────────────────── 3.  Requirement table ────────────────────────────
    st.subheader("Which quantities satisfy a requirement?")
    req_id = st.multiselect(
        "Requirement ID", sorted(REQS_DF["id"].unique())
    )
    if req_id != []:
        st.write(REQS_DF.query("id in @req_id")[["id", "quantity"]])
    else:
        st.info("⬆️ Pick one or more requirement IDs to show the quantities that satisfy them.")


    # ──────────────────────────── 4.  Cost charts ────────────────────────────
    st.subheader("Cost Calculation")
    # Display a grid of metrics with total costs
    costs = calculate_costs(unopt_tests["tests"])
    cols = st.columns(2)
    st.markdown("##### Test Configuration Metrics")
    show_optimized = st.checkbox("Show Optimized Values", value=True, key="cost_opt_plot")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Unoptimized Apply Cost", f"{costs['total_apply_cost']:,} $")
    col2.metric("Unoptimized Retract Cost", f"{costs['total_retract_cost']:,} $")
    col3.metric("Unoptimized Combined Cost", f"{costs['total_combined_cost']:,} $")
    # st.markdown("---")
    if show_optimized:
        # show optimized costs
        opt_costs = calculate_costs(opt_tests["tests"])
        col1, col2, col3 = st.columns(3)
        col1.metric("Optimized Apply Cost", f"{opt_costs['total_apply_cost']:,} $")
        col2.metric("Optimized Retract Cost", f"{opt_costs['total_retract_cost']:,} $")
        col3.metric("Optimized Combined Cost", f"{opt_costs['total_combined_cost']:,} $")   
    
    st.markdown("##### Cost Distribution")
    cols = st.columns(3)
    cost_type = cols[0].radio(label="Cost Calculation: ", options=["absolute", "relative"], horizontal=True,
                             format_func=lambda x: {"relative": "Calculate cost for test **in execution order**", "absolute": "Calculate cost for **each test isotedly**"}[x])
    show_cumsum = cols[1].checkbox("Show Cumilative Cost Line", value=True)
    display_in_execorder = cols[1].checkbox("Show Graph in order or the Execution", value=True)
    show_optimized = cols[2].checkbox("Show Optimized Test Configuration **Plot**", value=show_optimized, key="cost_opt_plot2")
    with st.expander("Show plot settings", expanded=False):
            cols = st.columns(2)
            barcolor = cols[0].color_picker(label="Adjust the color of the bars of the bar-plot", value="#87ceeb")
            linecolor = cols[1].color_picker(label="Adjust the color of the line of the line-plot", value="#ff0000")
            fig_height = st.slider(
                "Set plot height",
                min_value=400, max_value=1200, value=650, step=50, 
            )
    fig1 = make_cost_plots(
        unopt_tests["tests"], 
        title="Unoptimized Tests", 
        type=cost_type,
        show_cumsum=show_cumsum,
        display_in_execorder=display_in_execorder,
        fig_height=fig_height, barcolor=barcolor, linecolor=linecolor
    )
    st.plotly_chart(fig1, use_container_width=True)
    if show_optimized:
        fig2 = make_cost_plots(
            opt_tests["tests"], 
            title="Optimized Tests", 
            type=cost_type,
            show_cumsum=show_cumsum,
            display_in_execorder=display_in_execorder,
            fig_height=fig_height, barcolor=barcolor, linecolor=linecolor
        )
        st.plotly_chart(fig2, use_container_width=True)



@st.cache_data
def load_csv(name: str) -> pd.DataFrame:
    """Load a CSV once and cache the result."""
    return pd.read_csv(name)

@st.cache_data
def load_tests(path: str = "reports/tests_optimized_def.json") -> list[dict]:
    """Return the list of tests from the JSON definition."""
    

