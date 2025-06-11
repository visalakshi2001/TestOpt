import os
import pandas as pd
import streamlit as st
from projectdetail import DATA_TIES      # reuse the same mapping
import json

from makeplots import plot_scenario_heatmaps, plot_sequence_dots, build_scenario_timeline, make_presence_df, style_presence

from jsontocsv import json_to_csv
from costcalc import calculate_costs

def render(project: dict) -> None:
    folder   = project["folder"]
    csv_path = os.path.join(folder, "reqs.csv")
    json_path = os.path.join(folder, "reqs.json")

    if not os.path.exists(json_path):
        st.info("reqs.json data is not available – upload it via **🪄 Edit Data**")
        return
    json_to_csv(json_input_path=json_path, csv_output_path=csv_path)

    # reqs_df = pd.read_csv(csv_path)
    # with st.expander("Requirements Data", expanded=True):
    #     st.write(reqs_df)


    # st.write(pd.read_json(os.path.join("reports/tests_raw_def.json")))
    unopt_tests = json.load(open(os.path.join("reports/tests_unoptimized_def.json")))
    # st.write(pd.DataFrame(unopt_tests["tests"]))
    opt_tests = json.load(open(os.path.join("reports/tests_optimized_def.json")))
    # st.write(pd.DataFrame(opt_tests["tests"]))
    
    show_optimized = st.checkbox("Show Optimized Tests", value=True)
    
    # Display a grid of metrics with total costs
    costs = calculate_costs(unopt_tests["tests"])
    st.markdown("### Total Costs")
    col1, col2, col3 = st.columns(3)
    col1.metric("Unoptimized Apply Cost", f"{costs['total_apply_cost']:,} €")
    col2.metric("Unoptimized Retract Cost", f"{costs['total_retract_cost']:,} €")
    col3.metric("Unoptimized Combined Cost", f"{costs['total_combined_cost']:,} €")
    st.markdown("---")
    
    if show_optimized:
        # show optimized costs
        opt_costs = calculate_costs(opt_tests["tests"])
        col1, col2, col3 = st.columns(3)
        col1.metric("Optimized Apply Cost", f"{opt_costs['total_apply_cost']:,} €")
        col2.metric("Optimized Retract Cost", f"{opt_costs['total_retract_cost']:,} €")
        col3.metric("Optimized Combined Cost", f"{opt_costs['total_combined_cost']:,} €")   
    
    plot_option = st.selectbox(
        "Select Plot Type",
        options=["Scenario Heatmaps", "Test Sequence Dots", "Scenario Timeline", "Presence Matrix"],
        index=0
    )
    
    if plot_option == "Scenario Heatmaps":
        fig1, fig2= plot_scenario_heatmaps()
        st.plotly_chart(fig1, use_container_width=True)
        if show_optimized:
             st.plotly_chart(fig2, use_container_width=True)
    elif plot_option == "Test Sequence Dots":
        fig1 = plot_sequence_dots(opt_tests["tests"], "Optimized Test Sequence")
        fig2 = plot_sequence_dots(unopt_tests["tests"], "Unoptimized Test Sequence")
        st.plotly_chart(fig2, use_container_width=True)
        if show_optimized:
             st.plotly_chart(fig1, use_container_width=True)
    elif plot_option == "Scenario Timeline":
        if show_optimized:
            st.markdown("### Optimized Scenario Timeline")
            fig = build_scenario_timeline(opt_tests["tests"], "Optimized Scenario Timeline")
            st.plotly_chart(fig, use_container_width=True)
        fig = build_scenario_timeline(unopt_tests["tests"], "Unoptimized Scenario Timeline")
        st.plotly_chart(fig, use_container_width=True)
    elif plot_option == "Presence Matrix":
        cols = st.columns(2)
        show_additional = cols[0].checkbox("Show Additional Scenarios", value=False)
        flipped = cols[1].checkbox("Flip Grid Order", value=False)
        df1, _ = make_presence_df(opt_tests["tests"], flipped=flipped)
        df2, __ = make_presence_df(unopt_tests["tests"], flipped=flipped)
        df1 = style_presence(df1, show_additional=show_additional)
        df2 = style_presence(df2, show_additional=show_additional)
        st.dataframe(df1, use_container_width=True, row_height=30, height=500)

        if show_optimized:
            st.dataframe(df2,  use_container_width=True, row_height=30, height=500)
        
        # st.dataframe(_)


    