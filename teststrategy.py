import streamlit as st
import os
import json
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from src.costcalc2 import calculate_costs
from makeplots import build_scenario_timeline, plot_sequence_dots, plot_scenario_heatmaps, make_presence_df, style_presence, make_cost_plots, make_cost_histogram


from streamlit_echarts import st_echarts

def render(project: dict) -> None:
    folder   = project["folder"]
    
    # ──────────────────────────── 1.  Load data once ────────────────────────────
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
    costs = json.load(open("reports/test-plan-py2/costs.json", "rb+"))

    reqproxy2 = {}
    for ss in reqproxy["requirements"]:
        # merge all the situations list into one list if there are more than one lists
        reqproxy2[ss["id"]] = ss
        reqproxy2[ss["id"]]["situations"] = [scenario for situation in ss["situations"] for scenario in situation["scenarios"]]
        reqproxy2[ss["id"]].pop("configs", None)  

    scenario_cost_df = pd.DataFrame(list(costs["scenarios"].items()), columns=["Scenario", "Cost"])
    quantity_cost_df = pd.DataFrame(list(costs["observations"].items()), columns=["Quantity", "Cost"])

    # # ──────────────────────────── 2.  Test Configuration Metrics ────────────────────────────
    
    st.markdown("### Test Configuration Metrics")   
    cols = st.columns(4)
    cols[0].metric("Total Requirements:", f"{len(reqproxy2)}")
    cols[1].metric("Total Scenarios:", f"{len(scenario_cost_df)}")
    cols[2].metric("Total Quantities:", f"{len(quantity_cost_df)}")
    cols[3].metric("Total Test Configurations:", f"{len(unopt_tests['tests'])}")

    # Display a grid of metrics with total costs
    st.markdown("##### Test Configuration Metrics")
    costs = calculate_costs(unopt_tests["tests"])
    # show_optimized_numbers = st.checkbox("Show Optimized Values", value=True, key="cost_opt_plot")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Unoptimized Apply Cost", f"{costs['total_apply_cost']:,} $")
    col2.metric("Unoptimized Retract Cost", f"{costs['total_retract_cost']:,} $")
    col3.metric("Unoptimized Combined Cost", f"{costs['total_combined_cost']:,} $")
    # st.markdown("---")
    # if show_optimized_numbers:
        # show optimized costs
    opt_costs = calculate_costs(opt_tests["tests"])
    col1, col2, col3 = st.columns(3)
    col1.metric("Optimized Apply Cost", f"{opt_costs['total_apply_cost']:,} $")
    col2.metric("Optimized Retract Cost", f"{opt_costs['total_retract_cost']:,} $")
    col3.metric("Optimized Combined Cost", f"{opt_costs['total_combined_cost']:,} $")

    # # ──────────────────────────── 3.  Test Configuration Chart ────────────────────────────
    
    st.markdown("##### Test Configuration Chart")
    show_optimized = st.checkbox("Show Optimized Test Configurations", key="opt_plot2")
    plot_option = st.selectbox(
        "Select Plot Type",
        options=["Scenario Heatmaps", "Test Sequence Dots", "Scenario Timeline", "Presence Matrix"],
        index=1
    )
    
    if plot_option == "Scenario Heatmaps":
        with st.expander("Show plot settings", expanded=False):
            cell_size = st.slider(
                "Set cell size",
                min_value=5, max_value=50, value=20, step=1,
                key="cell_size_slider"
            )
            fig_height = st.slider(
                "Set plot height",
                min_value=400, max_value=1200, value=650, step=50,
                key="fig_height_slider" 
            )
        fig1 = plot_scenario_heatmaps(unopt_tests["tests"], "Unoptimized Scenario Heatmaps", 
                                      cell_size=cell_size, fig_height=fig_height)
        st.plotly_chart(fig1, use_container_width=True)
        if show_optimized:
            fig2 = plot_scenario_heatmaps(opt_tests["tests"], "Optimized Scenario Heatmaps", 
                                          cell_size=cell_size, fig_height=fig_height)
            st.plotly_chart(fig2, use_container_width=True)
    elif plot_option == "Test Sequence Dots":
        with st.expander("Show plot settings", expanded=False):
            cell_size = st.slider(
                "Set cell size",
                min_value=5, max_value=10, value=9, step=1,
                key="cell_size_slider"
            )
            fig_height = st.slider(
                "Set plot height",
                min_value=400, max_value=1200, value=500, step=50,
                key="fig_height_slider"
            )
        fig1 = plot_sequence_dots(unopt_tests["tests"], "Unoptimized Test Sequence", 
                                  cell_size=cell_size, fig_height=fig_height)
        st.plotly_chart(fig1, use_container_width=True)
        if show_optimized:
            fig2 = plot_sequence_dots(opt_tests["tests"], "Optimized Test Sequence", 
                                      cell_size=cell_size, fig_height=fig_height)
            st.plotly_chart(fig2, use_container_width=True)
    elif plot_option == "Scenario Timeline":
        with st.expander("Show plot settings", expanded=False):
            cell_size = st.slider(
                "Set cell size",
                min_value=5, max_value=14, value=10, step=1,
                key="cell_size_slider"
            )
            fig_height = st.slider(
                "Set plot height",
                min_value=400, max_value=1200, value=500, step=50,
                key="fig_height_slider"
            )
        fig1 = build_scenario_timeline(unopt_tests["tests"], "Unoptimized Scenario Timeline", 
                                       cell_size=cell_size, fig_height=fig_height)
        st.plotly_chart(fig1, use_container_width=True)
        if show_optimized:
            fig2 = build_scenario_timeline(opt_tests["tests"], "Optimized Scenario Timeline", 
                                           cell_size=cell_size, fig_height=fig_height)
            st.plotly_chart(fig2, use_container_width=True)
    elif plot_option == "Presence Matrix":
        cols = st.columns(2)
        show_additional = cols[0].checkbox("Show Additional Scenarios", value=False)
        flipped = cols[1].checkbox("Flip Grid Order", value=False)
        df1, __ = make_presence_df(unopt_tests["tests"], flipped=flipped)
        df1 = style_presence(df1, show_additional=show_additional)
        st.markdown("### Unoptimized Presence Matrix")
        st.dataframe(df1,  use_container_width=True, row_height=30, height=500)
        if show_optimized:
            df2, _ = make_presence_df(opt_tests["tests"], flipped=flipped)
            df2 = style_presence(df2, show_additional=show_additional)
            st.markdown("### Optimized Presence Matrix")
            st.dataframe(df2, use_container_width=True, row_height=30, height=500)
    
    # # ──────────────────────────── 4.  Cost charts ────────────────────────────
    st.subheader("Cost Calculation")
    
    st.markdown("##### Cost Distribution")
    cols = st.columns([3, 2, 2])
    cost_type = cols[0].radio(label="Choose how the cost should be calculated: ", options=["absolute", "relative"], horizontal=True,
                             format_func=lambda x: {"relative": "Calculate cost **with apply and retract cost of each test**", "absolute": "Calculate cost for **each test in isolation** (absolute cost)"}[x])
    display_in_execorder = cols[1].radio(label="Choose the order of viewing the configuration data: ", options=[True, False], horizontal=True,
                             format_func=lambda x: {True: "Arrange Test IDs in order of execution", False: "Arrange Test IDs in ascending order of cost"}[x])
    if display_in_execorder:
        show_cumsum = cols[2].checkbox("Show Cumulative Cost Line", value=True)
    else:
        show_cumsum = False
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
    # if show_optimized:
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
