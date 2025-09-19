import streamlit as st
import pandas as pd
import os
import shutil
from jsontocsv import json_to_csv

import io
import xml.etree.ElementTree as ET
# from generate_error import parse_failure_block, failure_to_dataframe, natural_language_message

VIEW_OPTIONS = [
    "Architecture",
    "Requirements",
    "Test Strategy",
    "Test Results",
    "Test Facilities",
    "Warnings/Issues",
    "Scenarios",
]
REPORTS_ROOT = "reports"                           #  ./reports/…
DATA_TIES = {
    "Home Page": ["TripleCount"],
    "Test Facilities": ["TestFacilities", "TestEquipment", "TestPersonnel"],
    "Requirements": ["Requirements"],
    "Architecture": ["SystemArchitecture", "MissionArchitecture"],
    "Test Strategy": ["TestStrategy", "TestEquipment", "TestFacilities"],
    "Test Results": ["TestResults"],
    "Test Configuration": ["reqs", "costs"],
    # (Warnings/Issues pulls from these same files, so no separate entry needed)
}

@st.dialog("Project Details")
def project_form(mode=1):
    if mode == 1:
        st.write("Fill in the new dashboard details. **'Home Page' view is always included.**")
        st.caption("*Fields marked **(:red[*])** are required*")
        with st.form("new_proj_form"):
            name = st.text_input("Project (Dashboard) Name **:red[*]**", key="project_name")
            description = st.text_area("Project Description", key="project_description")
            views = st.multiselect(
                "Select additional views to include",
                VIEW_OPTIONS,
                key="project_views",
            )

            submitted = st.form_submit_button("Create Project")
            if submitted:
                if name.strip() == "":
                    st.write("❗ :red[Name cannot be empty]")
                    st.stop()
                
                # Persist project details in session_state
                projectlist = st.session_state['projectlist']

                # 🚫 Duplicate‑name guard  (case‑insensitive)
                if any(p["name"].lower() == name.lower() for p in projectlist):
                    st.error(f"A project called **{name}** already exists. Pick another name.")
                    st.stop()

                project_folder = os.path.join(REPORTS_ROOT, name.lower().replace(" ", "_"))
                os.makedirs(project_folder, exist_ok=True)

                projectlist.append({
                    'id': len(projectlist)+1, 
                    'name': name, 
                    'description': description, 
                    'views': ["Home Page"] + views, 
                    'folder': project_folder
                })
                st.session_state['projectlist'] = projectlist
                st.session_state["currproject"] = name          # immediately select it

                # Rerun to display the new dashboard immediately
                st.rerun()
    
    if mode == 2:
        currproject = st.session_state['currproject']
        projectlist = st.session_state['projectlist']
        details = [p for p in projectlist if p['name'] == currproject][0]
        index = projectlist.index(details)
        
        # if "Home Page" in details['views']:
        #     details['views'].remove("Home Page")
        # ⚠️  **No in‑place mutation** – copy views first
        current_views = [v for v in details["views"] if v != "Home Page"]

        st.write("Edit project details")

        with st.form("edit_proj_form"):
            name = st.text_input("Project Name", value=details['name'], key="edit_project_name")
            description = st.text_area("Description", value=details['description'], key="edit_project_description")
            views = st.multiselect(
                "Select Views", 
                options=VIEW_OPTIONS,
                default=current_views,
                key="edit_project_views")

            submitted = st.form_submit_button("Save Project")
            if submitted:
                if name == "":
                    st.write("❗ :red[Name cannot be empty]")
                    st.stop()
                
                # 🚫 Duplicate‑name guard (exclude the record being edited)
                if any(
                    (i != index) and (p["name"].lower() == name.lower())
                    for i, p in enumerate(projectlist)
                ):
                    st.error(f"Another project is already named **{name}**.")
                    st.stop()
                
                old_folder = details["folder"]
                new_folder = os.path.join(REPORTS_ROOT, name.lower().replace(" ", "_"))

                if old_folder != new_folder:
                    shutil.move(old_folder, new_folder)            # rename directory


                projectlist[index] = {
                    'id': details['id'], 
                    'name': name, 
                    'description': description, 
                    'views': ["Home Page"] + views, 
                    'folder': new_folder,
                }
                st.session_state['projectlist'] = projectlist
                st.session_state["currproject"] = name

                # Rerun to display the new dashboard immediately
                st.rerun()

