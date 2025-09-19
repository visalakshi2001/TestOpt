import streamlit as st
import os
import json
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from makeplots import build_sankey, make_presence_df, style_presence, make_cost_plots, make_cost_histogram


from streamlit_echarts import st_echarts

def render(project: dict) -> None:
    folder   = project["folder"]
    csv_path = os.path.join(folder, "reqs.csv")
    json_path = os.path.join(folder, "reqs.json")

    if not os.path.exists(json_path):
        st.info("reqs.json data is not available – upload it via **🪄 Edit Data**")
        return
    
    # # ──────────────────────────── 2.  Load data once ────────────────────────────
    opt_tests = json.load(open(os.path.join("reports/test-plan-py2/test_order_optimized.json")))
    pruned_tests = json.load(open(os.path.join("reports/test-plan-py2/pruned_tests.json")))
    unopt_tests = {"tests": pruned_tests}
    ct = []
    for i, tt in enumerate(unopt_tests["tests"]):
        tt["id"] = i+1 
        # add apply and retract to each test, apply the tests that were not in previous test and retract the tests that are not in the current test
        apply = list(set(tt["scenarios"]) - set(ct))
        retract = list(set(ct) - set(tt["scenarios"]))
        tt["apply"] = apply
        tt["retract"] = retract
        ct = tt["scenarios"]
    
    for ss in opt_tests["tests"]:
        target = [test for test in unopt_tests["tests"] if test["uuid"] == ss["uuid"]][0]
        ss["id"] = target["id"]

    reqproxy = json.load(open("reports/test-plan-py2/requirements-proxied.json", "rb+"))
    reqproxy2 = {}
    for ss in reqproxy["requirements"]:
        # merge all the situations list into one list if there are more than one lists
        reqproxy2[ss["id"]] = ss
        reqproxy2[ss["id"]]["situations"] = ",".join([scenario for situation in ss["situations"] for scenario in situation["scenarios"]])
        reqproxy2[ss["id"]].pop("configs", None)  

    reqproxy2_df = pd.DataFrame.from_dict(reqproxy2, orient="index")
    reqproxy2_df = reqproxy2_df.reset_index(drop=True).rename(columns={"situations": "scenarios"})

    # make a scenarios dataframe from reqproxy2 with the structure:
    # scenarioID, requirementIDs
    # by iterating through each requirement and its situations and adding it to the scenario id with comma separated requirement ids
    scenario_dict = {}
    for req_id, req in reqproxy2.items():
        for situation in req["situations"].split(","):
            if situation not in scenario_dict:
                scenario_dict[situation] = set()
            scenario_dict[situation].add(req_id)
    scenario_df = pd.DataFrame(list(scenario_dict.items()), columns=["scenarioID", "requirementIDs"])
    scenario_df["requirementIDs"] = scenario_df["requirementIDs"].apply(lambda x: ",".join(x))

    # # ──────────────────────────── 3.   Sankey  ────────────────────────────
    st.subheader("Select scenario(s) to inspect")
    cho_scenarios = st.multiselect(
        "Scenario ID", sorted(scenario_df["scenarioID"].unique()), max_selections=10
    )
    if cho_scenarios:
        with st.expander("Show plot settings", expanded=False):
            plot_height = st.slider(
                "Set plot size",
                min_value=450, max_value=900, value=600, step=30,)
        fig = build_sankey(scenario_df, reqproxy2_df, cho_scenarios, plot_height=plot_height)
        st.plotly_chart(fig)
    else:
        st.info("⬆️ Pick one or more scenario IDs to show the Sankey.")
    


    # # ──────────────────────────── 3.  Requirement table ────────────────────────────
    st.subheader("Which quantities satisfy a requirement?")
    req_id = st.multiselect(
        "Requirement ID", sorted(reqproxy2_df["id"].unique())
    )
    if req_id != []:
        st.write(reqproxy2_df.query("id in @req_id")[["id", "quantity"]])
    else:
        st.info("⬆️ Pick one or more requirement IDs to show the quantities that satisfy them.")


    # # ──────────────────────────── 4.  Cost charts ────────────────────────────
    st.subheader("Cost Calculation")
    
    st.markdown("##### Cost Distribution")
    cols = st.columns(3)
    cost_type = cols[0].radio(label="Cost Calculation: ", options=["absolute", "relative"], horizontal=True,
                             format_func=lambda x: {"relative": "Calculate cost for test **in execution order**", "absolute": "Calculate cost for **each test in isolation**"}[x])
    show_cumsum = cols[1].checkbox("Show Cumulative Cost Line", value=True)
    display_in_execorder = cols[1].checkbox("Show Graph in order of the Execution", value=True)
    show_optimized = cols[2].checkbox("Show Optimized Test Configuration **Plot**", key="cost_opt_plot2") #value=show_optimized,
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


    # # ──────────────────────────── 5.  Cost Distribution ────────────────────────────
    
    st.subheader("Cost Distribution Histogram")
    with st.expander("Show plot settings", expanded=False):
            nbins = st.slider(
                "Set number of bins",
                min_value=50, max_value=200, value=150, step=10,)
            bargap = st.slider(
                "Set gap between bars",
                min_value=0.0, max_value=1.0, value=0.1, step=0.05,)
            fig_height = st.slider(
                "Set plot height",
                min_value=400, max_value=1200, value=650, step=50,
                key="cost_hist_height"
            )
    fig = make_cost_histogram(
        unopt_tests["tests"], opt_tests["tests"],
        title="Cost Distribution Histogram",
        fig_height=fig_height, nbins=nbins, bargap=bargap
    )
    st.plotly_chart(fig, use_container_width=True)

@st.cache_data
def load_csv(name: str) -> pd.DataFrame:
    """Load a CSV once and cache the result."""
    return pd.read_csv(name)



# tabs
# SCENARIOS
# REQUIREMENTS
# TEST STRATEGY

# remove cumulative line in ascending bar chart
# remove option to show optimized in the metrics section
# add the absolute cost to the cumulative sum
# remove isotedly from plot title and subtitle