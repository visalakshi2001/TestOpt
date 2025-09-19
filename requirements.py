
import streamlit as st
import os
import json
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# from makeplots import build_sankey, make_presence_df, style_presence, make_cost_plots, make_cost_histogram


from streamlit_echarts import st_echarts

def render(project: dict) -> None:
    folder   = project["folder"]
    # csv_path = os.path.join(folder, "reqs.csv")
    # json_path = os.path.join(folder, "reqs.json")

    # if not os.path.exists(json_path):
    #     st.info("reqs.json data is not available – upload it via **🪄 Edit Data**")
    #     return

    reqproxy = json.load(open("reports/test-plan-py2/requirements-proxied.json", "rb+"))
    reqproxy2 = {}
    for ss in reqproxy["requirements"]:
        # merge all the situations list into one list if there are more than one lists
        reqproxy2[ss["id"]] = ss
        reqproxy2[ss["id"]]["situations"] = ",".join([scenario for situation in ss["situations"] for scenario in situation["scenarios"]])
        reqproxy2[ss["id"]].pop("configs", None)  

    reqproxy2_df = pd.DataFrame.from_dict(reqproxy2, orient="index")
    reqproxy2_df = reqproxy2_df.reset_index(drop=True).rename(columns={"situations": "scenarios"})

    
    st.subheader("Which quantities satisfy a requirement?")
    req_id = st.multiselect(
        "Requirement ID", sorted(reqproxy2_df["id"].unique()), key="req_quant_select"
    )
    if req_id != []:
        st.write(reqproxy2_df.query("id in @req_id")[["id", "quantity"]])
    else:
        st.info("⬆️ Pick one or more requirement IDs to show the quantities that satisfy them.")

    with st.expander("Show all requirements and their quantities", icon="📜"):
        st.dataframe(reqproxy2_df[["id", "quantity"]], use_container_width=True)