@st.dialog("Select a tab below and replace its data")
def replace_data(project):
    """
    • Upload required JSON for selected tabs – auto‑converted to CSV
    • De‑select existing files to delete them
    """
    folder = project["folder"]
    tabs = project["views"]

    st.markdown("### Select tab(s) you want to modify")
    sel_tabs = st.multiselect("Tabs", options=tabs)

    # --------------------------------------- current & required filenames
    req_json = {f"{tie}.json" for tab in sel_tabs for tie in DATA_TIES[tab]}
    existing_json = {f for f in os.listdir(folder) if f.endswith(".json")}
    existing_csv  = {f for f in os.listdir(folder) if f.endswith(".csv")}

    # --------------------------------------- DELETE (un‑tick to remove)
    to_keep = st.multiselect(
        "Files already present (de-select a file to delete it from tab's storage)",
        options=sorted(existing_json & req_json),
        default=sorted(existing_json & req_json),
    )
    st.caption(":red[Do not use the deselect option, if you just want to replace a file.]")
    st.caption(":orange[To update an existing file, just upload a new version below]")
    to_delete = (existing_json & req_json) - set(to_keep)
    if to_delete:
        st.warning(f"These files will be **deleted** on save: {', '.join(to_delete)}")

    # --------------------------------------- UPLOAD
    new_files = st.file_uploader(
        "Upload the JSON files listed below",
        type="json", accept_multiple_files=True,
        key=f"uploader_{project['id']}" 
    )

    # ------------- save uploads (JSON + converted CSV)
    uploaded_names = set()                       # keep track of just‑uploaded names
    for f in new_files:
        json_out = f.name.split(".json")[0].strip().translate({ord(ch): None for ch in '0123456789'}).strip() + ".json"
        path_json = os.path.join(folder, json_out)
        with open(path_json, "wb") as out:
            out.write(f.getbuffer())
        csv_out = f.name.split(".json")[0].strip().translate({ord(ch): None for ch in '0123456789'}).strip() + ".csv"
        json_to_csv(json_file_object=f.getvalue(),
                    csv_output_path=os.path.join(folder, csv_out))
        st.success(f"Saved {json_out} converted and saved")
        uploaded_names.add(json_out)
    
    # ------------------- MISSING / COMPLETE STATUS ---------------------------
    # What will remain after this dialog *if* the user clicks "Save Changes"
    future_present = (existing_json - to_delete) | uploaded_names
    missing_files  = sorted(req_json - future_present)

    if sel_tabs:                                 # only show feedback if a tab was chosen
        if missing_files:
            st.warning(f"Missing required files: {', '.join(missing_files)}")
        else:
            st.success("🎉 All required files are present!")

    # ------------- commit deletes
    if st.button("Save Changes"):
        for filename in to_delete:
            for ext in (".json", ".csv"):
                p = os.path.join(folder, filename.replace(".json", ext))
                if os.path.exists(p):
                    os.remove(p)
        st.rerun()

# @st.dialog("🔍 OML Reasoning‑Error Inspector")
# def error_inspector_form():

#     uploaded = st.file_uploader("Upload a *reasoning.xml* file", type=["xml"])
#     if uploaded:
#         xml_bytes = uploaded.getvalue()
#         try:
#             tree = ET.parse(io.BytesIO(xml_bytes))
#         except ET.ParseError as e:
#             st.error(f"XML parsing error: {e}")
#             st.stop()

#         failures = tree.findall(".//failure")
#         if not failures:
#             st.success("No <failure> elements found – the file appears clean 🎉")
#             st.stop()

#         for idx, fail_elem in enumerate(failures, start=1):
#             data = parse_failure_block(fail_elem.text or "")
#             if not data:
#                 st.warning(f"Couldn’t interpret failure block #{idx}.")
#                 continue
#             st.subheader(f"Violation")
#             st.write(natural_language_message(data), unsafe_allow_html=True)
#             st.dataframe(failure_to_dataframe(data), use_container_width=True, hide_index=True)
