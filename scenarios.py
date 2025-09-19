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
    
    # # ──────────────────────────── 2.  Load data once ────────────────────────────

    reqproxy = json.load(open("reports/test-plan-py2/requirements-proxied.json", "rb+"))
    reqproxy2 = {}
    for ss in reqproxy["requirements"]:
        # merge all the situations list into one list if there are more than one lists
        reqproxy2[ss["id"]] = ss
        reqproxy2[ss["id"]]["situations"] = ",".join([scenario for situation in ss["situations"] for scenario in situation["scenarios"]])
        reqproxy2[ss["id"]].pop("configs", None)  

    reqproxy2_df = pd.DataFrame.from_dict(reqproxy2, orient="index")
    reqproxy2_df = reqproxy2_df.reset_index(drop=True).rename(columns={"situations": "scenarios"})

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
    