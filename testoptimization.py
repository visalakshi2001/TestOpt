import os
import pandas as pd
import streamlit as st
from projectdetail import DATA_TIES      # reuse the same mapping
import json

from makeplots import plot_scenario_heatmaps, plot_sequence_dots, build_scenario_timeline, make_presence_df, style_presence

from jsontocsv import json_to_csv

def render(project: dict) -> None:
    folder   = project["folder"]
    csv_path = os.path.join(folder, "reqs.csv")
    json_path = os.path.join(folder, "reqs.json")

    if not os.path.exists(json_path):
        st.info("reqs.json data is not available – upload it via **🪄 Edit Data**")
        return
    json_to_csv(json_input_path=json_path, csv_output_path=csv_path)

    unopt_tests = json.load(open(os.path.join("reports/tests_unoptimized_def.json")))
    opt_tests = json.load(open(os.path.join("reports/tests_optimized_def.json")))
    reqs = pd.read_csv(os.path.join(folder, "reqs.csv"))
    scenarios = pd.read_csv(os.path.join("reports/", "scenarios.csv"))
    tests_raw_def = pd.read_json("reports/tests_raw_def.json")
    show_optimized = st.checkbox("Show Optimized Test Configurations", value=True)
    
    st.markdown("### Test Configuration Metrics")   
    cols = st.columns(4)
    cols[0].metric("Total Requirements:", f"{len(reqs)}")
    cols[1].metric("Total Scenarios:", f"{len(scenarios)}")
    cols[2].metric("Total Quantities:", f"{reqs['quantity'].nunique()}")
    cols[3].metric("Total Test Configurations:", f"{len(tests_raw_def)}")

    plot_option = st.selectbox(
        "Select Plot Type",
        options=["Scenario Heatmaps", "Test Sequence Dots", "Scenario Timeline", "Presence Matrix"],
        index=0
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
        


    