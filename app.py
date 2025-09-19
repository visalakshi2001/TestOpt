import os
import pandas as pd
import streamlit as st
from projectdetail import project_form, VIEW_OPTIONS, DATA_TIES, replace_data, REPORTS_ROOT

import homepage
import scenarios
import teststrategy
import requirements

st.set_page_config("Test Optimization Dashboard", page_icon="🤖", layout="wide")


def init_session():
    """Ensure all required session_state keys exist."""

    if 'projectlist' not in st.session_state:
        st.session_state['projectlist'] = [
            {
                'id': 1, 
                'name': "Test Optimization Dashboard", 
                'description': "", 
                'views': ["Home Page"] + ["Test Strategy", "Requirements", "Scenarios"], 
                'folder': os.path.join(REPORTS_ROOT, "Test Optimization Dashboard".lower().replace(" ", "_"))
            }
        ]
        os.makedirs(os.path.join(REPORTS_ROOT, "Test Optimization Dashboard".lower().replace(" ", "_")), exist_ok=True)
    if 'currproject' not in st.session_state:
        st.session_state['currproject'] = None


def show_tab(tab_name, project):
    """
    Dispatch each tab to its own view module.
    Tabs not yet modularised fall back to a simple CSV preview + missing‑file message.
    """
    # ---- 1.  delegated views  ------------------------------------------------
    if tab_name == "Home Page":
        homepage.render(project)          # ./homepage.py
        return
    
    if tab_name == "Test Strategy":
        teststrategy.render(project)
        return
    
    if tab_name == "Scenarios":
        scenarios.render(project)
        return
    
    if tab_name == "Requirements":
        requirements.render(project)
        return


    # ---- 2.  generic fallback for other tabs  -------------------------------
    folder = project["folder"]
    for base in DATA_TIES[tab_name]:
        csv_path = os.path.join(folder, f"{base}.csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            st.dataframe(df, use_container_width=True)
        else:
            st.info(f"{base}.json data is not available - upload it via **🪄 Edit Data** button")     

def panel():
    with st.sidebar:
        st.subheader("Select Project")
        projectlist = st.session_state['projectlist']
        currproject = st.session_state['currproject']

        if projectlist != []:
            projectnames = [p['name'] for p in projectlist]
            currproject = st.radio("Select Current Project", options=projectnames)
            st.session_state['currproject'] = currproject
        else:
            st.write("Create new dashboard using 'New Project'")


        st.subheader("Preferences")
        newproject = st.button("New Project", )
        changeproject = st.button("Edit Project")

        if newproject:
            project_form(mode=1)
        if changeproject:
            project_form(mode=2)
        
        # --------------- create a gap using container ------------
        st.container(height=100, border=False)
        st.subheader("Having problems with OML description?")
        st.caption("Upload your *reasoning.xml* file to easily breakdown your error")
        inspect = st.button("Inspect Error", icon="🔍")

def main():

    projectlist = st.session_state['projectlist']
    currproject = st.session_state['currproject']

    if projectlist != []:
        project = [p for p in projectlist if p['name'] == currproject][0]
    
    if currproject == None:
        st.title("Welcome!")
        st.write("Create your first project to get started.")
    else:
        with st.container():
            col1, col2 = st.columns([0.9, 0.15])
            with col1:
                st.header(project["name"], divider='violet')
            with col2:
                if st.button("🪄 Edit Data", type='primary'):
                    replace_data(project) 
        
        if project['views'] != []:
            VIEWTABS = st.tabs(project['views'])
            for i, tab in enumerate(VIEWTABS):
                with tab:
                    show_tab(project["views"][i], project)
    return


if __name__ == "__main__":
    init_session()
    panel()
    main()